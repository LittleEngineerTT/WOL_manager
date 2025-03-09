import paramiko


def wake_me_up(mac, config, interface):
    ssh = paramiko.SSHClient()
    ssh_filename = config["path_to_private_key"]
    mdp = config["ssh_password"]
    router_ip = config["router_ip"]
    router_hostname = config["router_hostname"]
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(router_ip, username=router_hostname, password=mdp, key_filename=ssh_filename)
    stdin, stdout, stderr = ssh.exec_command("sudo /usr/sbin/etherwake -i " + interface + " " + mac)
    ssh.close()