import os
import sys
import time
from io import StringIO

import paramiko

NB_TRY = 6

def status_checker(mac, starting_time, config):
    ssh_filename = config["path_to_private_key"]
    mdp = config["ssh_password"]
    router_ip = config["router_ip"]
    router_hostname = config["router_hostname"]
    time.sleep(int(starting_time))
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(router_ip, username=router_hostname, password=mdp, key_filename=ssh_filename)
    for i in range(5):
        stdin, stdout, stderr = ssh.exec_command("ip neigh")
        buffer = StringIO()
        sys.stdout = buffer
        print(stdout.read().decode())
        ip_neigh_output = buffer.getvalue()
        # restore stdout to default for print()
        sys.stdout = sys.__stdout__
        # This will be stored in the ip_neigh_output variable
        all_lines = ip_neigh_output.split("\n")
        for line in all_lines:
            line = line[:-1]
            if mac.lower() in line:
                if line.endswith("REACHABLE"):
                    ssh.close()
                    return True
    ssh.close()
    return False
