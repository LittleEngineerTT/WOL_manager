"""Zigbee2MQTT button events."""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

import aiomqtt

from .config import Settings

log = logging.getLogger(__name__)

RECONNECT_DELAY = 10.0
# Zigbee2MQTT topics that are not device state messages. The legacy
# <device>/action topic duplicates the "action" field of the state message.
_IGNORED_SEGMENTS = frozenset({"availability", "set", "get", "action"})


@dataclass(frozen=True)
class ButtonEvent:
    button: str
    action: str


def parse_event(topic: str, payload: object, base_topic: str) -> ButtonEvent | None:
    """Return the button action carried by a Zigbee2MQTT state message, if any."""
    prefix = f"{base_topic}/"
    if not topic.startswith(prefix):
        return None
    button = topic.removeprefix(prefix)
    segments = button.split("/")
    if segments[0] == "bridge" or segments[-1] in _IGNORED_SEGMENTS:
        return None
    if isinstance(payload, bytes | bytearray):
        payload = payload.decode(errors="replace")
    if not isinstance(payload, str):
        return None
    try:
        state = json.loads(payload)
    except ValueError:
        return None
    action = state.get("action") if isinstance(state, dict) else None
    if not isinstance(action, str) or not action:
        return None
    return ButtonEvent(button=button, action=action)


async def listen(settings: Settings, on_event: Callable[[ButtonEvent], Awaitable[None]]) -> None:
    """Call ON_EVENT for every button action, reconnecting to the broker forever."""
    assert settings.mqtt_host
    topic = f"{settings.mqtt_base_topic}/#"
    while True:
        try:
            async with aiomqtt.Client(
                settings.mqtt_host,
                settings.mqtt_port,
                username=settings.mqtt_username,
                password=settings.mqtt_password,
            ) as client:
                await client.subscribe(topic)
                log.info("Listening to %s on %s:%s", topic, settings.mqtt_host, settings.mqtt_port)
                async for message in client.messages:
                    # Retained messages replay the last state when subscribing:
                    # they are not new button presses.
                    if message.retain:
                        continue
                    event = parse_event(str(message.topic), message.payload, settings.mqtt_base_topic)
                    if event is None:
                        continue
                    log.info("Button %s: %s", event.button, event.action)
                    try:
                        await on_event(event)
                    except Exception:
                        log.exception("Could not handle the button action %s of %s", event.action, event.button)
        except aiomqtt.MqttError as err:
            log.warning("MQTT broker unavailable (%s), retrying in %.0f s", err, RECONNECT_DELAY)
            await asyncio.sleep(RECONNECT_DELAY)
