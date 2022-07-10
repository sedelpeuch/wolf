import datetime
import json

import requests
import serial
import unidecode as unidecode
from flask import Blueprint, render_template, request

import config


class Member:
    def __init__(self):
        self.bp = Blueprint('member', __name__, url_prefix='/member')

        self.port_USB = "/dev/ttyUSB"
        self.ser = None
        self.baudrate = 9600

        self.bp.route('/scan')(self.scan_member)
        self.bp.route('/new_link', methods=['POST'])(self.new_link)
        self.bp.route('/confirm_link')(self.confirm_link)
        self.data = None
        self.actual_n_serie = None
        self.actual_member = None

    def initialize(self):
        for i in range(0, 10):
            try:
                self.ser = serial.Serial(self.port_USB + str(i), self.baudrate)
                return True
            except serial.serialutil.SerialException:
                pass
        if self.ser is None:
            return False

    def read_serie(self):
        try:
            line = self.ser.readline().strip().decode('utf-8')
            self.ser.close()
        except serial.serialutil.SerialException:
            self.ser.close()
            self.initialize()
            line = self.ser.readline().strip().decode('utf-8')
            self.ser.close()
        return line

    def process_member(self, member):
        timestamp = datetime.datetime.fromtimestamp(member["datec"])
        member["datec"] = timestamp.strftime('%d/%m/%Y')
        timestamp = timestamp + datetime.timedelta(days=365)
        if timestamp < timestamp.today():
            member["expired"] = True
        member["datem"] = timestamp.strftime('%d/%m/%Y')
        try:
            formations = list(member["array_options"]["options_impression3d"].split(','))
            member["impression_3d"] = True if '1' in formations else False
            member["laser"] = True if '2' in formations else False
            member["cnc"] = True if '3' in formations else False
        except TypeError:
            member["array_options"] = {}
            member["array_options"]["options_nserie"] = None
        return member

    def scan_member(self):
        status = self.initialize()
        if status is False:
            return render_template(template_name_or_list='index.html', status='Connectez le lecteur RFID et reeassayez')
        n_serie = self.read_serie()
        self.actual_n_serie = n_serie
        try:
            r = requests.get(config.url + config.url_member, headers=config.headers)
        except requests.ConnectionError:
            return render_template(template_name_or_list='index.html', status='Connectez le PC à internet')
        self.data = json.loads(r.text)
        for member in self.data:
            if member["array_options"] is not None and member["array_options"] != []:
                if member["array_options"]["options_nserie"] == n_serie:
                    member = self.process_member(member)
                    return render_template(template_name_or_list='index.html', status="Member found", member=member)
        return render_template(template_name_or_list='index.html', status='Adhérent inconnu', new=True)

    def new_link(self):
        lastname = request.form['lastname']
        lastname = unidecode.unidecode(lastname)
        firstname = request.form['firstname']
        firstname = unidecode.unidecode(firstname)
        found = None
        try:
            r = requests.get(config.url + config.url_member, headers=config.headers)
        except requests.ConnectionError:
            return render_template(template_name_or_list='index.html', status='Connectez le PC à internet')
        self.data = json.loads(r.text)
        for member in self.data:
            if unidecode.unidecode(member["firstname"]).lower() == firstname.lower() and unidecode.unidecode(
                    member["lastname"]).lower() == lastname.lower():
                found = self.process_member(member)
                break
        if found is None:
            return render_template(template_name_or_list='index.html', status='Non adhérent', new=True, unknow=True,
                                   lastname=lastname, firstname=firstname)
        elif found["array_options"]["options_nserie"] is None or found["array_options"]["options_nserie"] == "":
            self.actual_member = found
            return render_template(template_name_or_list='index.html', status='Adhérent non lié', new=True,
                                   to_link=True,
                                   lastname=lastname, firstname=firstname, member=found)
        else:
            return render_template(template_name_or_list='index.html', status='Adhérent déjà lié', new=True,
                                   adhesion=False, already_link=True,
                                   lastname=lastname, firstname=firstname, member=found)

    def confirm_link(self):
        # confirm adminitrator card

        self.initialize()
        n_serie = self.read_serie()

        users = requests.get(config.url + config.url_user, headers=config.headers).text
        users = json.loads(users)

        member = requests.get(config.url + config.url_member, headers=config.headers).text
        member = json.loads(member)
        lock = True

        for member in member:
            if member["array_options"] is not None and member["array_options"] != []:
                if member["array_options"]["options_nserie"] == n_serie:
                    member = self.process_member(member)
                    break
        for user in users:
            if user["lastname"] == member["lastname"] and user["firstname"] == member["firstname"]:
                if user["lasname"] != "Schmitz":
                    lock = False
                break
        # put modifications
        if not lock:
            try:
                formations = self.actual_member["array_options"]["options_impression3d"]
            except TypeError:
                formations = ""
            id = self.actual_member["id"]
            url = "https://gestion.eirlab.net/api/index.php/members/" + str(id)
            content = {
                "array_options": {
                    "options_impression3d": formations,
                    "options_nserie": self.actual_n_serie
                }
            }
            print(content)
            # r = requests.put(url, json=content, headers=config.headers)
            return render_template(template_name_or_list='index.html', status='Adhérent lié', new=True,
                                   member=self.actual_member, success=True)
        else:
            return render_template(template_name_or_list='index.html', status='Adhérent non lié', new=True,
                                   member=self.actual_member, error=True, lastname=member["lastname"],
                                   firstname=member["firstname"])
