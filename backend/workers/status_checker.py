import subprocess
import threading


class StatusChecker:

    def __init__(self, network: str):
        self.devices = []
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

                            # Check for status
                            if status == "REACHABLE":
                                device_status = "up"
                            elif status == "UNREACHABLE":
                                device_status = "down"
                            else:
                                continue

                            self.devices_status[mac] = device_status
                            targeted_mac.remove(mac)

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
