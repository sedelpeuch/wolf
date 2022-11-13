import collections
import datetime
import json
import os
import time

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

        self.bp.route('/list_formations', methods=['GET'])(self.list_formations)
        self.bp.route('/remove/<event_id>/<user_id>', methods=['GET'])(self.remove_user)
        self.bp.route('/add/<event_id>', methods=['POST'])(self.add_user)
        self.bp.route('/end/<event_id>', methods=['GET'])(self.end_formation)
        self.bp.route('/owner/<event_id>/<user_id>', methods=['GET'])(self.owner_formation)

        self.formation = None
        self.fabmanager = None
        self.job = ""
        self.list_add = []
        self.actual_n_serie = ""

    def start(self):
        """
        Débute le processus d'ajout de formations aux adhérents. Initialise le lecteur RFID et attend qu'une carte
        soit posée. Lorsqu'elle est posée la fonciton vérifie qu'il fait bien parti du groupe "Fabmanager" sur dolibarr

        :return: formation.html avec les informations du fabmanager et la liste des formations qu'il peut donner si 
        la carte est celle d'un fabmanager
        :return: formation.html avec un message d'erreur sinon
        """
        self.formation = None
        self.fabmanager = None
        self.job = ""
        self.list_add = []
        self.actual_n_serie = ""

        lock, member, user, status = common.unlock("Fabmanagers", self.rfid, request.remote_addr)

        if not lock:
            self.job = user["job"]
            self.fabmanager = member
            return render_template('formations.html', member=member, job=self.job, err=status)
        else:
            return render_template('formations.html', error="Vous n'êtes pas autorisé à accéder à cette page", err=status)

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

        :return: formation.html avec la liste des adhérents ajoutés à la formation et la fiche de la dernière 
        personne ajoutée
        :return: formation.html avec la liste des adhérents ajoutés à la formation et un formulaire pour remplir un 
        nom et prénom si la carte n'a pas été reconnue
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

        :return: formation.html avec la liste des personnes formées, la formation en cours, le fabmanager et un 
        bouton permettant de confirmer le lien en scannant la carte d'un administrateur.
        :return: formation.html avec la liste des personnes formées, la formation en cours, le fabmanager et un 
        message d'erreur si le nom et le prénom ne sont pas valides.
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

        :return: formation.html, la liste des personnes formées, la formation en cours et le fabmanager avec le 
        message d'erreur "Adhérent non lié" si l'administrateur n'est pas trouvé
        :return: formation.html avec "Adhérent lié", la liste des personnes formées, la formation en cours et le 
        fabmanager si la liaison a été effectuée, la fiche de l'adhérent est mise à jour avec la formation qu'il 
        vient d'aquérir
        """
        lock, member, user, status = common.unlock("ConseilAdministration", self.rfid, request.remote_addr)
        self.job = user["job"]

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
                                   fabmanager=self.fabmanager, formation=self.formation, list_add=self.list_add,
                                   err=status)

    def list_formations(self, to_unlock=True):

        """
        Récupère la liste des formations disponibles dans dolibarr et les affiche dans un menu déroulant

        :return: formation.html avec la liste des formations disponibles
        """
        if to_unlock:
            lock, member, user, status = common.unlock("Fabmanagers", self.rfid, request.remote_addr)
        else:
            lock = False
        if not lock:
            agenda = requests.get(config.url + config.url_agenda, headers=config.headers)
            agenda = json.loads(agenda.text)
            agenda = [event for event in agenda if event["type_code"] == "FORMA"]
            agenda = [event for event in agenda if
                      int(event["percentage"]) < 100 or event["datep"] >= time.time() - 86400 * 7]

            users = requests.get(config.url + config.url_user, headers=config.headers)
            users = json.loads(users.text)
            agenda = sorted(agenda, key=lambda k: k['datep'])
            for event in agenda:
                event["user_information"] = {}
                duration = event["datef"] - event["datep"]
                duration = str(datetime.timedelta(seconds=duration))
                event["ended"] = False if int(event["percentage"]) < 100 else True
                event['datef'] = duration[:-3]
                event["datep"] = datetime.datetime.fromtimestamp(int(event["datep"])).strftime('%d/%m/%Y %H:%M')
                for user_assigned in event["userassigned"]:
                    for user in users:
                        if user_assigned == user["id"]:
                            event["user_information"][str(user_assigned)] = user
                            # check if user["id"].jpg in /static/img/users
                            if os.path.isfile("/opt/wolf/static/img/users/" + str(user["id"]) + ".jpg"):
                                event["user_information"][str(user_assigned)]["image"] = "/static/img/users/" + user[
                                    "id"] + ".jpg"
                            else:
                                event["user_information"][str(user_assigned)][
                                    "image"] = "/static/img/users/user_anonymous.png"
                            break
                # sort user_information by lastname
                event["user_information"] = collections.OrderedDict(
                        sorted(event["user_information"].items(), key=lambda t: t[1]["lastname"]))

                # put the event["user_information"] user with the same id as the event["userownerid"] first
                if str(event["userownerid"]) in event["user_information"]:
                    event["user_information"] = collections.OrderedDict(
                            [(str(event["userownerid"]), event["user_information"][str(event["userownerid"])])] +
                            sorted(event["user_information"].items(), key=lambda t: t[0] != str(event["userownerid"])))

                event['formation'] = {}
                if event["note_private"] != '':
                    with open('/opt/wolf/formations.json') as data_file:
                        data = json.load(data_file)
                        try:
                            event['formation'] = data[event["note_private"]]
                        except KeyError:
                            pass

                list_addable = {}
                for user in users:
                    if user["id"] not in event["user_information"] and user['statut'] == '1':
                        list_addable[user["id"]] = user
                # sort list_addable by lastname
                list_addable = collections.OrderedDict(sorted(list_addable.items(), key=lambda t: t[1]["lastname"]))
                event["list_addable"] = list_addable

            return render_template(template_name_or_list='formations.html', list_formations="", agenda=agenda)
        else:
            return render_template(template_name_or_list='formations.html', list_formations="Vous n'êtes pas autorisé à"
                                                                                            " accéder à cette page")

    def remove_user(self, event_id, user_id):
        """
        Supprime un utilisateur d'une formation

        :param id_user: id de l'utilisateur à supprimer
        :param id_event: id de la formation
        :return: formation.html avec la liste des formations disponibles
        """
        event = requests.get(config.url + "agendaevents/" + event_id, headers=config.headers)
        event = json.loads(event.text)
        if event["userownerid"] == user_id:
            # choose another userownerid
            if len(event["userassigned"]) > 1:
                for user in event["userassigned"]:
                    if user != user_id:
                        event["userownerid"] = user
                        break
        content = {"userownerid" : event["userownerid"]}
        result = requests.put(config.url + "agendaevents/" + event_id, headers=config.headers, json=content)
        event["userassigned"] = [user for user in event["userassigned"] if user != user_id]
        content = {"userassigned": event["userassigned"]}
        result = requests.put(config.url + "agendaevents/" + event_id, headers=config.headers, json=content)
        return self.list_formations(to_unlock=False)

    def add_user(self, event_id):
        """
        Ajoute un utilisateur à une formation

        :param id_user: id de l'utilisateur à ajouter
        :param id_event: id de la formation
        :return: formation.html avec la liste des formations disponibles
        """
        event = requests.get(config.url + "agendaevents/" + event_id, headers=config.headers)
        event = json.loads(event.text)
        id_user = request.form["formateur"].split(":")[0]
        user_content = {"id": id_user, "mandatory": '0', 'answer_status': '0', 'transparency': '0'}
        event["userassigned"][str(id_user)] = user_content
        content = {"userassigned": event["userassigned"]}
        result = requests.put(config.url + "agendaevents/" + event_id, headers=config.headers, json=content)
        return self.list_formations(to_unlock=False)

    def end_formation(self, event_id):
        """
        Termine une formation

        :param id_event: id de la formation
        :return: formation.html avec la liste des formations disponibles
        """
        event = requests.get(config.url + "agendaevents/" + event_id, headers=config.headers)
        event = json.loads(event.text)
        task = requests.get(config.url + "tasks/" + event["elementid"], headers=config.headers)
        for user in event["userassigned"]:
            date = datetime.datetime.fromtimestamp(event["datep"]).strftime('%Y-%m-%d %H:%M:%S')
            spenttime = {'date': date, 'duration': event["datef"] - event["datep"], 'user_id': user}
            result = requests.post(config.url + "tasks/" + event["elementid"] + "/addtimespent", headers=config.headers,
                                   json=spenttime)
        content = {"percentage": 100}
        result = requests.put(config.url + "agendaevents/" + event_id, headers=config.headers, json=content)
        return self.list_formations(to_unlock=False)

    def owner_formation(self, event_id, user_id):
        """
        Retourne la liste des formations dont l'utilisateur est propriétaire

        :param id_user: id de l'utilisateur
        :return: liste des formations dont l'utilisateur est propriétaire
        """
        event = requests.get(config.url + "agendaevents/" + event_id, headers=config.headers)
        event = json.loads(event.text)
        event["userownerid"] = user_id
        content = {"userownerid": event["userownerid"]}
        result = requests.put(config.url + "agendaevents/" + event_id, headers=config.headers, json=content)
        return self.list_formations(to_unlock=False)
