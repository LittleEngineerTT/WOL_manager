import json

import pytest

from wol_bot.mqtt import ButtonEvent, parse_event


def payload(**state):
    return json.dumps(state).encode()


def test_parses_button_action():
    event = parse_event("zigbee2mqtt/desk button", payload(action="single", battery=90), "zigbee2mqtt")
    assert event == ButtonEvent(button="desk button", action="single")


def test_keeps_friendly_names_with_slashes():
    event = parse_event("z2m/office/remote", payload(action="2_double"), "z2m")
    assert event == ButtonEvent(button="office/remote", action="2_double")


@pytest.mark.parametrize(
    ("topic", "data"),
    [
        ("zigbee2mqtt/desk", payload(battery=90)),
        ("zigbee2mqtt/desk", payload(action="")),
        ("zigbee2mqtt/desk", payload(action=None)),
        ("zigbee2mqtt/desk", b"not json"),
        ("zigbee2mqtt/desk", b"[1, 2]"),
        ("zigbee2mqtt/desk/action", b"single"),
        ("zigbee2mqtt/desk/availability", payload(state="online")),
        ("zigbee2mqtt/desk/set", payload(action="single")),
        ("zigbee2mqtt/bridge/event", payload(action="single")),
        ("other/desk", payload(action="single")),
    ],
)
def test_ignores_other_messages(topic, data):
    assert parse_event(topic, data, "zigbee2mqtt") is None
