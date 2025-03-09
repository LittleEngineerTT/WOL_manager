import paramiko


def wake_me_up(mac: str, config: dict, interface: str) -> None:
    """
    Send wol packet outside the subnet.
    Packet must be sent in the same layer 2.
    :param mac: mac of the device
    :param config: configuration of the project
    :param interface: router interface to send the packet.
    :return: None
    """
    ssh = paramiko.SSHClient()
    ssh_filename = config["path_to_private_key"]
    mdp = config["ssh_password"]
    router_ip = config["router_ip"]
    router_hostname = config["router_hostname"]
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(router_ip, username=router_hostname, password=mdp, key_filename=ssh_filename)
    stdin, stdout, stderr = ssh.exec_command("sudo /usr/sbin/etherwake -i " + interface + " " + mac)
    ssh.close()
