import json
import threading
import time

import requests
from flask import Blueprint, render_template, request

import barcode
import common
import config
import fournisseurs

products = {}


def arrival_end():
    """

    :return:
    """
    barcode.running_virtual_keyboard = False
    return render_template('stock.html')


class Stock:
    def __init__(self):
        self.bp = Blueprint('fournisseur', __name__, url_prefix='/stock')
        self.bp.route('/recherche', methods=['POST', 'GET'])(self.search)
        self.bp.route('/recherche/rupture', methods=['POST'])(self.search_breakage)
        self.bp.route('/recherche/achat', methods=['POST'])(self.search_buy)
        self.bp.route('/recherche/add', methods=['POST'])(self.search_add)

        self.bp.route('/arrivage', methods=['GET'])(self.arrival)
        self.bp.route('/arrivage/fournisseur', methods=['POST'])(self.arrival_supplier)
        self.bp.route('/arrivage/add', methods=['POST', 'GET'])(self.arrival_add)
        self.bp.route('/arrivage/remove', methods=['POST', 'GET'])(self.arrival_remove)
        self.bp.route('/arrivage/confirm', methods=['GET'])(self.arrival_confirm)
        self.bp.route('/arrivage/end', methods=['GET'])(arrival_end)

        self.url_rs = "https://fr.rs-online.com/web/search/searchBrowseAction.html?method=searchProducts&searchTerm="
        self.url_otelo = "https://www.otelo.fr/is-bin/INTERSHOP.enfinity/WFS/Otelo-France-Site/fr_FR/-/EUR/Navigation" \
                         "-Dispatch?Ntk=Default_OTFR&Ntt="
        self.url_makershop = "https://www.makershop.fr/recherche?search_query="
        self.suppliers = fournisseurs.Fournisseurs()
        self.supplier = None
        self.fabmanager = None
        self.job = ""
        self.list_add = {}
        self.actual_n_serie = ""
        self.warehouse = None
        self.search_reference = ""
        self.search_component = None
        self.component_eirlab = None

    def search(self):
        search_component = {}
        component_eirlab = None
        if request.method == 'POST':
            if request.form['ref'] != "" and request.form['name'] == "":
                self.search_reference = request.form['ref']
                component_eirlab, search_component, item = self.suppliers.find(self.search_reference)
            elif request.form['name'] != "" and request.form['ref'] == "":
                self.search_reference = request.form['name']
                search_component = self.suppliers.find_dolibarr_name(self.search_reference)
            else:
                return render_template('stock.html', unknow_composant=True, error="Remplissez nom ou référence")
        elif request.method == 'GET':
            self.search_reference = self.suppliers.barcode.read_barcode()
            component_eirlab, search_component, item = self.suppliers.find(self.search_reference)
            self.suppliers.barcode.close()
        self.search_component = search_component
        self.component_eirlab = component_eirlab

        warehouses = requests.get(config.url + config.url_warehouse, headers=config.headers).text
        warehouses = json.loads(warehouses)
        if search_component == {}:
            return render_template('stock.html', unknow_composant=True)
        else:
            return render_template('stock.html', recherche_composant=search_component, recherche=True,
                                   composant_eirlab=component_eirlab, warehouses=warehouses)

    def search_breakage(self):
        fournisseur = request.form['rupture_fournisseur']
        identity = request.form['rupture_identity']
        description = request.form['rupture_description']
        qte = request.form['rupture_qte']

        # Add stockmovement
        identifier = self.search_component[fournisseur]["dolibarr"]["id"]
        warehouse = self.search_component[fournisseur]["warehouse"]
        quantity = self.search_component[fournisseur]["dolibarr"]["stock_reel"]
        stockmovement = {"product_id": identifier, "warehouse_id": warehouse["id"], "qty": -int(quantity)}
        requests.post(config.url + "stockmovements", json=stockmovement, headers=config.headers)

        # Update notes with identity and description
        #     'array_options': {
        #       'options_command': 'Test'
        #     },
        content = {"status": "pending", "identity": identity, "description": description, "quantity": qte}
        product = {"array_options": {"options_command": json.dumps(content)}}
        requests.put(config.url + "products/" + str(identifier), json=product, headers=config.headers)

        return render_template('stock.html', recherche_composant=self.search_component, recherche=True,
                               composant_eirlab=self.component_eirlab)

    def search_buy(self):
        return render_template('stock.html', recherche_composant=self.search_component, recherche=True,
                               composant_eirlab=self.component_eirlab)

    def search_add(self):
        self.list_add = {}

        self.supplier = request.form['add_fournisseur']
        self.warehouse = request.form['warehouse']
        self.warehouse = self.warehouse.split('-')[2]
        lock, member, user, status = common.unlock("ConseilAdministration", self.suppliers.rfid, request.remote_addr)

        if not lock:
            ref = ""
            quantite = ""
            if request.method == 'POST':
                try:
                    quantite = request.form['add_qte']  # get current quantity of this reference
                except KeyError:
                    pass
                ref = self.search_reference  # get current ref with form
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
            return self.arrival_confirm()

    def arrival(self):
        self.supplier = None
        self.fabmanager = None
        self.job = ""
        self.list_add = {}

        lock, member, user, status = common.unlock("ConseilAdministration", self.suppliers.rfid, request.remote_addr)

        if not lock:
            with open('/opt/wolf/fournisseurs.json', 'r') as f:
                data = json.load(f)
                warehouses = requests.get(config.url + config.url_warehouse, headers=config.headers).text
                warehouses = json.loads(warehouses)
                return render_template('stock.html', arrivage=True, fournisseurs=data, warehouses=warehouses)
        else:
            return render_template('stock.html', arrivage_error="Vous n'êtes pas autorisé à accéder à cette page")

    def arrival_supplier(self):
        self.supplier = request.form['fournisseur']
        self.warehouse = request.form['warehouse']
        self.warehouse = self.warehouse.split('-')[2]
        barcode.running_virtual_keyboard = True
        time.sleep(0.5)
        threading.Thread(target=barcode.read_virtual_barcode).start()
        with open('/opt/wolf/fournisseurs.json', 'r') as f:
            data = json.load(f)
            return render_template('stock.html', fournisseur=data[self.supplier], arrivage_recherche=True)

    def arrival_add(self):
        quantite = ""
        ref = ""
        if request.method == 'POST':
            try:
                quantite = request.form['arrivage_qte']  # get current quantity of this reference
            except KeyError:
                pass
            ref = request.form['arrivage_ref']  # get current ref with form
        if quantite == "":
            quantite = "0"
        try:
            if self.list_add[ref] != {}:
                quantite = int(self.list_add[ref]['quantite']) + int(quantite)
                if quantite < 0:
                    try:
                        del self.list_add[ref]
                    except KeyError:
                        pass
                else:
                    self.list_add[ref]['quantite'] = quantite
        except KeyError:
            if int(quantite) < 0:
                with open('/opt/wolf/fournisseurs.json', 'r') as f:
                    data = json.load(f)
                    return render_template('stock.html', fournisseur=data[self.supplier],
                                           arrivage_composants=self.list_add, arrivage_error="Quantité invalide",
                                           arrivage_recherche=True)
            self.list_add[ref] = {"ref": ref, "quantite": quantite}
        with open('/opt/wolf/fournisseurs.json', 'r') as f:
            data = json.load(f)
            return render_template('stock.html', fournisseur=data[self.supplier], arrivage_composants=self.list_add,
                                   arrivage_recherche=True)

    def arrival_remove(self):
        if request.method == 'POST':
            ref = request.form['composant']
            if ref is not None:
                del self.list_add[ref]
        with open('/opt/wolf/fournisseurs.json', 'r') as f:
            data = json.load(f)
            return render_template('stock.html', fournisseur=data[self.supplier], arrivage_composants=self.list_add,
                                   arrivage_recherche=True)

    def thread_search(self, ref):
        global products
        try:
            products[ref]["product"] = getattr(self.suppliers, self.supplier)(ref)[self.supplier]
        except TypeError:
            pass

    def arrival_confirm(self):
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
                    status, item, warehouse = self.suppliers.find_dolibarr(ref)
                    try:
                        packaging = int(products[composant]["product"]["packaging"])
                    except ValueError:
                        packaging = 1
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

                    identifier = 0
                    if item is not None:
                        identifier = item['id']

                    if status:
                        # the product already exist in dolibarr, just update dolibarr with stockmovement
                        stockmovement = {"product_id": identifier, "warehouse_id": str(self.warehouse), "qty": qty,
                                         "price": price}
                        if common.PUB:
                            requests.post(config.url + "stockmovements", json=stockmovement, headers=config.headers)
                            products_add[composant] = products[composant]
                    else:
                        # the product doesn't exist in dolibarr, create it and update dolibarr with stockmovement
                        content = {'label': str(products[composant]["product"]["title"]),
                                   'description': str(products[composant]["product"]["attributes"]), 'other': None,
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
                                   'accountancy_code_sell_export': '', 'accountancy_code_buy_intra': str(self.supplier),
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
                                identifier = status.json()
                                stockmovement = {"product_id": identifier, "warehouse_id": str(self.warehouse),
                                                 "qty": qty, "price": price}
                                requests.post(config.url + "stockmovements", json=stockmovement, headers=config.headers)
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
