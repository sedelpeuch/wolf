import datetime
import confif
import requests
from flask import Blueprint, render_template

formation_dictionnary = {"laser": '1', "impression_3d": '2', "cnc": '3'}
PUB = False


def update_member(member, formation, actual_n_serie):
    print(formation)
    try:
        formations = member["array_options"]["options_impression3d"]
    except (TypeError, KeyError):
        formations = ""
    id = member["id"]
    if formation is not None:
        if formation_dictionnary[formation] not in formations:
            formations = formations + ',' + formation_dictionnary[formation]
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
    print(member)
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
    if formations is not None:
        list(formations.split(','))
        member["impression_3d"] = True if '2' in formations else False
        member["laser"] = True if '1' in formations else False
        member["cnc"] = True if '3' in formations else False
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

    def index(self):
        return render_template(template_name_or_list='index.html')

    def error_404(self, e=None):
        return render_template(template_name_or_list='404.html'), 404

    def error_500(self, e=None):
        return render_template(template_name_or_list='500.html'), 500

    def formations(self):
        return render_template(template_name_or_list='formations.html')
