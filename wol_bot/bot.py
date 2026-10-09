"""Telegram handlers."""

from __future__ import annotations

import asyncio
import contextlib
import html
import logging
import time
from collections.abc import Awaitable, Callable, Coroutine
from typing import Any

from telegram import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.error import TelegramError
from telegram.ext import Application, ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes

from . import mqtt, network
from .config import Settings
from .storage import Device, DeviceExistsError, DeviceStore
from .validation import normalize_ip, normalize_mac, validate_name

log = logging.getLogger(__name__)

ALL = "all"
COMMANDS = (
    ("wake", "Wake a device: /wake NAME or /wake all"),
    ("status", "Check whether a device is up: /status NAME or /status all"),
    ("devices", "List registered devices"),
    ("add", "Register a device: /add NAME MAC IP"),
    ("delete", "Remove a device: /delete NAME"),
    ("bind", "Wake a device with a Zigbee button: /bind NAME, then press the button"),
    ("unbind", "Remove the buttons of a device: /unbind NAME"),
    ("buttons", "List Zigbee buttons and the devices they wake"),
    ("help", "Show this help"),
)


def _commands(settings: Settings) -> list[tuple[str, str]]:
    return [(name, text) for name, text in COMMANDS if settings.mqtt_host or name not in MQTT_COMMANDS]


def _help_text(settings: Settings) -> str:
    return "\n".join(f"/{name} — {description}" for name, description in _commands(settings))


MQTT_COMMANDS = frozenset({"bind", "unbind", "buttons"})
BIND_TIMEOUT = 60.0

Handler = Callable[[Update, ContextTypes.DEFAULT_TYPE], Coroutine[Any, Any, None]]


def _settings(context: ContextTypes.DEFAULT_TYPE) -> Settings:
    return context.bot_data["settings"]


def _store(context: ContextTypes.DEFAULT_TYPE) -> DeviceStore:
    return context.bot_data["store"]


def authorized(handler: Handler) -> Handler:
    """Only users listed in ALLOWED_USER_IDS may use the bot."""

    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        if user is None:
            return
        if user.id not in _settings(context).allowed_user_ids:
            log.warning("Rejected update from unauthorized user %s", user.id)
            if update.callback_query:
                await update.callback_query.answer("Not authorized", show_alert=True)
            elif update.effective_message:
                await update.effective_message.reply_text(
                    f"You are not allowed to use this bot. Your Telegram user ID is {user.id}."
                )
            return
        await handler(update, context)

    return wrapper


async def _reply(update: Update, text: str, keyboard: InlineKeyboardMarkup | None = None) -> None:
    """Answer a command, or edit the message when the update comes from a button."""
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
    elif update.effective_message:
        await update.effective_message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=keyboard)


def _device_keyboard(action: str, devices: list[Device], with_all: bool) -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton(device.name, callback_data=f"{action}:{device.name}")] for device in devices]
    if with_all and len(devices) > 1:
        buttons.append([InlineKeyboardButton("All devices", callback_data=f"{action}:{ALL}")])
    return InlineKeyboardMarkup(buttons)


def _resolve(store: DeviceStore, name: str) -> list[Device] | None:
    """Return the devices matching NAME ("all" matches every device), or None if unknown."""
    if name.lower() == ALL:
        return store.list()
    device = store.get(name)
    return [device] if device else None


async def _with_target(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    action: str,
    prompt: str,
    run: Callable[[Update, ContextTypes.DEFAULT_TYPE, list[Device]], Awaitable[None]],
    with_all: bool = True,
) -> None:
    """Run ACTION on the device given as argument, or show a keyboard to pick one."""
    store = _store(context)
    if not context.args:
        devices = store.list()
        if not devices:
            await _reply(update, "No devices registered yet. Add one with /add NAME MAC IP.")
            return
        await _reply(update, prompt, _device_keyboard(action, devices, with_all))
        return

    name = context.args[0]
    targets = _resolve(store, name) if with_all else ([d] if (d := store.get(name)) else None)
    if targets is None:
        await _reply(update, f"Unknown device <b>{html.escape(name)}</b>. See /devices.")
        return
    if not targets:
        await _reply(update, "No devices registered yet. Add one with /add NAME MAC IP.")
        return
    await run(update, context, targets)


async def _send_magic_packets(settings: Settings, devices: list[Device]) -> str:
    woken, failed = [], []
    for device in devices:
        try:
            await asyncio.to_thread(network.wake, device.mac, settings.broadcast_address, settings.wol_port)
            woken.append(device.name)
        except (OSError, ValueError):
            # ValueError: invalid MAC address stored by a previous version.
            log.exception("Could not send the magic packet to %s", device.name)
            failed.append(device.name)
    lines = []
    if woken:
        lines.append("Magic packet sent to " + ", ".join(f"<b>{html.escape(n)}</b>" for n in woken) + ".")
    if failed:
        lines.append("Could not send the magic packet to " + ", ".join(html.escape(n) for n in failed) + ".")
    return "\n".join(lines)


async def _wake(update: Update, context: ContextTypes.DEFAULT_TYPE, devices: list[Device]) -> None:
    await _reply(update, await _send_magic_packets(_settings(context), devices))


async def _status(update: Update, context: ContextTypes.DEFAULT_TYPE, devices: list[Device]) -> None:
    states = await asyncio.gather(*(network.is_up(device.ip) for device in devices))
    lines = [
        f"{'🟢' if up else '🔴'} <b>{html.escape(device.name)}</b> is {'up' if up else 'down'}"
        for device, up in zip(devices, states, strict=True)
    ]
    await _reply(update, "\n".join(lines))


async def _delete(update: Update, context: ContextTypes.DEFAULT_TYPE, devices: list[Device]) -> None:
    device = devices[0]
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Delete", callback_data=f"confirm-delete:{device.name}"),
                InlineKeyboardButton("Cancel", callback_data="cancel:"),
            ]
        ]
    )
    await _reply(update, f"Delete <b>{html.escape(device.name)}</b>?", keyboard)


@authorized
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply(update, html.escape(_help_text(_settings(context))))


@authorized
async def devices_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    devices = _store(context).list()
    if not devices:
        await _reply(update, "No devices registered yet. Add one with /add NAME MAC IP.")
        return
    lines = [
        f"<b>{html.escape(d.name)}</b>\n<code>{html.escape(d.mac)}</code> · <code>{html.escape(d.ip)}</code>"
        for d in devices
    ]
    await _reply(update, "\n\n".join(lines))


@authorized
async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args or []
    if len(args) != 3:
        await _reply(update, "Usage: /add NAME MAC IP\nExample: /add desktop a1:b2:c3:d4:e5:f6 192.168.1.20")
        return
    try:
        name, mac, ip = args
        device = Device(name=validate_name(name), mac=normalize_mac(mac), ip=normalize_ip(ip))
        _store(context).add(device)
    except (ValueError, DeviceExistsError) as err:
        await _reply(update, html.escape(str(err)))
        return
    await _reply(update, f"<b>{html.escape(device.name)}</b> added.")


@authorized
async def wake_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _with_target(update, context, "wake", "Which device should I wake up?", _wake)


@authorized
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Telegram sends a bare /start when a chat is opened: show the help.
    # /start NAME is kept as an alias of /wake NAME.
    if not context.args:
        await _reply(update, "Wake-on-LAN bot.\n\n" + html.escape(_help_text(_settings(context))))
        return
    await _with_target(update, context, "wake", "Which device should I wake up?", _wake)


@authorized
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _with_target(update, context, "status", "Which device should I check?", _status)


@authorized
async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _with_target(update, context, "delete", "Which device should I delete?", _delete, with_all=False)


@authorized
async def bind_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _with_target(update, context, "bind", "Which device should a button wake?", _start_binding, with_all=False)


async def _start_binding(update: Update, context: ContextTypes.DEFAULT_TYPE, devices: list[Device]) -> None:
    chat = update.effective_chat
    if chat is None:
        return
    device = devices[0]
    context.bot_data["pending_bind"] = (device.name, chat.id, time.monotonic() + BIND_TIMEOUT)
    await _reply(
        update,
        f"Press the button that should wake <b>{html.escape(device.name)}</b> within {BIND_TIMEOUT:.0f} seconds.\n"
        "Each kind of press (single, double, long…) can wake a different device.",
    )


@authorized
async def unbind_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _with_target(update, context, "unbind", "Which device should lose its buttons?", _unbind, with_all=False)


async def _unbind(update: Update, context: ContextTypes.DEFAULT_TYPE, devices: list[Device]) -> None:
    device = devices[0]
    removed = _store(context).unbind(device.name)
    name = html.escape(device.name)
    await _reply(update, f"Buttons of <b>{name}</b> removed." if removed else f"No button wakes <b>{name}</b>.")


@authorized
async def buttons_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    bindings = _store(context).bindings()
    if not bindings:
        await _reply(update, "No buttons yet. Bind one with /bind NAME.")
        return
    lines = [
        f"<b>{html.escape(b.device)}</b> ← <code>{html.escape(b.button)}</code> {html.escape(b.action)}"
        for b in bindings
    ]
    await _reply(update, "\n".join(lines))


async def handle_button_event(application: Application, event: mqtt.ButtonEvent) -> None:
    """Bind a button when /bind is pending, otherwise wake the device bound to it."""
    store: DeviceStore = application.bot_data["store"]
    settings: Settings = application.bot_data["settings"]
    button, action = html.escape(event.button), html.escape(event.action)

    pending = application.bot_data.pop("pending_bind", None)
    if pending:
        name, chat_id, deadline = pending
        if time.monotonic() <= deadline and store.get(name):
            previous = store.bind(event.button, event.action, name)
            text = f"<code>{button}</code> {action} now wakes <b>{html.escape(name)}</b>."
            if previous and previous.lower() != name.lower():
                text += f" It woke <b>{html.escape(previous)}</b> before."
            await application.bot.send_message(chat_id, text, parse_mode=ParseMode.HTML)
            return

    device = store.device_for_button(event.button, event.action)
    if device is None:
        return
    result = await _send_magic_packets(settings, [device])
    text = f"Button <code>{button}</code> {action}: {result[0].lower()}{result[1:]}"
    for user_id in settings.allowed_user_ids:
        try:
            await application.bot.send_message(user_id, text, parse_mode=ParseMode.HTML)
        except TelegramError as err:
            # The user never opened a chat with the bot, or blocked it.
            log.warning("Could not notify user %s: %s", user_id, err)


@authorized
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None:
        return
    action, _, name = (query.data or "").partition(":")
    store = _store(context)

    if action == "cancel":
        await _reply(update, "Cancelled.")
        return
    if action == "confirm-delete":
        deleted = store.delete(name)
        await _reply(update, f"<b>{html.escape(name)}</b> deleted." if deleted else "Device already deleted.")
        return

    runners = {"wake": _wake, "status": _status, "delete": _delete, "bind": _start_binding, "unbind": _unbind}
    if action not in runners:
        await query.answer()
        return
    single = action in {"delete", "bind", "unbind"}
    targets = ([d] if (d := store.get(name)) else None) if single else _resolve(store, name)
    if not targets:
        await _reply(update, f"Unknown device <b>{html.escape(name)}</b>. See /devices.")
        return
    await runners[action](update, context, targets)


async def _on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    log.error("Unhandled error while processing an update", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text("Something went wrong, see the bot logs.")


async def _post_init(application: Application) -> None:
    settings: Settings = application.bot_data["settings"]
    await application.bot.set_my_commands([BotCommand(name, text) for name, text in _commands(settings)])
    if settings.mqtt_host:
        application.bot_data["mqtt_task"] = asyncio.create_task(
            mqtt.listen(settings, lambda event: handle_button_event(application, event))
        )


async def _post_stop(application: Application) -> None:
    task: asyncio.Task[None] | None = application.bot_data.pop("mqtt_task", None)
    if task:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task


def build_application(settings: Settings, store: DeviceStore) -> Application:
    application = ApplicationBuilder().token(settings.bot_token).post_init(_post_init).post_stop(_post_stop).build()
    application.bot_data["settings"] = settings
    application.bot_data["store"] = store

    for name, handler in (
        ("start", start_command),
        ("help", help_command),
        ("devices", devices_command),
        ("add", add_command),
        ("wake", wake_command),
        ("status", status_command),
        ("delete", delete_command),
    ):
        application.add_handler(CommandHandler(name, handler))
    if settings.mqtt_host:
        for name, handler in (("bind", bind_command), ("unbind", unbind_command), ("buttons", buttons_command)):
            application.add_handler(CommandHandler(name, handler))
    application.add_handler(CallbackQueryHandler(button))
    application.add_error_handler(_on_error)
    return application
