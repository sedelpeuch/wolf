import json

import requests
import unidecode
from flask import Blueprint, render_template, request

import common
import config
import rfid


class Formations:
    """
    La classe formation permet d'ajouter une formation à un ou plusieurs adhérents
    """

    def __init__(self):
        self.bp = Blueprint('formations', __name__, url_prefix='/formations')

        self.rfid = rfid.Serial()
        self.bp.route('/start')(self.start)
        self.bp.route('/confirm', methods=['POST'])(self.confirm)
        self.bp.route('/add', methods=['GET'])(self.add)
        self.bp.route('/new_link', methods=['POST'])(self.new_link)
        self.bp.route('/confirm_link', methods=['GET'])(self.confirm_link)
        self.formation = None
        self.fabmanager = None
        self.job = ""
        self.list_add = []
        self.actual_n_serie = ""

    def start(self):
        """
        Débute le processus d'ajout de formations aux adhérents. Initialise le lecteur RFID et attend qu'une carte
        soit posée. Lorsqu'elle est posée la fonciton vérifie qu'il fait bien parti du groupe "Fabmanager" sur dolibarr

        :return: formation.html avec les informations du fabmanager et la liste des formations qu'il peut donner si la carte est celle d'un fabmanager
        :return: formation.html avec un message d'erreur sinon
        """
        self.rfid.initialize()
        self.formation = None
        self.fabmanager = None
        self.job = ""
        self.list_add = []
        self.actual_n_serie = ""
        n_serie = self.rfid.read_serie()

        users = requests.get(config.url + config.url_user, headers=config.headers).text
        users = json.loads(users)

        member = requests.get(config.url + config.url_member, headers=config.headers).text
        member = json.loads(member)
        lock = True
        job = ""

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
                groups = json.loads(groups)
                self.job = user["job"]
                for group in groups:
                    if group["name"] == "Fabmanagers":
                        lock = False
                        break
                break
        if not lock:
            self.fabmanager = member
            return render_template('formations.html', member=member, job=self.job)
        else:
            return render_template('formations.html', error="Vous n'êtes pas autorisé à accéder à cette page")

    def confirm(self):
        """
        Récupère la formation choisie par le fabmanager

        :return: formation.html avec le fabmanager ainsi que la formation en cours
        :return: formation.html avec un message d'erreur demandant de choisir une formation sinon
        """
        try:
            self.formation = request.form['formations']
        except KeyError:
            return render_template(template_name_or_list='formations.html', error='Veuillez choisir une formation',
                                   job=self.job, fabmanager=self.fabmanager, member=self.fabmanager)
        return render_template('formations.html', formation=self.formation, fabmanager=self.fabmanager, job=self.job)

    def add(self):
        """
        Initialise le lecteur RFID et attends la lecture d'une carte puis lui ajoute la formation choisie par le
        fabmanager

        :return: formation.html avec la liste des adhérents ajoutés à la formation et la fiche de la dernière personne ajoutée
        :return: formation.html avec la liste des adhérents ajoutés à la formation et un formulaire pour remplir un nom et prénom si la carte n'a pas été reconnue
        """
        self.rfid.initialize()
        self.actual_n_serie = self.rfid.read_serie()
        try:
            r = requests.get(config.url + config.url_member, headers=config.headers)
        except requests.ConnectionError:
            return render_template(template_name_or_list='index.html', status='Connectez le PC à internet')
        data = json.loads(r.text)
        member = None
        for user in data:
            if user["array_options"] is not None and user["array_options"] != []:
                if user["array_options"]["options_nserie"] == self.actual_n_serie:
                    member = common.process_member(user)
                    break
        if member is not None:
            if member not in self.list_add:
                self.list_add.append(member)
                member = common.update_member(member, self.formation, self.actual_n_serie)
                member = common.process_formations(member)
            return render_template('formations.html', list_add=self.list_add, job=self.job, student=member,
                                   success=True, fabmanager=self.fabmanager, formation=self.formation)
        if member is None:
            return render_template('formations.html', error="Votre carte n'est pas relié avec un adhérent",
                                   job=self.job, fabmanager=self.fabmanager, formation=self.formation)

    def new_link(self):
        """
        Récupère le nom et le prénom transmis via le formulaire et vérifie s'il est adhérent dans dolibarr

        :return: formation.html avec la liste des personnes formées, la formation en cours, le fabmanager et un bouton permettant de confirmer le lien en scannant la carte d'un administrateur.
        :return: formation.html avec la liste des personnes formées, la formation en cours, le fabmanager et un message d'erreur si le nom et le prénom ne sont pas valides.
        """
        lastname = request.form['lastname']
        lastname = unidecode.unidecode(lastname)
        firstname = request.form['firstname']
        firstname = unidecode.unidecode(firstname)
        found = None
        try:
            r = requests.get(config.url + config.url_member, headers=config.headers)
        except requests.ConnectionError:
            return render_template(template_name_or_list='formations.html', error='Connectez le PC à internet')
        self.data = json.loads(r.text)
        for member in self.data:
            if unidecode.unidecode(member["firstname"]).lower() == firstname.lower() and unidecode.unidecode(
                    member["lastname"]).lower() == lastname.lower():
                found = common.process_member(member)
                break
        if found is None:
            return render_template(template_name_or_list='formations.html', status='Non adhérent', job=self.job,
                                   fabmanager=self.fabmanager, formation=self.formation, unknow=True,
                                   list_add=self.list_add)
        elif found["array_options"]["options_nserie"] is None or found["array_options"]["options_nserie"] == "":
            self.actual_member = found
            return render_template(template_name_or_list='formations.html', status='Adhérent non lié', job=self.job,
                                   fabmanager=self.fabmanager, formation=self.formation, to_link=True,
                                   lastname=self.actual_member["lastname"], firstname=self.actual_member["firstname"],
                                   list_add=self.list_add, student=self.actual_member)

        return render_template('formations.html', error=True, job=self.job, fabmanager=self.fabmanager,
                               formation=self.formation, list_add=self.list_add)

    def confirm_link(self):
        """
        Permet de confirmer la liaison d'une carte RFID à un adhérent à partir de son nom et prénom, le bouton de
        confirmation n'est accessible que si l'adhérent a été trouvé par la fonction new_link mais qu'il n'est pas
        lié à une carte RFID. Un membre du conseil d'administration est nécessaire pour confirmer la liaison.

        :return: formation.html, la liste des personnes formées, la formation en cours et le fabmanager avec le message d'erreur "Adhérent non lié" si l'administrateur n'est pas trouvé
        :return: formation.html avec "Adhérent lié", la liste des personnes formées, la formation en cours et le fabmanager si la liaison a été effectuée, la fiche de l'adhérent est mise à jour avec la formation qu'il vient d'aquérir
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
        # put modifications
        if not lock:
            self.list_add.append(self.actual_member)
            self.actual_member = common.update_member(self.actual_member, self.formation, self.actual_n_serie)
            self.actual_member = common.process_formations(self.actual_member)
            return render_template(template_name_or_list='formations.html', status='Adhérent lié', new=True,
                                   success=True, student=self.actual_member, job=self.job, fabmanager=self.fabmanager,
                                   formation=self.formation, linked=True, list_add=self.list_add)
        else:
            return render_template(template_name_or_list='formations.html', status='Adhérent non lié', new=True,
                                   student=self.actual_member, not_linked=True, job=self.job,
                                   fabmanager=self.fabmanager, formation=self.formation, list_add=self.list_add)
