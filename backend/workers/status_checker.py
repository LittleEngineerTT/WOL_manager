import subprocess
import threading

import nmap


class StatusChecker:

    def __init__(self, network: str):
        self.devices = []
        self.mapping = {}
        self.devices_status = {}
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
        :param mac: mac address of the given device
        :param config: config of the project
        :return: True if device is UP, False otherwise
        """

        try:
            result = subprocess.run(['ip', 'neigh'], capture_output=True, text=True, check=True)

            targeted_mac = [device.mac for device in self.devices]
            for line in result.stdout.strip().split('\n'):
                if len(targeted_mac) == 0:
                    break

                if line:
                    parts = line.split()

                    # Get only [IP_ADDRESS dev INTERFACE lladdr MAC_ADDRESS STATE] format
                    if len(parts) >= 4:
                        # Check if target is a managed device
                        mac = parts[4] if len(parts) > 4 and parts[3] == "lladdr" else ""

                        if mac and mac in targeted_mac:
                            status = parts[-1] if len(parts) > 5 else ""

                            # Store mac along its IP
                            ip = parts[0]
                            self.mapping[mac] = ip

                            # Check for status
                            self.devices_status[mac] = True if status == "REACHABLE" else False
                            targeted_mac.remove(mac)

            # mac not in ARP table
            for mac in targeted_mac:
                self.devices_status[mac] = False
                self.mapping[mac] = None

        except subprocess.CalledProcessError:
            return


    def keep_status_reachable(self):
        """
        Keep device in ARP table avoiding STALE, DELAY... states.
        """
        for device in self.devices:
            if not device.mac in self.mapping.keys() or not self.mapping[device.mac]:
                continue
            subprocess.run(['ping', '-c', '1', device.ip, '-W', '1'], stdout=subprocess.DEVNULL)
