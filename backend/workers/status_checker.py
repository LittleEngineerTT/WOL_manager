from logging import Logger

import subprocess
import threading


class StatusChecker:

    def __init__(self, network: str, logger: Logger):
        self.devices = []
        self.devices_status = {}
        self.logger = logger
        self.network = network
        self.running = False


    def run(self):
        self.run_keep_status()
        self.run_check_status()


    def run_check_status(self):
        """
        Execute periodically check status.
        """
        self.check_status()
        threading.Timer(10, self.run_check_status).start()


    def run_keep_status(self):
        """
        Execute periodically keep status.
        """
        self.keep_status_reachable()
        threading.Timer(5, self.run_keep_status).start()


    def check_status(self):
        """
        Check if device is UP using arp table of the router.
        :return: True if device is UP, False otherwise
        """

        try:
            result = subprocess.run(['ip', 'neigh'], capture_output=True, text=True, check=True)
            self.analyse_arp_table(result)

            for device in self.devices:
                if device.mac not in self.devices_status.keys():
                    self.devices_status[device.mac] = "down"

        except subprocess.CalledProcessError:
            return


    def keep_status_reachable(self):
        """
        Keep device in ARP table avoiding STALE, DELAY... states.
        """
        for device in self.devices:
            subprocess.run(['ping', '-c', '1', device.ip, '-W', '1'], stdout=subprocess.DEVNULL)


    def analyse_arp_table(self, arp_table):
        """
        Analyse arp table to update devices status.
        :param arp_table: arp table to analyse
        :return:
        """

        targeted_mac = [device.mac for device in self.devices]

        for line in arp_table.stdout.strip().split('\n'):
            if len(targeted_mac) == 0:
                break

            if not line:
                continue

            parts = line.split()
            if len(parts) < 4:
                continue

            # Check if target is a managed device
            mac = parts[4] if len(parts) > 4 and parts[3] == "lladdr" else ""

            # Check for status
            if "REACHABLE" in parts:
                device_status = "up"
            elif any(status in parts for status in ["UNREACHABLE", "FAILED", "INCOMPLETE"]):
                device_status = "down"
            else:
                continue

            if mac and mac in targeted_mac:
                # Check for device shutdown
                if mac in self.devices_status.keys() and device_status == "down" and self.devices_status[
                    mac] == "up":
                    device = next((device for device in self.devices if device.mac == mac), None)
                    self.logger.info(f"{device.hostname} has been shutdown")

                targeted_mac.remove(mac)

            else:
                ip = parts[0]
                device = next((device for device in self.devices if device.ip == ip), None)

                if not device:
                    continue

                mac = device.mac
                if mac not in targeted_mac:
                    continue

                # Check for device shutdown
                if mac in self.devices_status.keys() and device_status == "down" and self.devices_status[
                    mac] == "up":
                    self.logger.info(f"{device.hostname} has been shutdown")

                targeted_mac.remove(mac)

            self.devices_status[mac] = device_status