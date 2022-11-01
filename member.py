import json

import requests
import unidecode as unidecode
from flask import Blueprint, render_template, request

import common
import config
import rfid


class Member:
    """
    La classe membre permet de :

    - lire la fiche d'un adhérent à partir de sa carte RFID
    - lier une carte RFID à un adhérent
    - confirmer la liaison d'une carte RFID à un adhérent à l'aide d'un membre du conseil d'administration
    """

    def __init__(self):
        self.bp = Blueprint('member', __name__, url_prefix='/member')

        self.rfid = rfid.Serial()  # Initialisation du lecteur RFID

        self.bp.route('/scan')(self.scan_member)
        self.bp.route('/new_link', methods=['POST'])(self.new_link)
        self.bp.route('/confirm_link')(self.confirm_link)
        self.bp.route('/list', methods=['POST'])(self.list_member)

        self.data = None  # Données provenant des requêtes dolibarr sur les adhérents
        self.actual_n_serie = None  # Numéro de série de la dernière carte RFID lue
        self.actual_member = None  # Adhérent lié à la dernière carte RFID lue
        self.rfid.initialize()

    def scan_member(self):
        """
        Permet de lire la carte RFID et de demander la correspondance à la base de données sur dolibarr

        :return: index.html avec le message d'erreur "Connectez le PC à internet" si la connexion à la base de
        données n'est pas établie
        :return: index.html avec le message d'erreur "Connectez le lecteur RFID et réessayez" si la lecture de la
        carte n'est pas possible
        :return: index.html avec le message d'erreur "Adhérent inconnu" si l'adhérent n'est pas trouvé,
        l'onglet "Adhérent inconnu" avec le formulaire nom prénom apparait
        :return: index.html avec la fiche de l'adhérent si l'adhérent est trouvé
        """
        status = self.rfid.initialize()
        if status is False:
            return render_template(template_name_or_list='index.html', status='Connectez le lecteur RFID et réessayez')

        n_serie = self.rfid.read_serie()
        self.actual_n_serie = n_serie
        try:
            r = requests.get(config.url + config.url_member, headers=config.headers)
        except requests.ConnectionError:
            return render_template(template_name_or_list='index.html', status='Connectez le PC à internet')
        self.data = json.loads(r.text)
        for member in self.data:
            if member["array_options"] is not None and member["array_options"] != []:
                if member["array_options"]["options_nserie"] == n_serie:
                    member = common.process_member(member)
                    return render_template(template_name_or_list='index.html', status="Adhérent trouvé", member=member)
        return render_template(template_name_or_list='index.html', status='Adhérent inconnu', new=True)

    def new_link(self):
        """
        Permet de lier une carte RFID à un adhérent à partir de son nom et prénom, l'onglet "Adhérent inconnu" est
        accessible uniquement après avoir scanné une carte (fonction scan_member)

        :return: index.html avec le message d'erreur "Connectez le PC à internet" si la connexion à la base de
        données n'est pas établie
        :return: index.html avec le message "Non adhérent" si l'adhérent n'est pas trouvé
        :return: index.html avec le message d'erreur "Adhérent déjà lié" si la carte RFID est déjà liée à un
        adhérent, la fiche de l'adhérent apparait
        :return: index.html avec le message d'erreur "Adhérent non lié" si la carte RFID n'est pas liée, la fiche de
        l'adhérent apparait
        """
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
                found = common.process_member(member)
                break
        if found is None:
            return render_template(template_name_or_list='index.html', status='Non adhérent', new=True, unknow=True,
                                   lastname=lastname, firstname=firstname)
        elif found["array_options"]["options_nserie"] is None or found["array_options"]["options_nserie"] == "":
            self.actual_member = found
            return render_template(template_name_or_list='index.html', status='Adhérent non lié', new=True,
                                   to_link=True, lastname=lastname, firstname=firstname, member=found)
        else:
            return render_template(template_name_or_list='index.html', status='Adhérent déjà lié', new=True,
                                   adhesion=False, already_link=True, lastname=lastname, firstname=firstname,
                                   member=found)

    def confirm_link(self):
        """
        Permet de confirmer la liaison d'une carte RFID à un adhérent à partir de son nom et prénom, le bouton de
        confirmation n'est accessible que si l'adhérent a été trouvé par la fonction new_link mais qu'il n'est pas
        lié à une carte RFID. Un membre du conseil d'administration est nécessaire pour confirmer la liaison.

        :return: index.html avec le message d'erreur "Adhérent non lié" si l'administrateur n'est pas trouvé
        :return: index.html avec "Adhérent lié" si la liaison a été effectuée
        """

        self.rfid.initialize()
        n_serie = self.rfid.read_serie()

        users = requests.get(config.url + config.url_user, headers=config.headers).text
        users = json.loads(users)

        member = requests.get(config.url + config.url_member, headers=config.headers).text
        member = json.loads(member)
        lock = True

        for member in member:
            if member["array_options"] is not None and member["array_options"] != []:
                if member["array_options"]["options_nserie"] == n_serie:
                    member = common.process_member(member)
                    break
        for user in users:
            if user["lastname"] == member["lastname"] and user["firstname"] == member["firstname"]:
                groups = requests.get(
                        config.url + "users/" + user["id"] + "/groups?sortfield=t.rowid&sortorder=ASC&limit=100",
                        headers=config.headers).text
                print(groups)
                groups = json.loads(groups)
                for group in groups:
                    if group["name"] == "ConseilAdministration":
                        lock = False
                        break
                break

        if not lock:
            self.actual_member = common.update_member(self.actual_member, None, self.actual_n_serie)
            return render_template(template_name_or_list='index.html', status='Adhérent lié', new=True,
                                   member=self.actual_member, success=True, lastname=self.actual_member["lastname"],
                                   firstname=self.actual_member["firstname"])
        else:
            return render_template(template_name_or_list='index.html', status='Adhérent non lié', new=True,
                                   member=self.actual_member, error=True, lastname=member["lastname"],
                                   firstname=member["firstname"])

    def list_member(self):
        """
        Permet d'afficher la liste des adhérents

        :return: index.html avec la liste des adhérents
        """
        try:
            r = requests.get(config.url + config.url_member, headers=config.headers)
        except requests.ConnectionError:
            return render_template(template_name_or_list='index.html', status='Connectez le PC à internet')
        self.data = json.loads(r.text)
        for member in self.data:
            member = common.process_member(member)

        result_search = []

        if request.form['lastname'] != "" or request.form['firstname'] != "":
            for member in self.data:
                if member['lastname'].lower() == request.form['lastname'].lower():
                    result_search.append(member)
                elif member['firstname'].lower() == request.form['firstname'].lower():
                    result_search.append(member)
            result_search = sorted(result_search, key=lambda k: k['lastname'])
            return render_template(template_name_or_list='index.html', list_member=result_search)

        # sort self.data by firstname
        self.data = sorted(self.data, key=lambda k: k['lastname'])
        return render_template(template_name_or_list='index.html', list_member=self.data)
