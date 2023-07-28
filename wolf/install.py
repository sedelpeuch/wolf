#! /usr/bin/env python3
"""
1. create_service(dir_path, service_name): This function generates a systemd service file at dir_path (defaults to the
script's directory if not specified). The name of the service file is specified with the service_name argument (
defaults to 'wolf.service'). The service is configured to start a Python script located in a virtual environment in
the parent directory of dir_path. If the service file already exists, it is overwritten, the systemd daemon is
reloaded, and the service is subsequently started or restarted.

2. create_token_file(token_dict, file_path):
This function writes a provided dictionary (token_dict) into a JSON file at
file_path (defaults to 'token.json' if not specified). If the file already exists, its content is replaced with the
new token_dict.

Overall, this script is useful for creating a Linux systemd service that manages a Python application and for storing
sensitive token information into a standalone JSON file. As a security measure, the actual token should be provided
dynamically and securely, not hardcoded. Also, the script should be run with sufficient permissions, usually as root
or via sudo, to allow the creation/modification of system services.
"""
import getpass
import json
import os
import subprocess
import time


def create_service(dir_path=os.path.dirname(os.path.realpath(__file__)), service_name='wolf.service'):
    """
    Creates a service file in the specified directory path. If the service file already exists, it is overwritten.

    :param dir_path: The directory path where the service file will be created. Defaults to the directory path of the
    current file.
    :param service_name: The name of the service file. Defaults to 'wolf.service.'
    :return: None
    """
    service_content = f"""
    [Unit]
    Description=Wolf Service
    After=multi-user.target

    [Service]
    WorkingDirectory={dir_path}
    ExecStart={dir_path}/../{'venv'}/bin/python3 {dir_path}/main.py
    User={getpass.getuser()}
    Restart=on-failure

    [Install]
    WantedBy=multi-user.target
    """

    service_path = f"/etc/systemd/system/{service_name}"

    if not os.path.exists(service_path):
        subprocess.run(["touch", service_path])
        with open(service_path, 'w') as service_file:
            service_file.write(service_content)
        subprocess.run(["systemctl", "daemon-reload"])
        subprocess.run(["systemctl", "is-active", "--quiet", service_name])
        time.sleep(2)
        subprocess.run(["systemctl", "enable", service_name])
        print(f"{service_name} created and enabled.")
    else:
        with open(service_path, 'w') as service_file:
            service_file.write(service_content)
        subprocess.run(["systemctl", "daemon-reload"])
        subprocess.run(["systemctl", "is-active", "--quiet", service_name])
        time.sleep(2)
        subprocess.run(["systemctl", "restart", service_name])
        print(f"{service_name} already exists and was restarted.")


def create_token_file(token_dict, file_path='token.json'):
    """
    Create a token file.

    :param token_dict: A dictionary containing tokens.
    :param file_path: Optional. The path of the token file. The default is 'token.json.'
    :return: None
    """
    if not os.path.exists(file_path):
        subprocess.run(["touch", file_path])
    with open(file_path, 'w') as token_file:
        json.dump(token_dict, token_file)
    print(f"token.json created at {file_path}.")


if __name__ == "__main__":
    service_name = 'wolf.service'
    token_dict = {"app": "token"}  # Needs to be replaced with the actual token. KEEP SECRET AND NEVER COMMIT TO GIT!

    create_service(service_name=service_name)
    create_token_file(token_dict)
