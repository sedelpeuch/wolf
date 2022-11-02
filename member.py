import csv
import datetime
import json
import time

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
        self.bp.route('/helloasso', methods=['POST'])(self.add_helloasso)

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

        members = requests.get(config.url + config.url_member, headers=config.headers).text
        members = json.loads(members)
        lock = True

        for member in members:
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
        self.rfid.initialize()
        n_serie = self.rfid.read_serie()

        users = requests.get(config.url + config.url_user, headers=config.headers).text
        users = json.loads(users)

        members = requests.get(config.url + config.url_member, headers=config.headers).text
        members = json.loads(members)
        lock = True

        for member in members:
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
                for group in groups:
                    if group["name"] == "ConseilAdministration":
                        lock = False
                        break
                break

        if not lock:
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
                return render_template(template_name_or_list='index.html', status_list="Liste des adhérents",
                                       list_member=result_search)

            # sort self.data by firstname
            self.data = sorted(self.data, key=lambda k: k['lastname'])
            return render_template(template_name_or_list='index.html', status_list="Liste des adhérents",
                                   list_member=self.data)

    def add_helloasso(self):

        self.rfid.initialize()
        n_serie = self.rfid.read_serie()

        users = requests.get(config.url + config.url_user, headers=config.headers).text
        users = json.loads(users)

        members = requests.get(config.url + config.url_member, headers=config.headers).text
        members = json.loads(members)
        lock = True

        for member in members:
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
                for group in groups:
                    if group["name"] == "ConseilAdministration":
                        lock = False
                        break
                break

        if not lock:
            if request.files['file'] != "":
                f = request.files['file']
                # save in static/helloasso with name helloasso.csv
                f.save("helloasso.csv")

                member_renew = []
                member_new = []

                with open('helloasso.csv', 'r') as csv_file:
                    input = csv.reader(csv_file, delimiter=';')
                    adherents = []
                    header = next(input)
                    expected_header = ['Date', 'Email acheteur', 'Nom', 'Prénom', 'Status', 'Tarif', 'Montant (€)',
                                       'Code Promo', "Url carte d'adhérent",
                                       'Champ complémentaire 1\nNuméro de téléphone', 'Champ complémentaire 2\nEmail',
                                       'Champ complémentaire 3\nAdresse', 'Champ complémentaire 4\nCode Postal',
                                       'Champ complémentaire 5\nVille',
                                       'Champ complémentaire 6\nJustificatif de tarif réduit (carte étudiant avec '
                                       'année, certificat de scolarité, etc)']
                    if header != expected_header:
                        return render_template(template_name_or_list='index.html', status_file='Fichier invalide')
                    for row in input:
                        adherent = Adherent()
                        adherent.fill_basic(row)
                        adherent.fill_fk_adherent_type(row)
                        adherent.fill_date(row)
                        adherents.append(adherent)
                    with open('helloasso_after.csv', 'w') as csv_file:
                        output = csv.writer(csv_file, delimiter=';')
                        output.writerow(["Réf adhérent* (a.ref)", "Titre civilité (a.civility)", "Nom* (a.lastname)",
                                         "Prénom (a.firstname)", "Genre (a.gender)", "Identifiant* (a.login)",
                                         "Mot de passe (a.pass)", "Id type adhérent* (a.fk_adherent_type)",
                                         "Nature de l'adhérent* (a.morphy)", "Société (a.societe)",
                                         "Adresse (a.address)", "Code postal (a.zip)", "Ville (a.town)",
                                         "StateId|StateCode (a.state_id)", "CountryId|CountryCode (a.country)",
                                         "Tél pro. (a.phone)", "Tél perso. (a.phone_perso)",
                                         "Tél portable (a.phone_mobile)", "Email (a.email)", "Birthday (a.birth)",
                                         "État* (a.statut)", "Photo (a.photo)", "Note (publique) (a.note_public)",
                                         "Note (privée) (a.note_private)", "Date création (a.datec)",
                                         "Date fin adhésion (a.datefin)", "Tiers (a.fk_soc)", "N° Série (extra.nserie)",
                                         "Formations (extra.impression3d)"])
                        # adherents = delete_double(adherents)
                        for adherent in adherents:
                            try:
                                write = True
                                for member in members:
                                    try:
                                        login = member["login"].lower()
                                    except AttributeError:
                                        login = ""
                                    if login == adherent.login.lower():
                                        write = False
                                        # transform 2022-10-04 to timestamp
                                        adherent.datec = time.mktime(
                                                datetime.datetime.strptime(adherent.datec, "%Y-%m-%d").timetuple())
                                        adherent.datefin = time.mktime(
                                                datetime.datetime.strptime(adherent.datefin, "%Y-%m-%d").timetuple())
                                        subscription = {'start_date': adherent.datec, 'end_date': adherent.datefin,
                                                        'amount': 0 if adherent.fk_adherent_type == 1 else 50 if
                                                        adherent.fk_adherent_type == 2 else 100}
                                        # requests.post(config.url + "members/" + member['id'] + "/subscriptions",
                                        #         headers=config.headers, json=subscription)
                                        member_renew.append(adherent)
                                if write:
                                    member_new.append(adherent)
                                    member = {'login': adherent.login, 'address': adherent.address, 'zip': adherent.zip,
                                              'town': adherent.town, 'email': adherent.email,
                                              'phone_perso': adherent.phone, 'morphy': 'phy', 'public': '0',
                                              'datec': time.mktime(datetime.datetime.strptime(adherent.datec,
                                                                                              "%Y-%m-%d").timetuple()),
                                              'datem': time.mktime(datetime.datetime.strptime(adherent.datefin,
                                                                                              "%Y-%m-%d").timetuple()),
                                              'typeid': str(adherent.fk_adherent_type),
                                              'type': 'Plein tarif' if adherent.fk_adherent_type == 3 else 'Plein '
                                                                                                           'tarif ('
                                                                                                           'sur '
                                                                                                           'facture)'
                                              if adherent.fk_adherent_type == 4 else "Etudiants en dehors de Bordeaux"
                                                                                                                                                             " INP et demandeurs d'emploi" if adherent.fk_adherent_type == 2 else "Etudiant ou personnel de Bordeaux "
                                                                                                                                                                                                                                  "INP",
                                              'need_subscription': '1', 'datefin': time.mktime(
                                                datetime.datetime.strptime(adherent.datefin, "%Y-%m-%d").timetuple()),
                                              'entity': '1', 'country_id': '1', 'country_code': 'FR',
                                              'lastname': adherent.lastname, 'firstname': adherent.firstname,
                                              'statut': '1', 'status': '1', }
                                    result = requests.post(config.url + "members", headers=config.headers, json=member)
                                    adherent.write_csv(output)
                            except AttributeError:
                                pass
        return render_template(template_name_or_list='index.html', member_renew=member_renew, member_new=member_new,
                               status_file='Fichier valide')


class Adherent:
    def __init__(self):
        self.ref = "auto"  # auto-generated
        self.lastname = ""  #
        self.firstname = ""  #
        self.login = ""  #
        self.fk_adherent_type = 1  #
        self.morphy = "phy"  #
        self.phone = ""  #
        self.address = ""  #
        self.zip = ""  #
        self.town = ""  #
        self.country = "FR"  #
        self.email = "sebastien40200.delpeuch@gmail.com"  #
        self.statut = 1  #
        self.datec = ""  #
        self.datefin = ""  #
        self.to_delete = False  #

    def fill_basic(self, row):
        self.lastname = row[2]
        self.firstname = row[3]
        self.login = self.firstname[0].lower() + self.lastname.lower()
        self.phone = row[9]
        self.email = row[10]
        self.address = row[11]
        self.zip = row[12]
        self.town = row[13]

    def fill_fk_adherent_type(self, row):
        if row[5] == "Etudiant ou personnel de Bordeaux INP":
            self.fk_adherent_type = 1
        elif row[5] == "Etudiants en dehors de Bordeaux INP et demandeurs d'emploi":
            self.fk_adherent_type = 2
        elif row[5] == "Plein tarif":
            self.fk_adherent_type = 3
        elif row[5] == "Plein tarif (sur facture)":
            self.fk_adherent_type = 4

    def fill_date(self, row):
        # datec is the date of row[0] without hour and replace '/' by '-' and reverse the order
        datec = row[0].split(' ')[0].replace('/', '-').split('-')[::-1]
        self.datec = '-'.join(datec)
        datec[0] = str(int(datec[0]) + 1)
        self.datefin = '-'.join(datec)

    def write_csv(self, csv_file):
        csv_file.writerow(
                [self.ref, "", self.lastname, self.firstname, "", self.login, "", self.fk_adherent_type, self.morphy,
                 "", self.address, self.zip, self.town, "", self.country, "", self.phone, "", self.email, "",
                 self.statut, "", "", "", self.datec, self.datefin, "", ""])
