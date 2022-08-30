import json
import time
from datetime import timedelta

import requests
from flask import Blueprint, request, render_template

import common
import config
import fournisseurs
import rfid


class Emprunt:
    def __init__(self):
        self.bp = Blueprint('Emprunt', __name__, url_prefix='/emprunt')
        self.bp.route("/materiel", methods=['POST'])(self.materiel)
        self.bp.route("/confirm", methods=['GET'])(self.confirm)
        self.bp.route("/materiel/confirm/<id>", methods=['POST'])(self.materiel_confirm)
        self.bp.route("/identity/confirm", methods=['GET'])(self.identity_confirm)
        self.bp.route("/identity/adherent", methods=['POST'])(self.identity_adherent)
        self.bp.route("/identity/notadherent", methods=['POST'])(self.identity_notadherent)
        self.bp.route("/see/identity", methods=['GET', 'POST'])(self.see_identity)
        self.bp.route("/return/<id>", methods=['POST'])(self.return_product)
        self.bp.route("/see/all", methods=['GET'])(self.see_all)

        self.ref = ""
        self.four = fournisseurs.Fournisseurs()
        self.product = False
        self.identity = False
        self.date = False
        self.quantity = 1
        self.item = None
        self.warehouse = None

        self.list_emprunt = []

        self.rfid = rfid.Serial()
        self.rfid.initialize()

    def materiel(self):
        self.ref = request.form['ref']
        self.name = request.form['name']
        statut = None
        recherche_composant = None
        if self.ref != '' and self.name == '':
            statut, item, warehouse = self.four.find_dolibarr(self.ref)
        elif self.ref == '' and self.name != '':
            recherche_composant = self.four.find_dolibarr_name(self.name)
        else:
            return render_template(template_name_or_list='emprunt.html', status='Veuillez entrer une référence ou un '
                                                                                'nom de composant',
                                   confirmed_identity=self.identity, date=self.date, today=time.strftime("%Y-%m-%d"))

        if statut is None and recherche_composant is None:
            return render_template('emprunt.html', error=True)

        if statut is not None and statut:
            self.fournisseur = item["accountancy_code_buy_intra"]
            self.warehouse = warehouse
            self.item = item
            try:
                product = getattr(self.four, self.fournisseur)(self.ref)[self.fournisseur]
                product["dolibarr"] = self.item
                product["warehouse"] = self.warehouse
                product["eirlab"] = True
                self.product = {self.item["id"]: product}
            except AttributeError:
                return render_template('emprunt.html', product=item, warehouse=warehouse,
                                       recherche_composant=self.product, confirmed_identity=self.identity,
                                       date=self.date, today=time.strftime("%Y-%m-%d"), quantity=self.quantity)
        elif recherche_composant is not None:
            self.product = recherche_composant
            return render_template('emprunt.html', recherche_composant=self.product, confirmed_identity=self.identity,
                                   date=self.date, today=time.strftime("%Y-%m-%d"), quantity=self.quantity)
        else:
            return render_template('emprunt.html', error=True)

    def materiel_confirm(self, id):
        if request.method == 'POST':
            try:
                self.quantity = request.form['quantity']  # get current quantity of this reference
            except KeyError:
                pass
        if self.quantity == "":
            self.quantity = "1"
        if self.product is False:
            return render_template('emprunt.html', status="Oups ! Quelque chose s'est mal passé, veuillez réessayer")
        self.product = self.product[id]
        self.item = self.product["dolibarr"]
        return render_template('emprunt.html', confirmed_product=self.product, confirmed_identity=self.identity,
                               date=self.date, today=time.strftime("%Y-%m-%d"), quantity=self.quantity)

    def identity_adherent(self):
        status = self.rfid.initialize()
        self.date = request.form['date']
        if status is False:
            return render_template(template_name_or_list='emprunt.html', status='Connectez le lecteur RFID et '
                                                                                'réessayez')

        n_serie = self.rfid.read_serie()
        self.actual_n_serie = n_serie
        try:
            r = requests.get(config.url + config.url_member, headers=config.headers)
        except requests.ConnectionError:
            return render_template(template_name_or_list='emprunt.html', status='Connectez le PC à internet',
                                   confirmed_product=self.product, confirmed_identity=self.identity, date=self.date,
                                   today=time.strftime("%Y-%m-%d"), quantity=self.quantity)
        self.data = json.loads(r.text)
        for member in self.data:
            if member["array_options"] is not None and member["array_options"] != []:
                if member["array_options"]["options_nserie"] == n_serie:
                    member = common.process_member(member)
                    self.identity = {"lastname": member['lastname'], "firstname": member['firstname'],
                                     "email": member['email'], "id": member['id']}
                    return render_template(template_name_or_list='emprunt.html', member=member,
                                           confirmed_product=self.product, date=self.date,
                                           today=time.strftime("%Y-%m-%d"), quantity=self.quantity)
        return render_template(template_name_or_list='emprunt.html', status='Adhérent inconnu, demandez à un '
                                                                            'administrateur', new=True,
                               confirmed_product=self.product, date=self.date, today=time.strftime("%Y-%m-%d"),
                               quantity=self.quantity)

    def identity_confirm(self):
        return render_template('emprunt.html', confirmed_product=self.product, confirmed_identity=self.identity,
                               date=self.date, today=time.strftime("%Y-%m-%d"), quantity=self.quantity)

    def confirm(self):
        # create stockmovement to EMP (emprunt) and put object with json in emprunt
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
                groups = json.loads(groups)
                for group in groups:
                    if group["name"] == "ConseilAdministration":
                        lock = False
                        break
                break
        # put modifications
        if not lock:
            stockmovement_to_emp = {"product_id": self.item["id"], "warehouse_id": str(2), "qty": self.quantity}
            stockmovement_from_origin = {"product_id": self.item["id"], "warehouse_id": str(self.warehouse["id"]),
                                         "qty": str(-int(self.quantity))}

            description = json.loads(self.item["description"].replace("'", '"'))
            new_description = {"date": time.strftime("%Y-%m-%d"), "return_date": self.date, "quantity": self.quantity,
                               "identity": self.identity, "origin_warehouse": self.warehouse["id"]}
            statut = False
            if len(description) > 0:
                for element in description:
                    if element["identity"] == self.identity:
                        statut = True
                        element["quantity"] = str(int(element["quantity"]) + int(self.quantity))
                        if element["return_date"] <= self.date:
                            element["return_date"] = self.date
                        break

            if not statut:
                description.append(new_description)

            emprunt = {"description": str(description)}

            if common.PUB:
                status = requests.post(config.url + "stockmovements", json=stockmovement_to_emp, headers=config.headers)

                status = requests.post(config.url + "stockmovements", json=stockmovement_from_origin,
                                       headers=config.headers)

                status = requests.put(config.url + "products/" + str(self.item["id"]), json=emprunt,
                                      headers=config.headers)

                return render_template('emprunt.html', confirmed_product=self.product, confirmed_identity=self.identity,
                                       date=self.date, today=time.strftime("%Y-%m-%d"), emprunt_confirm=True,
                                       quantity=self.quantity)
        else:
            return render_template('emprunt.html', confirmed_product=self.product, confirmed_identity=self.identity,
                                   date=self.date, today=time.strftime("%Y-%m-%d"), emprunt_confirm=True,
                                   quantity=self.quantity, error="Administrateur non reconnu")

    def identity_notadherent(self):
        lastname = request.form['lastname']
        firstname = request.form['firstname']
        email = request.form['email']
        self.date = request.form['date']
        self.identity = {"lastname": lastname, "firstname": firstname, "email": email}
        return render_template('emprunt.html', confirmed_product=self.product, date=self.date,
                               today=time.strftime("%Y-%m-%d"), quantity=self.quantity)

    def see_identity(self):
        self.list_emprunt = []
        # Get the identity of the person
        if request.method == 'POST':
            lastname = request.form['lastname']
            firstname = request.form['firstname']
            email = request.form['email']
            self.identity = {"lastname": lastname, "firstname": firstname, "email": email}
        elif request.method == 'GET':
            status = self.rfid.initialize()
            if status is False:
                return render_template(template_name_or_list='emprunt.html', status='Connectez le lecteur RFID et '
                                                                                    'réessayez')
            n_serie = self.rfid.read_serie()
            self.actual_n_serie = n_serie
            r = requests.get(config.url + config.url_member, headers=config.headers)
            self.data = json.loads(r.text)
            for member in self.data:
                if member["array_options"] is not None and member["array_options"] != []:
                    if member["array_options"]["options_nserie"] == n_serie:
                        member = common.process_member(member)
                        self.identity = {"lastname": member['lastname'], "firstname": member['firstname'],
                                         "email": member['email'], "id": member['id']}

        # get all products in the EMP warehouse (id = 2)
        r = requests.get(config.url + config.url_product, headers=config.headers)
        products = json.loads(r.text)
        for product in products:
            if product["description"] != "" and product["description"] != []:
                try:
                    description = json.loads(product["description"].replace("'", '"'))
                    for element in description:
                        try:
                            if element["id"] == self.identity["id"]:
                                product["emprunt"] = element
                                self.list_emprunt.append(product)
                        except KeyError:
                            if element["identity"]["lastname"] == self.identity["lastname"] and element["identity"][
                                "firstname"] == self.identity["firstname"]:
                                if product not in self.list_emprunt:
                                    product["emprunt"] = element
                                    self.list_emprunt.append(product)
                            if element["identity"]["email"] == self.identity["email"] and element["identity"][
                                "lastname"] == self.identity["lastname"]:
                                if product not in self.list_emprunt:
                                    product["emprunt"] = element
                                    self.list_emprunt.append(product)
                            if element["identity"]["email"] == self.identity["email"] and element["identity"][
                                "firstname"] == self.identity["firstname"]:
                                if product not in self.list_emprunt:
                                    product["emprunt"] = element
                                    self.list_emprunt.append(product)
                except json.decoder.JSONDecodeError:
                    pass
        for element in self.list_emprunt:
            # if more than 30 days
            if time.strftime("%Y-%m-%d") > element["emprunt"]["return_date"] + str(timedelta(days=30)):
                element["status"] = 'danger'
            elif time.strftime("%Y-%m-%d") > element["emprunt"]["return_date"]:
                element["status"] = 'warning'
            else:
                element["status"] = 'success'
        if len(self.list_emprunt) == 0:
            return render_template('emprunt.html', no_emprunt=True, identity=self.identity)
        return render_template('emprunt.html', identity=self.identity, list_emprunt=self.list_emprunt)

    def return_product(self, id):
        list_all = False
        if not self.identity:
            list_all = True
            self.identity = {"lastname": request.form['lastname'], "firstname": request.form['firstname'],
                             "email": request.form['email'], }
        for element in range(len(self.list_emprunt)):
            if self.list_emprunt[element]["id"] == id:
                stockmovement_from_emp = {"product_id": self.list_emprunt[element]["id"], "warehouse_id": 2,
                                          "qty": str(-int(self.list_emprunt[element]["emprunt"]["quantity"]))}
                stockmovement_from_origin = {"product_id": self.list_emprunt[element]["id"],
                                             "warehouse_id": self.list_emprunt[element]["emprunt"]["origin_warehouse"],
                                             "qty": str(int(self.list_emprunt[element]["emprunt"]["quantity"]))}
                description = json.loads(self.list_emprunt[element]["description"].replace("'", '"'))

                for elt in description:
                    if elt["identity"]["lastname"] == self.identity["lastname"] and elt["identity"]["firstname"] == \
                            self.identity["firstname"]:
                        description.remove(elt)
                    elif elt["identity"]["email"] == self.identity["email"] and elt["identity"]["lastname"] == \
                            self.identity["lastname"]:
                        description.remove(elt)
                    elif elt["identity"]["email"] == self.identity["email"] and elt["identity"]["firstname"] == \
                            self.identity["firstname"]:
                        description.remove(elt)
                emprunt = {"description": str(description)}
                if common.PUB:
                    status = requests.post(config.url + "stockmovements", json=stockmovement_from_emp,
                                           headers=config.headers)
                    status = requests.post(config.url + "stockmovements", json=stockmovement_from_origin,
                                           headers=config.headers)
                    status = requests.put(config.url + "products/" + str(id), json=emprunt, headers=config.headers)
                self.list_emprunt[element]["returned"] = True
        if list_all:
            return render_template('emprunt.html', list_complete=self.list_emprunt)
        return render_template('emprunt.html', identity=self.identity, list_emprunt=self.list_emprunt)

    def see_all(self):
        # create stockmovement to EMP (emprunt) and put object with json in emprunt
        self.identity = False
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
                groups = json.loads(groups)
                for group in groups:
                    if group["name"] == "ConseilAdministration":
                        lock = False
                        break
                break
        # put modifications
        if not lock:
            products = requests.get(config.url + config.url_product, headers=config.headers)
            products = json.loads(products.text)
            self.list_emprunt = []
            for product in products:
                if product["description"] != "" and product["description"] != []:
                    try:
                        description = json.loads(product["description"].replace("'", '"'))
                        for element in description:
                            product["emprunt"] = element
                            self.list_emprunt.append(product)
                    except json.decoder.JSONDecodeError:
                        pass
            for elt in self.list_emprunt:
                if time.strftime("%Y-%m-%d") > elt["emprunt"]["return_date"] + str(timedelta(days=30)):
                    elt["status"] = 'danger'
                elif time.strftime("%Y-%m-%d") > elt["emprunt"]["return_date"]:
                    elt["status"] = 'warning'
                else:
                    elt["status"] = 'success'
            if len(self.list_emprunt) == 0:
                return render_template('emprunt.html', no_emprunt_all=True)
            return render_template('emprunt.html', list_complete=self.list_emprunt)
