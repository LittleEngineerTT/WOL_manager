import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from wol_bot import bot
from wol_bot.config import Settings
from wol_bot.storage import Device, DeviceStore

ALLOWED = 42
DESKTOP = Device("desktop", "aa:bb:cc:dd:ee:ff", "192.168.1.20")
NAS = Device("nas", "aa:bb:cc:dd:ee:01", "192.168.1.2")


@pytest.fixture
def store(tmp_path):
    return DeviceStore(tmp_path / "devices.db")


@pytest.fixture
def context(store):
    settings = Settings(bot_token="t", allowed_user_ids=frozenset({ALLOWED}), broadcast_address="192.168.1.255")
    return SimpleNamespace(bot_data={"settings": settings, "store": store}, args=[])


@pytest.fixture
def woken(monkeypatch):
    calls = []
    monkeypatch.setattr(bot.network, "wake", lambda mac, address, port: calls.append((mac, address, port)))
    return calls


def message_update(user_id=ALLOWED):
    message = SimpleNamespace(reply_text=AsyncMock())
    return SimpleNamespace(effective_user=SimpleNamespace(id=user_id), effective_message=message, callback_query=None)


def button_update(data, user_id=ALLOWED):
    query = SimpleNamespace(data=data, answer=AsyncMock(), edit_message_text=AsyncMock())
    return SimpleNamespace(effective_user=SimpleNamespace(id=user_id), effective_message=None, callback_query=query)


def run(handler, update, context, *args):
    context.args = list(args)
    asyncio.run(handler(update, context))


def replies(update):
    if update.callback_query:
        return [call.args[0] for call in update.callback_query.edit_message_text.call_args_list]
    return [call.args[0] for call in update.effective_message.reply_text.call_args_list]


def keyboard(update):
    return update.effective_message.reply_text.call_args.kwargs["reply_markup"]


def test_unauthorized_user_is_rejected(context, store, woken):
    store.add(DESKTOP)
    update = message_update(user_id=7)
    run(bot.wake_command, update, context, "desktop")
    assert woken == []
    assert "Your Telegram user ID is 7" in replies(update)[0]


def test_unauthorized_button_is_rejected(context, store):
    store.add(DESKTOP)
    update = button_update("confirm-delete:desktop", user_id=7)
    run(bot.button, update, context)
    assert store.get("desktop") == DESKTOP
    update.callback_query.answer.assert_awaited_once_with("Not authorized", show_alert=True)


def test_add_normalizes_and_stores(context, store):
    update = message_update()
    run(bot.add_command, update, context, "desktop", "AA-BB-CC-DD-EE-FF", "192.168.1.20")
    assert store.list() == [DESKTOP]
    assert "added" in replies(update)[0]


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        (["desktop"], "Usage"),
        (["desktop", "aa:bb:cc:dd:ee:ff;x", "192.168.1.20"], "Invalid MAC address"),
        (["desktop", "aa:bb:cc:dd:ee:ff", "nope"], "Invalid IP address"),
        (["all", "aa:bb:cc:dd:ee:ff", "192.168.1.20"], "reserved"),
        (["<b>", "aa:bb:cc:dd:ee:ff", "192.168.1.20"], "Invalid name: &lt;b&gt;"),
    ],
)
def test_add_rejects_invalid_input(context, store, args, expected):
    update = message_update()
    run(bot.add_command, update, context, *args)
    assert store.list() == []
    assert expected in replies(update)[0]


def test_add_rejects_duplicates(context, store):
    store.add(DESKTOP)
    update = message_update()
    run(bot.add_command, update, context, "laptop", "aa:bb:cc:dd:ee:ff", "192.168.1.30")
    assert "desktop already uses this MAC address" in replies(update)[0]


def test_wake_one_device_uses_configured_broadcast(context, store, woken):
    store.add(DESKTOP)
    update = message_update()
    run(bot.wake_command, update, context, "Desktop")
    assert woken == [("aa:bb:cc:dd:ee:ff", "192.168.1.255", 9)]
    assert "Magic packet sent to <b>desktop</b>" in replies(update)[0]


def test_start_with_argument_is_an_alias_of_wake(context, store, woken):
    store.add(DESKTOP)
    run(bot.start_command, message_update(), context, "desktop")
    assert [mac for mac, _, _ in woken] == [DESKTOP.mac]


def test_bare_start_shows_help(context, woken):
    update = message_update()
    run(bot.start_command, update, context)
    assert woken == []
    assert "/wake" in replies(update)[0]


def test_wake_all(context, store, woken):
    store.add(DESKTOP)
    store.add(NAS)
    run(bot.wake_command, message_update(), context, "all")
    assert sorted(mac for mac, _, _ in woken) == sorted([DESKTOP.mac, NAS.mac])


def test_wake_unknown_device(context, store, woken):
    update = message_update()
    run(bot.wake_command, update, context, "ghost")
    assert woken == []
    assert "Unknown device <b>ghost</b>" in replies(update)[0]


def test_wake_without_argument_shows_keyboard(context, store, woken):
    store.add(DESKTOP)
    store.add(NAS)
    update = message_update()
    run(bot.wake_command, update, context)
    assert woken == []
    data = [row[0].callback_data for row in keyboard(update).inline_keyboard]
    assert data == ["wake:desktop", "wake:nas", "wake:all"]


def test_wake_button(context, store, woken):
    store.add(DESKTOP)
    update = button_update("wake:desktop")
    run(bot.button, update, context)
    assert [mac for mac, _, _ in woken] == [DESKTOP.mac]
    update.callback_query.answer.assert_awaited()


def test_wake_reports_socket_errors(context, store, monkeypatch):
    store.add(DESKTOP)

    def fail(*_):
        raise OSError("network unreachable")

    monkeypatch.setattr(bot.network, "wake", fail)
    update = message_update()
    run(bot.wake_command, update, context, "desktop")
    assert "Could not send the magic packet to desktop" in replies(update)[0]


def test_status(context, store, monkeypatch):
    store.add(DESKTOP)
    store.add(NAS)
    monkeypatch.setattr(bot.network, "is_up", AsyncMock(side_effect=lambda ip: ip == NAS.ip))
    update = message_update()
    run(bot.status_command, update, context, "all")
    assert replies(update)[0] == "🔴 <b>desktop</b> is down\n🟢 <b>nas</b> is up"


def test_status_for_a_device_added_just_before(context, store, monkeypatch):
    monkeypatch.setattr(bot.network, "is_up", AsyncMock(return_value=True))
    run(bot.add_command, message_update(), context, "desktop", DESKTOP.mac, DESKTOP.ip)
    update = message_update()
    run(bot.status_command, update, context, "desktop")
    assert "is up" in replies(update)[0]


def test_delete_asks_for_confirmation(context, store):
    store.add(DESKTOP)
    update = message_update()
    run(bot.delete_command, update, context, "desktop")
    assert store.get("desktop") == DESKTOP
    data = [button.callback_data for button in keyboard(update).inline_keyboard[0]]
    assert data == ["confirm-delete:desktop", "cancel:"]

    confirm = button_update("confirm-delete:desktop")
    run(bot.button, confirm, context)
    assert store.list() == []
    assert "deleted" in replies(confirm)[0]


def test_delete_all_is_not_allowed(context, store):
    store.add(DESKTOP)
    update = message_update()
    run(bot.delete_command, update, context, "all")
    assert store.list() == [DESKTOP]
    assert "Unknown device" in replies(update)[0]


def test_delete_cancel(context, store):
    store.add(DESKTOP)
    update = button_update("cancel:")
    run(bot.button, update, context)
    assert store.list() == [DESKTOP]
    assert replies(update) == ["Cancelled."]


def test_devices_lists_and_escapes(context, store):
    update = message_update()
    run(bot.devices_command, update, context)
    assert "No devices registered yet" in replies(update)[0]

    store.add(DESKTOP)
    update = message_update()
    run(bot.devices_command, update, context)
    assert replies(update)[0] == "<b>desktop</b>\n<code>aa:bb:cc:dd:ee:ff</code> · <code>192.168.1.20</code>"


def test_build_application_registers_every_command(context):
    application = bot.build_application(context.bot_data["settings"], context.bot_data["store"])
    commands = {command for handler in application.handlers[0] for command in getattr(handler, "commands", ())}
    assert commands == {"start", "help", "devices", "add", "wake", "status", "delete"}


def test_wake_skips_invalid_mac_stored_by_a_previous_version(context, store):
    # Former versions accepted MAC addresses with trailing garbage.
    store.add(Device("broken", "aa:bb:cc:dd:ee:01;garbage", "192.168.1.30"))
    update = message_update()
    run(bot.wake_command, update, context, "broken")
    assert "Could not send the magic packet to broken" in replies(update)[0]


@pytest.fixture
def mqtt_context(store):
    settings = Settings(
        bot_token="t", allowed_user_ids=frozenset({ALLOWED, 43}), broadcast_address="192.168.1.255", mqtt_host="mqtt"
    )
    return SimpleNamespace(bot_data={"settings": settings, "store": store}, args=[])


def application(context):
    return SimpleNamespace(bot_data=context.bot_data, bot=SimpleNamespace(send_message=AsyncMock()))


def sent(app):
    return [(call.args[0], call.args[1]) for call in app.bot.send_message.call_args_list]


def test_bind_then_press_binds_the_button(mqtt_context, store, woken):
    store.add(DESKTOP)
    update = message_update()
    update.effective_chat = SimpleNamespace(id=ALLOWED)
    run(bot.bind_command, update, mqtt_context, "desktop")
    assert "Press the button" in replies(update)[0]

    app = application(mqtt_context)
    asyncio.run(bot.handle_button_event(app, bot.mqtt.ButtonEvent("remote", "1_single")))
    assert store.device_for_button("remote", "1_single") == DESKTOP
    assert sent(app) == [(ALLOWED, "<code>remote</code> 1_single now wakes <b>desktop</b>.")]
    assert woken == []


def test_button_press_wakes_and_notifies_every_allowed_user(mqtt_context, store, woken):
    store.add(DESKTOP)
    store.bind("remote", "1_single", "desktop")
    app = application(mqtt_context)
    asyncio.run(bot.handle_button_event(app, bot.mqtt.ButtonEvent("remote", "1_single")))
    assert woken == [("aa:bb:cc:dd:ee:ff", "192.168.1.255", 9)]
    assert sorted(user for user, _ in sent(app)) == [ALLOWED, 43]
    assert "magic packet sent to <b>desktop</b>" in sent(app)[0][1]


def test_unbound_button_is_ignored(mqtt_context, store, woken):
    store.add(DESKTOP)
    app = application(mqtt_context)
    asyncio.run(bot.handle_button_event(app, bot.mqtt.ButtonEvent("remote", "1_single")))
    assert woken == []
    assert sent(app) == []


def test_expired_bind_does_not_bind(mqtt_context, store, woken):
    store.add(DESKTOP)
    mqtt_context.bot_data["pending_bind"] = ("desktop", ALLOWED, 0.0)
    app = application(mqtt_context)
    asyncio.run(bot.handle_button_event(app, bot.mqtt.ButtonEvent("remote", "1_single")))
    assert store.bindings() == []
    assert "pending_bind" not in mqtt_context.bot_data


def test_notification_failure_does_not_stop_other_users(mqtt_context, store, woken):
    store.add(DESKTOP)
    store.bind("switch", "single", "desktop")
    app = application(mqtt_context)
    app.bot.send_message.side_effect = [bot.TelegramError("blocked"), None]
    asyncio.run(bot.handle_button_event(app, bot.mqtt.ButtonEvent("switch", "single")))
    assert app.bot.send_message.await_count == 2


def test_unbind_and_list_buttons(mqtt_context, store):
    store.add(DESKTOP)
    store.bind("switch", "single", "desktop")
    update = message_update()
    run(bot.buttons_command, update, mqtt_context)
    assert replies(update) == ["<b>desktop</b> ← <code>switch</code> single"]

    update = message_update()
    run(bot.unbind_command, update, mqtt_context, "desktop")
    assert "removed" in replies(update)[0]
    assert store.bindings() == []


def test_mqtt_commands_hidden_without_broker(context):
    update = message_update()
    run(bot.help_command, update, context)
    assert "/bind" not in replies(update)[0]
