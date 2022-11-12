import datetime
import json
import threading
import time
import traceback

import requests
from flask import Blueprint, render_template, request

import config
import rfid

PUB = True
LOGIN_IP = {}


def update_member(member, formation, actual_n_serie):
    """
    Actualise un membre dans la base de données avec son numéro de série et ou les formations qu'il a suivi
    :param member: le membre à mettre à jour
    :param formation: la formation à ajouter ou None si il n'y en a pas
    :param actual_n_serie: le numéro de série de la carte RFID lue
    :return: le membre mis à jour
    """
    try:
        formations = member["array_options"]["options_impression3d"]
    except (TypeError, KeyError):
        formations = ""
    if formations is None:
        formations = ""
    id = member["id"]
    if formation is not None:
        with open('/opt/wolf/formations.json') as json_file:
            json_formations = json.load(json_file)
            if json_formations[formation]['id'] not in formations:
                formations = formations + ',' + json_formations[formation]['id']
                member["array_options"]["options_impression3d"] = formations
    url = "https://gestion.eirlab.net/api/index.php/members/" + str(id)
    content = {"array_options": {"options_impression3d": formations, "options_nserie": actual_n_serie}}
    if PUB:
        r = requests.put(url, json=content, headers=config.headers)
    return member


def process_member(member):
    timestamp_begin = datetime.datetime.fromtimestamp(member["datec"])
    member["datec"] = timestamp_begin.strftime('%d/%m/%Y')
    try:
        timestamp = datetime.datetime.fromtimestamp(member["last_subscription_date_end"])
    except TypeError:
        timestamp = timestamp_begin + datetime.timedelta(days=365)
    if timestamp < timestamp.today():
        member["expired"] = True
    member["datem"] = timestamp.strftime('%d/%m/%Y')
    try:
        member = process_formations(member)
    except TypeError:
        member["array_options"] = {}
        member["array_options"]["options_nserie"] = None
    return member


def process_formations(member):
    formations = member["array_options"]["options_impression3d"]
    with open('/opt/wolf/formations.json') as json_file:
        json_formations = json.load(json_file)
        member['formations'] = {}
        member['no_formations'] = {}
        for formation in json_formations:
            if json_formations[formation]["id"] in formations:
                member["formations"][formation] = json_formations[formation]
            else:
                member["no_formations"][formation] = json_formations[formation]
    return member


def unlock(member_type: str, rfid: rfid.Serial, ip_adress: str = None):
    users = requests.get(config.url + config.url_user, headers=config.headers).text
    users = json.loads(users)
    # remove all user with user['statut'] != 1
    users = [user for user in users if user['statut'] == '1']

    members = requests.get(config.url + config.url_member, headers=config.headers).text
    members = json.loads(members)
    lock = True
    member = None
    user = None

    if ip_adress is not None:
        login = None
        for timestamp in LOGIN_IP:
            if LOGIN_IP[timestamp]['ip'] == ip_adress:
                if timestamp + 15 * 60 > time.time():
                    login = LOGIN_IP[timestamp]['login']
                    break
                else:
                    del LOGIN_IP[timestamp]
                    break
        if login is not None:
            for us in users:
                if us['login'] == login:
                    user = us
                    break
            for memb in members:
                if user["lastname"] == memb["lastname"] and user["firstname"] == memb["firstname"]:
                    groups = requests.get(
                            config.url + "users/" + user["id"] + "/groups?sortfield=t.rowid&sortorder=ASC&limit=100",
                            headers=config.headers).text
                    groups = json.loads(groups)
                    for group in groups:
                        if group["name"] == member_type:
                            lock = False
                            break
                    member = process_member(memb)
                    break
            return lock, member, user, "Connecté"
    try:
        rfid.initialize()
        n_serie = rfid.read_serie()
        if request.remote_addr != config.IP_PUBLIC_WOLF:
            return True, None, None, "Déconnecté"
    except AttributeError:
        return True, None, None, "Déconnecté"

    for memb in members:
        if memb["array_options"] is not None and memb["array_options"] != []:
            if memb["array_options"]["options_nserie"] == n_serie:
                member = process_member(memb)
                break
    for user in users:
        if user["lastname"] == member["lastname"] and user["firstname"] == member["firstname"]:
            groups = requests.get(
                    config.url + "users/" + user["id"] + "/groups?sortfield=t.rowid&sortorder=ASC&limit=100",
                    headers=config.headers).text
            groups = json.loads(groups)
            for group in groups:
                if group["name"] == member_type:
                    lock = False
                    break
            break
    return lock, member, user, "Reconnu"


class Common:
    def __init__(self, socketio):
        global socketio_instance
        self.bp = Blueprint('common', __name__, url_prefix='')

        self.bp.app_errorhandler(404)(self.error_404)
        self.bp.app_errorhandler(500)(self.error_500)

        self.bp.route('/')(self.index)
        self.bp.route('/404')(self.error_404)
        self.bp.route('/500')(self.error_500)
        self.bp.route('/formations')(self.formations)
        self.bp.route('/stock')(self.stock)
        self.bp.route('/emprunt')(self.emprunt)
        self.bp.route('/login', methods=['POST'])(self.connexion)
        self.bp.route('/logout')(self.deconnexion)
        self.client = {}

        self.socketio = socketio
        self.socketio.on_event('new_client', self.new_client, namespace='/login')
        threading.Thread(target=self.thread_websockect).start()

    def new_client(self, msg):
        self.client[request.remote_addr] = msg['data']

    def index(self):
        """
        Page d'accueil
        :return:
        """
        return render_template(template_name_or_list='index.html')

    def error_404(self, e=None):
        return render_template(template_name_or_list='404.html'), 404

    def error_500(self, e=None):
        trace = traceback.format_exc()
        lastline = trace.split('\n')[-2]
        firstword = lastline.split(':')[0]
        ticket = {'fk_soc': None, 'fk_project': None, 'origin_email': 'gestion@eirlab.net', 'fk_user_create': None,
                  'fk_user_assign': '4', 'subject': '[WOLF] - ' + firstword, 'message': trace}
        if PUB:
            r = requests.post(config.url + "tickets", json=ticket, headers=config.headers)
        return render_template(template_name_or_list='500.html', error=firstword, trace=trace), 500

    def formations(self):
        return render_template(template_name_or_list='formations.html')

    def stock(self):
        return render_template(template_name_or_list='stock.html')

    def emprunt(self):
        return render_template(template_name_or_list='emprunt.html')

    def thread_websockect(self):
        while True:
            time.sleep(2)
            find = False
            print("Clients")
            print(self.client)
            print("----------------")
            print("Login")
            print(LOGIN_IP)
            print("----------------")
            for c in self.client:
                for timestamp in LOGIN_IP:
                    if LOGIN_IP[timestamp]['ip'] == c:
                        find = True
                        if c == '192.168.0.117':
                            self.socketio.emit('login', {'login': "PCMEGABOT", 'sid': self.client[c]},
                                               namespace='/login')
                        else:
                            self.socketio.emit('login', {'login': LOGIN_IP[timestamp]['login'], 'sid': self.client[c]},
                                               namespace='/login')
                        break
                if not find:
                    self.socketio.emit('login', {'login': None, 'sid': self.client[c]}, namespace='/login')

    def connexion(self):
        ip_address = request.remote_addr
        name = request.form['login']
        password = request.form['password']
        result = requests.get(config.url + "login?login=" + name + "&password=" + password)
        if result.status_code == 200:
            LOGIN_IP[time.time()] = {"ip": ip_address, "login": name}

        return render_template(template_name_or_list='index.html', err="Connecté")

    def deconnexion(self):
        ip_address = request.remote_addr
        for timestamp in LOGIN_IP:
            if LOGIN_IP[timestamp]['ip'] == ip_address:
                del LOGIN_IP[timestamp]
                break
        return render_template(template_name_or_list='index.html', err="Déconnecté")
