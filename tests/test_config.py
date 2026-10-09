import pytest

from wol_bot.config import ConfigError, Settings


def test_defaults():
    settings = Settings.from_env({"TELEGRAM_BOT_TOKEN": "123:abc", "ALLOWED_USER_IDS": "1, 22,333"})
    assert settings.bot_token == "123:abc"
    assert settings.allowed_user_ids == {1, 22, 333}
    assert settings.database_path == "devices.db"
    assert settings.broadcast_address == "255.255.255.255"
    assert settings.wol_port == 9
    assert settings.mqtt_host is None
    assert settings.mqtt_base_topic == "zigbee2mqtt"


def test_mqtt_settings():
    settings = Settings.from_env(
        {
            "TELEGRAM_BOT_TOKEN": "t",
            "MQTT_HOST": "10.0.0.10",
            "MQTT_PORT": "1884",
            "MQTT_USERNAME": "wol",
            "MQTT_PASSWORD": "secret",
            "MQTT_BASE_TOPIC": "z2m/",
        }
    )
    assert (settings.mqtt_host, settings.mqtt_port) == ("10.0.0.10", 1884)
    assert (settings.mqtt_username, settings.mqtt_password) == ("wol", "secret")
    assert settings.mqtt_base_topic == "z2m"


def test_overrides():
    settings = Settings.from_env(
        {
            "TELEGRAM_BOT_TOKEN": "123:abc",
            "ALLOWED_USER_IDS": "",
            "DATABASE_PATH": "/tmp/x.db",
            "WOL_BROADCAST_ADDRESS": "192.168.1.255",
            "WOL_PORT": "7",
        }
    )
    assert settings.allowed_user_ids == frozenset()
    assert settings.database_path == "/tmp/x.db"
    assert settings.broadcast_address == "192.168.1.255"
    assert settings.wol_port == 7


@pytest.mark.parametrize(
    "env",
    [
        {},
        {"TELEGRAM_BOT_TOKEN": "  "},
        {"TELEGRAM_BOT_TOKEN": "t", "ALLOWED_USER_IDS": "me"},
        {"TELEGRAM_BOT_TOKEN": "t", "WOL_BROADCAST_ADDRESS": "lan"},
        {"TELEGRAM_BOT_TOKEN": "t", "WOL_PORT": "nine"},
        {"TELEGRAM_BOT_TOKEN": "t", "WOL_PORT": "70000"},
        {"TELEGRAM_BOT_TOKEN": "t", "MQTT_PORT": "0"},
        {"TELEGRAM_BOT_TOKEN": "t", "MQTT_BASE_TOPIC": "z2m/#"},
    ],
)
def test_invalid_settings(env):
    with pytest.raises(ConfigError):
        Settings.from_env(env)
