import datetime
import json

import requests
from flask import Blueprint, render_template

import config

PUB = True


def update_member(member, formation, actual_n_serie):
    """
    Actualise un membre dans la base de données avec son numéro de série et ou les formations qu'il a suivi
    :param member: le membre à mettre à jour
    :param formation: la formation à ajouter ou None si il n'y en a pas
    :param actual_n_serie: le numéro de série de la carte RFID lue
    :return: le membre mis à jour
    """
    print(formation)
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
    content = {
        "array_options": {
            "options_impression3d": formations,
            "options_nserie": actual_n_serie
        }
    }
    print(content)
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


class Common:
    def __init__(self):
        self.bp = Blueprint('common', __name__, url_prefix='')

        self.bp.app_errorhandler(404)(self.error_404)
        self.bp.app_errorhandler(500)(self.error_500)

        self.bp.route('/')(self.index)
        self.bp.route('/404')(self.error_404)
        self.bp.route('/500')(self.error_500)
        self.bp.route('/formations')(self.formations)
        self.bp.route('/stock')(self.stock)

    def index(self):
        """
        Page d'accueil
        :return:
        """
        return render_template(template_name_or_list='index.html')

    def error_404(self, e=None):
        return render_template(template_name_or_list='404.html'), 404

    def error_500(self, e=None):
        return render_template(template_name_or_list='500.html'), 500

    def formations(self):
        return render_template(template_name_or_list='formations.html')

    def stock(self):
        return render_template(template_name_or_list='stock.html')
