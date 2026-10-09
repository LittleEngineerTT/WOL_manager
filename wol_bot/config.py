"""Runtime settings, read from environment variables."""

from __future__ import annotations

import ipaddress
import os
from collections.abc import Mapping
from dataclasses import dataclass


class ConfigError(Exception):
    """A required setting is missing or invalid."""


@dataclass(frozen=True)
class Settings:
    bot_token: str
    allowed_user_ids: frozenset[int]
    database_path: str = "devices.db"
    broadcast_address: str = "255.255.255.255"
    wol_port: int = 9
    mqtt_host: str | None = None
    mqtt_port: int = 1883
    mqtt_username: str | None = None
    mqtt_password: str | None = None
    mqtt_base_topic: str = "zigbee2mqtt"

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> Settings:
        env = os.environ if env is None else env

        token = env.get("TELEGRAM_BOT_TOKEN", "").strip()
        if not token:
            raise ConfigError("TELEGRAM_BOT_TOKEN is required")

        raw_ids = env.get("ALLOWED_USER_IDS", "")
        try:
            user_ids = frozenset(int(item) for item in raw_ids.replace(" ", "").split(",") if item)
        except ValueError as err:
            raise ConfigError("ALLOWED_USER_IDS must be a comma-separated list of Telegram user IDs") from err

        broadcast = env.get("WOL_BROADCAST_ADDRESS", cls.broadcast_address).strip()
        try:
            ipaddress.ip_address(broadcast)
        except ValueError as err:
            raise ConfigError(f"WOL_BROADCAST_ADDRESS is not an IP address: {broadcast}") from err

        port = _port(env, "WOL_PORT", cls.wol_port)
        mqtt_host = env.get("MQTT_HOST", "").strip() or None
        base_topic = env.get("MQTT_BASE_TOPIC", cls.mqtt_base_topic).strip().strip("/")
        if not base_topic or any(char in base_topic for char in "+#"):
            raise ConfigError("MQTT_BASE_TOPIC must be a topic without wildcards")

        return cls(
            bot_token=token,
            allowed_user_ids=user_ids,
            database_path=env.get("DATABASE_PATH", cls.database_path),
            broadcast_address=broadcast,
            wol_port=port,
            mqtt_host=mqtt_host,
            mqtt_port=_port(env, "MQTT_PORT", cls.mqtt_port),
            mqtt_username=env.get("MQTT_USERNAME", "").strip() or None,
            mqtt_password=env.get("MQTT_PASSWORD") or None,
            mqtt_base_topic=base_topic,
        )


def _port(env: Mapping[str, str], name: str, default: int) -> int:
    try:
        port = int(env.get(name) or default)
    except ValueError as err:
        raise ConfigError(f"{name} must be an integer") from err
    if not 1 <= port <= 65535:
        raise ConfigError(f"{name} must be between 1 and 65535")
    return port
