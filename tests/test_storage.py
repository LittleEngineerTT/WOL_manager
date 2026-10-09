import sqlite3

import pytest

from wol_bot.storage import Device, DeviceExistsError, DeviceStore

DESKTOP = Device("desktop", "aa:bb:cc:dd:ee:ff", "192.168.1.20")


@pytest.fixture
def store(tmp_path):
    return DeviceStore(tmp_path / "data" / "devices.db")


def test_add_list_get_delete(store):
    store.add(DESKTOP)
    assert store.list() == [DESKTOP]
    assert store.get("DESKTOP") == DESKTOP
    assert store.delete("desktop") is True
    assert store.list() == []
    assert store.delete("desktop") is False
    assert store.get("desktop") is None


def test_devices_are_sorted_by_name(store):
    store.add(Device("nas", "aa:bb:cc:dd:ee:01", "192.168.1.2"))
    store.add(Device("Desktop", "aa:bb:cc:dd:ee:02", "192.168.1.3"))
    assert [d.name for d in store.list()] == ["Desktop", "nas"]


@pytest.mark.parametrize(
    ("device", "field"),
    [
        (Device("Desktop", "aa:bb:cc:dd:ee:01", "192.168.1.21"), "name"),
        (Device("laptop", "aa:bb:cc:dd:ee:ff", "192.168.1.21"), "MAC address"),
        (Device("laptop", "aa:bb:cc:dd:ee:01", "192.168.1.20"), "IP address"),
    ],
)
def test_duplicates_are_rejected(store, device, field):
    store.add(DESKTOP)
    with pytest.raises(DeviceExistsError, match=field):
        store.add(device)
    assert store.list() == [DESKTOP]


def test_reads_database_of_the_former_web_backend(tmp_path):
    path = tmp_path / "devices.db"
    with sqlite3.connect(path) as conn:
        conn.execute(
            "CREATE TABLE devices (hostname VARCHAR NOT NULL, mac VARCHAR NOT NULL, ip VARCHAR NOT NULL,"
            " PRIMARY KEY (mac), UNIQUE (mac), UNIQUE (ip))"
        )
        conn.execute("INSERT INTO devices VALUES ('desktop', 'AA:BB:CC:DD:EE:FF', '192.168.1.20')")
    conn.close()

    store = DeviceStore(path)
    assert store.list() == [DESKTOP]
    with pytest.raises(DeviceExistsError):
        store.add(Device("other", "aa:bb:cc:dd:ee:ff", "192.168.1.30"))


def test_button_bindings(tmp_path):
    store = DeviceStore(tmp_path / "devices.db")
    desktop = Device("desktop", "aa:bb:cc:dd:ee:ff", "192.168.1.20")
    nas = Device("nas", "aa:bb:cc:dd:ee:01", "192.168.1.2")
    store.add(desktop)
    store.add(nas)

    assert store.bind("remote", "1_single", "desktop") is None
    assert store.bind("remote", "2_single", "nas") is None
    assert store.device_for_button("remote", "1_single") == desktop
    assert store.device_for_button("remote", "3_single") is None

    assert store.bind("remote", "1_single", "nas") == "desktop"
    assert store.device_for_button("remote", "1_single") == nas
    assert [b.action for b in store.bindings()] == ["1_single", "2_single"]

    assert store.unbind("NAS") == 2
    assert store.bindings() == []


def test_deleting_a_device_removes_its_buttons(tmp_path):
    store = DeviceStore(tmp_path / "devices.db")
    store.add(Device("desktop", "aa:bb:cc:dd:ee:ff", "192.168.1.20"))
    store.bind("switch", "single", "desktop")
    store.delete("desktop")
    store.add(Device("desktop", "aa:bb:cc:dd:ee:02", "192.168.1.21"))
    assert store.device_for_button("switch", "single") is None
