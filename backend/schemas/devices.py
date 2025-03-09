from models.devices import Device as DeviceModel
from libs.wake_me_up import wake_me_up

from io import StringIO

import sys
import time

from pydantic import BaseModel, field_validator
from re import match

import paramiko


class Device(BaseModel):
    hostname: str
    mac: str
    interface: str

    @field_validator('mac')
    @classmethod
    def is_valid(cls, mac: str) -> bool:
        """
        Check if device fields are valid.
        :return: False if any field is invalid else True
        """
        # Check for valid mac
        mac_regex = r"([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}"
        if not match(mac_regex, mac):
            raise ValueError('"foobar" not found in a')

        return mac


    @classmethod
    def get_devices(cls) -> list[DeviceModel]:
        """
        Get all devices.
        """
        devices = DeviceModel.get_devices()
        return devices


    def check_status(self, config: dict) -> bool:
        """
        Check if device is up using arp table of the router.
        :param mac: mac address of the given device
        :param config: config of the project
        :return: True if device is up, False otherwise
        """

        # Get data from config
        ssh_filename = config["path_to_private_key"]
        mdp = config["ssh_password"]
        router_ip = config["router_ip"]
        router_hostname = config["router_hostname"]

        # SSH setup
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(router_ip, username=router_hostname, password=mdp, key_filename=ssh_filename)
        #TODO: ping to ensure device presence inside arp table

        # Extend check to five seconds to ensure reliability
        for i in range(5):
            time.sleep(1)
            stdin, stdout, stderr = ssh.exec_command("ip neigh")
            buffer = StringIO()
            sys.stdout = buffer

            # without print cannot retrieve data
            print(stdout.read().decode())
            ip_neigh_output = buffer.getvalue()

            # restore stdout to default for print()
            sys.stdout = sys.__stdout__
            # This will be stored in the ip_neigh_output variable
            all_lines = ip_neigh_output.split("\n")

            for line in all_lines:
                line = line[:-1]

                # Check if device is Reachable
                if self.mac.lower() in line:
                    if line.endswith("REACHABLE"):
                        ssh.close()
                        return True
        ssh.close()
        return False


    def start(self, config: dict) -> None:
        """
        Send wake on lan packet to this device.
        Check if packets must be sent inside or outside the subnet.
        :param config: config of the project
        :return:
        """

        # Check if sending packet outside the subnet
        if self.interface:
            wake_me_up(mac=self.mac, config=config, interface=self.interface)
        else:
            # Sending packet inside the subnet
            # TODO: let non router send the wol packet
            pass


    def register(self) -> int:
        """
        Register new device
        :return: status code
        """

        devices = self.get_devices()

        # Check for duplicate
        for device in devices:
            if device.mac == self.mac:
                return 409

        DeviceModel.add_device(self.dict())
        return 200


    def delete(self) -> None:
        """
        Delete device
        :return: None
        """
        DeviceModel.delete_device(self.dict())
