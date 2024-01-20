#! /usr/bin/env python3
"""
Create_token_file(token_dict, file_path):
This function writes a provided dictionary (token_dict) into a JSON file at
file_path (defaults to 'token.json' if not specified). If the file already exists, its content
is replaced with the
new token_dict.
"""
import argparse
import getpass
import json
import os
import subprocess


def create_token_file(token_data, file_path="token.json"):
    """
    Create a token file.

    :param token_data: A dictionary containing tokens.
    :param file_path: Optional. The path of the token file. The default is 'token.json.'
    :return: None
    """
    if not os.path.exists(file_path):
        subprocess.run(["touch", file_path])
    with open(file_path, "w") as token_file:
        json.dump(token_data, token_file)
    print(f"token.json created at {file_path}.")


def parse_arguments():
    """
    Parses command line arguments and returns the parsed arguments.

    :return: A tuple containing the parsed arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--user", type=str, default=getpass.getuser(), help="user name"
    )
    unknown_args = parser.parse_known_args()
    user_args = {}
    for arg in unknown_args[1]:
        if arg.startswith("--"):
            key = arg[2:]
            value = unknown_args[1][unknown_args[1].index(arg) + 1]
            user_args[key] = value

    return unknown_args[0], user_args


if __name__ == "__main__":
    args = parse_arguments()
    if args[1]:
        token_dict = args[1]
    else:
        # Needs to be replaced with the actual token. KEEP SECRET AND NEVER COMMIT TO GIT!
        token_dict = {"app": "token"}
    create_token_file(token_dict)
