import json

import requests
import serial


def request_adherent(token):
    url = "https://gestion.eirlab.net/api/index.php/members?sortfield=t.rowid&sortorder=ASC&limit=600"
    headers = {
        "Accept": "application/json",
        "DOLAPIKEY": token}

    r = requests.get(url, headers=headers)
    data = json.loads(r.text)
    return data


def find(serie, data):
    for member in data:
        try:
            if member["array_options"]["options_nserie"] == serie:
                return member
        except TypeError:
            pass
    return None


def add_member(data, line, token, last_name, first_name):
    found = None
    for member in data:
        try:
            if member["firstname"] == first_name and member["lastname"] == last_name:
                found = member
                break
        except TypeError:
            pass
    if found is None:
        print("Member not found")
    else:
        formations = found["array_options"]["options_impression3d"]
        id = found["id"]
        url = "https://gestion.eirlab.net/api/index.php/members/" + str(id)
        json = {
            "array_options": {
                "options_impression3d": formations,
                "options_nserie": line
            }
        }
        headers = {
            "Accept": "application/json",
            "DOLAPIKEY": token}
        r = requests.put(url, json=json, headers=headers)
        print(r.text)


def read_serial():
    ser = serial.Serial('/dev/ttyUSB1', 9600)
    while True:
        # read a line from the serial port in hexadecimal format
        line = ser.readline().strip().decode('utf-8')
        token = "sPfJjheCExeL"
        data = request_adherent(token)
        member = find(line, data)
        if member is None:
            print("No member found")
            last_name = input("Last name: ")
            first_name = input("First name: ")
            add_member(data, line, token, last_name, first_name)
        else:
            for key, value in member.items():
                if value is not None and value != "":
                    print(key, value)


if __name__ == "__main__":
    read_serial()
