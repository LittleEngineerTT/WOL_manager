from os import getenv
from typing import Self

import requests


headers = {
    "Content-Type": "application/json"
}


class Device:
    hostname: str
    mac: str
    ip: str

    def __init__(self, hostname: str, mac: str, ip: str):
        self.hostname = hostname
        self.mac = mac
        self.ip = ip


    def dict(self):
        data = {"hostname": self.hostname, "mac": self.mac, "ip": self.ip}
        return data


    @classmethod
    def get_devices(cls) -> list[Self]:
        devices = []
        try:
            response = requests.get(f"http://localhost:8000/devices", headers=headers)
            response.raise_for_status()
            devices = response.json()["devices"]

            new_devices = []
            for device in devices:
                new_devices.append(Device(**device))
            devices = new_devices

        except requests.exceptions.RequestException as e:
            print(e)
            pass
        return devices


    @classmethod
    def start_device(cls, devices: list[Self]) -> bool:
        try:
            for device in devices:
                response = requests.post(f"http://localhost:8000/start", json=device.dict(), headers=headers)
                response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(e)
            return False
        return True


    @classmethod
    def get_status(cls, device: Self) -> bool:
        try:
            response = requests.post(f"http://localhost:8000/status", json=device.dict(), headers=headers)
            response.raise_for_status()
            return response.json()["status"]
        except requests.exceptions.RequestException as e:
            print(e)
            return False


    @classmethod
    def register_device(cls, device: Self) -> bool:
        try:
            response = requests.post(f"http://localhost:8000/register", json=device.dict(), headers=headers)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(e)
            return False


    @classmethod
    def delete_device(cls, devices: list[Self]) -> bool:
        try:
            for device in devices:
                response = requests.post(f"http://localhost:8000/delete", json=device.dict(), headers=headers)
                response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(e)
            return False
