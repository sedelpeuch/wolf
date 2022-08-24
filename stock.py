import json
import threading
import time

import requests
from flask import Blueprint, render_template, request

import barcode
import common
import config
import fournisseurs

product = {}


class Stock:
    def __init__(self):
        self.bp = Blueprint('fournisseur', __name__, url_prefix='/stock')
        self.bp.route('/recherche', methods=['POST', 'GET'])(self.recherche)
        self.bp.route('/recherche/rupture', methods=['POST'])(self.recherche_rupture)
        self.bp.route('/recherche/achat', methods=['POST'])(self.recherche_achat)
        self.bp.route('/recherche/add', methods=['POST'])(self.recherche_add)

        self.bp.route('/arrivage', methods=['GET'])(self.arrivage)
        self.bp.route('/arrivage/fournisseur', methods=['POST'])(self.arrivage_fournisseur)
        self.bp.route('/arrivage/add', methods=['POST', 'GET'])(self.arrivage_add)
        self.bp.route('/arrivage/remove', methods=['POST', 'GET'])(self.arrivage_remove)
        self.bp.route('/arrivage/confirm', methods=['GET'])(self.arrivage_confirm)
        self.bp.route('/arrivage/end', methods=['GET'])(self.arrivage_end)

        self.url_rs = "http://fr.rs-online.com/web/search/searchBrowseAction.html?method=searchProducts&searchTerm="
        self.url_otelo = "https://www.otelo.fr/is-bin/INTERSHOP.enfinity/WFS/Otelo-France-Site/fr_FR/-/EUR/Navigation" \
                         "-Dispatch?Ntk=Default_OTFR&Ntt="
        self.url_makershop = "https://www.makershop.fr/recherche?search_query="
        self.fournisseurs = fournisseurs.Fournisseurs()
        self.fournisseur = None
        self.fabmanager = None
        self.job = ""
        self.list_add = {}
        self.actual_n_serie = ""
        self.warehouse = None
        self.recherche_reference = ""

    def recherche(self):
        recherche_composant = {}
        composant_eirlab = None
        item = None
        if request.method == 'POST':
            self.recherche_reference = request.form['ref']
            composant_eirlab, recherche_composant, item = self.fournisseurs.find(self.recherche_reference)
        elif request.method == 'GET':
            self.recherche_reference = self.fournisseurs.barcode.read_barcode()
            composant_eirlab, recherche_composant, item = self.fournisseurs.find(self.recherche_reference)
            self.fournisseurs.barcode.close()
        self.recherche_composant = recherche_composant
        self.composant_eirlab = composant_eirlab

        warehouses = requests.get(config.url + config.url_warehouse, headers=config.headers).text
        warehouses = json.loads(warehouses)

        if recherche_composant == {}:
            return render_template('stock.html', unknow_composant=True)
        else:
            return render_template('stock.html', recherche_composant=recherche_composant, recherche=True,
                                   composant_eirlab=composant_eirlab, warehouses=warehouses)

    def recherche_rupture(self):
        fournisseur = request.form['rupture_fournisseur']
        identity = request.form['rupture_identity']
        description = request.form['rupture_description']

        # Add stockmovement
        id = self.recherche_composant[fournisseur]["dolibarr"]["id"]
        warehouse = self.recherche_composant[fournisseur]["warehouse"]
        quantite = self.recherche_composant[fournisseur]["dolibarr"]["stock_reel"]
        stockmovement = {"product_id": id, "warehouse_id": warehouse["id"], "qty": -int(quantite)}
        status = requests.post(config.url + "stockmovements", json=stockmovement, headers=config.headers)

        # Update notes with identity and description
        product = {"note_public": description, "note_private": identity}
        status = requests.put(config.url + "products/" + str(id), json=product, headers=config.headers)

        return render_template('stock.html', recherche_composant=self.recherche_composant, recherche=True,
                               composant_eirlab=self.composant_eirlab)

    def recherche_achat(self):
        return render_template('stock.html', recherche_composant=self.recherche_composant, recherche=True,
                               composant_eirlab=self.composant_eirlab)

    def recherche_add(self):
        self.list_add = {}

        status = self.fournisseurs.rfid.initialize()
        if status is False:
            return render_template(template_name_or_list='stock.html',
                                   arrivage_error='Connectez le lecteur RFID et réessayez')
        self.fournisseur = request.form['add_fournisseur']
        self.warehouse = request.form['warehouse']
        self.warehouse = self.warehouse.split('-')[2]
        self.actual_n_serie = self.fournisseurs.rfid.read_serie()

        users = requests.get(config.url + config.url_user, headers=config.headers).text
        users = json.loads(users)

        member = requests.get(config.url + config.url_member, headers=config.headers).text
        member = json.loads(member)
        lock = True
        job = ""
        for member in member:
            if member["array_options"] is not None and member["array_options"] != []:
                if member["array_options"]["options_nserie"] == self.actual_n_serie:
                    member = common.process_member(member)
                    break
        for user in users:
            if user["lastname"] == member["lastname"] and user["firstname"] == member["firstname"]:
                groups = requests.get(
                        config.url + "users/" + user["id"] + "/groups?sortfield=t.rowid&sortorder=ASC&limit=100",
                        headers=config.headers).text
                groups = json.loads(groups)
                for group in groups:
                    if group["name"] == "Fabmanagers":
                        lock = False
                        break
                break
        if not lock:
            quantite = ""
            if request.method == 'POST':
                try:
                    quantite = request.form['add_qte']  # get current quantity of this reference
                except KeyError:
                    pass
                ref = self.recherche_reference  # get current ref with form
            if quantite == "":
                quantite = "1"
            try:
                if self.list_add[ref] != {}:
                    quantite = int(self.list_add[ref]['quantite']) + int(quantite)
                    if quantite <= 0:
                        try:
                            del self.list_add[ref]
                        except KeyError:
                            pass
                    else:
                        self.list_add[ref]['quantite'] = quantite
            except KeyError:
                self.list_add[ref] = {"ref": ref, "quantite": quantite}
            return self.arrivage_confirm()



    def arrivage(self):
        status = self.fournisseurs.rfid.initialize()
        if status is False:
            return render_template(template_name_or_list='stock.html',
                                   arrivage_error='Connectez le lecteur RFID et réessayez')
        self.fournisseur = None
        self.fabmanager = None
        self.job = ""
        self.list_add = {}
        self.actual_n_serie = ""
        self.actual_n_serie = self.fournisseurs.rfid.read_serie()

        users = requests.get(config.url + config.url_user, headers=config.headers).text
        users = json.loads(users)

        member = requests.get(config.url + config.url_member, headers=config.headers).text
        member = json.loads(member)
        lock = True
        job = ""
        for member in member:
            if member["array_options"] is not None and member["array_options"] != []:
                if member["array_options"]["options_nserie"] == self.actual_n_serie:
                    member = common.process_member(member)
                    self.fabmanager = member
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
            with open('/opt/wolf/fournisseurs.json', 'r') as f:
                data = json.load(f)
                warehouses = requests.get(config.url + config.url_warehouse, headers=config.headers).text
                warehouses = json.loads(warehouses)
                return render_template('stock.html', arrivage=True, fournisseurs=data, warehouses=warehouses)
        else:
            return render_template('stock.html', arrivage_error="Vous n'êtes pas autorisé à accéder à cette page")

    def arrivage_fournisseur(self):
        self.fournisseur = request.form['fournisseur']
        self.warehouse = request.form['warehouse']
        self.warehouse = self.warehouse.split('-')[2]
        barcode.running_virtual_keyboard = True
        time.sleep(0.5)
        threading.Thread(target=barcode.read_virtual_barcode).start()
        with open('/opt/wolf/fournisseurs.json', 'r') as f:
            data = json.load(f)
            return render_template('stock.html', fournisseur=data[self.fournisseur], arrivage_recherche=True)

    def arrivage_add(self):
        quantite = ""
        if request.method == 'POST':
            try:
                quantite = request.form['arrivage_qte']  # get current quantity of this reference
            except KeyError:
                pass
            ref = request.form['arrivage_ref']  # get current ref with form
        if quantite == "":
            quantite = "1"
        try:
            if self.list_add[ref] != {}:
                quantite = int(self.list_add[ref]['quantite']) + int(quantite)
                if quantite <= 0:
                    try:
                        del self.list_add[ref]
                    except KeyError:
                        pass
                else:
                    self.list_add[ref]['quantite'] = quantite
        except KeyError:
            if int(quantite) <= 0:
                with open('/opt/wolf/fournisseurs.json', 'r') as f:
                    data = json.load(f)
                    return render_template('stock.html', fournisseur=data[self.fournisseur],
                                           arrivage_composants=self.list_add, arrivage_error="Quantité invalide",
                                           arrivage_recherche=True)
            self.list_add[ref] = {"ref": ref, "quantite": quantite}
        with open('/opt/wolf/fournisseurs.json', 'r') as f:
            data = json.load(f)
            return render_template('stock.html', fournisseur=data[self.fournisseur], arrivage_composants=self.list_add,
                                   arrivage_recherche=True)

    def arrivage_remove(self):
        ref = None
        print("list_add", self.list_add)
        if request.method == 'POST':
            # try:
            ref = request.form['composant']
            # except KeyError:
            #     pass
            if ref is not None:
                del self.list_add[ref]
        with open('/opt/wolf/fournisseurs.json', 'r') as f:
            data = json.load(f)
            print("list_add", self.list_add)
            return render_template('stock.html', fournisseur=data[self.fournisseur], arrivage_composants=self.list_add,
                                   arrivage_recherche=True)

    def thread_search(self, ref):
        global products
        try:
            products[ref]["product"] = getattr(self.fournisseurs, self.fournisseur)(ref)[self.fournisseur]
        except TypeError:
            pass

    def arrivage_confirm(self):
        global products
        barcode.running_virtual_keyboard = False
        products = self.list_add
        thread_pool = []
        for composant in self.list_add:
            composant = self.list_add[composant]
            thread_pool.append(threading.Thread(target=self.thread_search, args=(composant['ref'],)))
        for thread in thread_pool:
            thread.start()
        for thread in thread_pool:
            thread.join()
        products_add = {}
        products_error = {}

        for composant in products:
            try:
                if products[composant]["product"] is not None:
                    ref = products[composant]["product"]["ref"]
                    status, item, warehouse = self.fournisseurs.find_dolibarr(ref)
                    packaging = int(products[composant]["product"]["packaging"])
                    qty = str(int(products[composant]["quantite"]) * packaging)

                    # format price of product
                    try:
                        price = float(
                                products[composant]["product"]["price"].replace("€", "").replace(",", ".").replace(" ",
                                        ""))
                    except ValueError:
                        if type(products[composant]["product"]["price"]) == float:
                            price = products[composant]["product"]["price"]
                        else:
                            price = 0.0
                    except AttributeError:
                        price = products[composant]["product"]["price"]

                    if item is not None:
                        id = item['id']
                        four = item['accountancy_code_buy_intra']

                    if status:
                        # the product already exist in dolibarr, just update dolibarr with stockmovement
                        stockmovement = {"product_id": id, "warehouse_id": str(self.warehouse),
                                         "qty": qty, "price": price}
                        if common.PUB:
                            status = requests.post(config.url + "stockmovements", json=stockmovement,
                                                   headers=config.headers)
                            products_add[composant] = products[composant]
                    else:
                        # the product doesn't exist in dolibarr, create it and update dolibarr with stockmovement
                        content = {'label': products[composant]["product"]["title"],
                                   'description': products[composant]["product"]["attributes"], 'other': None,
                                   'type': '0', 'cost_price': price, 'status_buy': '1',
                                   'url': str(products[composant]["product"]["links_ref"]),
                                   'accountancy_code_buy': str(products[composant]["product"]["ref"]),
                                   'barcode': str(products[composant]["product"]["ref"]), 'barcode_type': '1',
                                   'ref': str(products[composant]["product"]["ref"]), 'price': '0.00',
                                   'price_ttc': '0.00', 'price_min': '0.00000000', 'price_min_ttc': '0.00000000',
                                   'price_base_type': 'TTC', 'multiprices': [], 'multiprices_ttc': [],
                                   'multiprices_base_type': [], 'multiprices_min': [], 'multiprices_min_ttc': [],
                                   'multiprices_tva_tx': [], 'prices_by_qty': [], 'prices_by_qty_list': [],
                                   'multilangs': [], 'default_vat_code': None, 'tva_tx': '0.000',
                                   'localtax1_tx': '0.000', 'localtax2_tx': '0.000', 'localtax1_type': '0',
                                   'localtax2_type': '0', 'lifetime': None, 'qc_frequency': None, 'stock_reel': None,
                                   'stock_theorique': None, 'pmp': '0.00000000', 'seuil_stock_alerte': '0',
                                   'desiredstock': None, 'duration_value': False, 'duration_unit': '', 'status': '0',
                                   'finished': None, 'fk_default_bom': None, 'status_batch': '0', 'batch_mask': '',
                                   'customcode': '', 'weight': None, 'weight_units': '0', 'length': None,
                                   'length_units': '-3', 'width': None, 'width_units': '-3', 'height': None,
                                   'height_units': '-3', 'surface': None, 'surface_units': '-6', 'volume': None,
                                   'volume_units': '-9', 'net_measure': None, 'net_measure_units': None,
                                   'accountancy_code_sell': '', 'accountancy_code_sell_intra': '',
                                   'accountancy_code_sell_export': '', 'accountancy_code_buy_intra': self.fournisseur,
                                   'accountancy_code_buy_export': '', 'date_creation': None, 'date_modification': None,
                                   'stock_warehouse': [], 'fk_default_warehouse': str(self.warehouse),
                                   'fk_price_expression': None, 'fk_unit': None, 'price_autogen': '0',
                                   'is_object_used': None, 'mandatory_period': '0', 'entity': '1',
                                   'validateFieldsErrors': [], 'import_key': None, 'array_options': [],
                                   'array_languages': None, 'linkedObjectsIds': None, 'canvas': '', 'ref_ext': None,
                                   'country_id': None, 'country_code': '', 'state_id': None, 'region_id': None,
                                   'barcode_type_coder': None, 'last_main_doc': None, 'note_public': '',
                                   'note_private': '', 'total_ht': None, 'total_tva': None, 'total_localtax1': None,
                                   'total_localtax2': None, 'total_ttc': None, 'date_validation': None, 'specimen': 0,
                                   'duration': ''}
                        if common.PUB:
                            status = requests.post(config.url + "products", json=content, headers=config.headers)
                            if status.status_code == 200:
                                id = status.json()
                                stockmovement = {"product_id": id, "warehouse_id": str(self.warehouse),
                                                 "qty": qty, "price": price}
                                status = requests.post(config.url + "stockmovements", json=stockmovement,
                                                       headers=config.headers)
                                products_add[composant] = products[composant]
                            else:
                                products[composant]["status"] = "Erreur Dolibarr"
                                products_error[composant] = products[composant]
            except KeyError:
                products[composant]["status"] = "Référence incorrecte"
                products[composant]["product"] = {}
                products[composant]["product"]["title"] = ""
                products[composant]["product"]["price"] = ""
                products[composant]["product"]["image"] = ""
                products[composant]["product"]["links_ref"] = ""
                products[composant]["product"]["links"] = ""
                products[composant]["product"]["packaging"] = ""
                products_error[composant] = products[composant]

        return render_template('stock.html', arrivage_confirm=True, products_add=products_add,
                               products_error=products_error)

    def arrivage_end(self):
        barcode.running_virtual_keyboard = False
        return render_template('stock.html')
