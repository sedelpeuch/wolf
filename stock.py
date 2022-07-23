import json
import threading

import requests
from flask import Blueprint, render_template, request

import common
import config
import fournisseurs

product = {}


class Stock:
    def __init__(self):
        self.bp = Blueprint('fournisseur', __name__, url_prefix='/stock')
        self.bp.route('/recherche', methods=['POST', 'GET'])(self.recherche)

        self.bp.route('/arrivage', methods=['GET'])(self.arrivage)
        self.bp.route('/arrivage/fournisseur', methods=['POST'])(self.arrivage_fournisseur)
        self.bp.route('/arrivage/add', methods=['POST', 'GET'])(self.arrivage_add)
        self.bp.route('/arrivage/remove', methods=['POST', 'GET'])(self.arrivage_remove)
        self.bp.route('/arrivage/confirm', methods=['GET'])(self.arrivage_confirm)

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

    def recherche(self):
        recherche_composant = {}
        composant_eirlab = None
        if request.method == 'POST':
            composant_eirlab, recherche_composant = self.fournisseurs.find(request.form['ref'])
        elif request.method == 'GET':
            ref = self.fournisseurs.barcode.read_barcode()
            composant_eirlab, recherche_composant = self.fournisseurs.find(ref)
            self.fournisseurs.barcode.close()
        if recherche_composant == {}:
            return render_template('stock.html', unknow_composant=True)
        else:
            return render_template('stock.html', recherche_composant=recherche_composant, recherche=True,
                                   composant_eirlab=composant_eirlab)

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
                return render_template('stock.html', arrivage=True, fournisseurs=data)
        else:
            return render_template('stock.html', arrivage_error="Vous n'êtes pas autorisé à accéder à cette page")

    def arrivage_fournisseur(self):
        self.fournisseur = request.form['fournisseur']
        with open('/opt/wolf/fournisseurs.json', 'r') as f:
            data = json.load(f)
            return render_template('stock.html', fournisseur=data[self.fournisseur], arrivage_recherche=True)

    def arrivage_add(self):
        if request.method == 'POST':
            try:
                quantite = request.form['arrivage_qte']
            except KeyError:
                pass
            ref = request.form['arrivage_ref']
        # if request.method == 'GET':
        #     ref = self.barcode.read_multiple()
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
        products[ref]["product"] = getattr(self.fournisseurs, self.fournisseur)(ref)[self.fournisseur]
        # here put on dolibarr

    def arrivage_confirm(self):
        global products
        products = self.list_add
        thread_pool = []
        for composant in self.list_add:
            composant = self.list_add[composant]
            thread_pool.append(
                threading.Thread(target=self.thread_search, args=(composant['ref'],)))
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
                    status, id = self.fournisseurs.find_dolibarr(ref)
                    if status:
                        # update dolibarr with stockmovement
                        price = products[composant]["product"]["price"].replace("€", "").replace(",", ".").replace(" ",
                                                                                                                   "")
                        stockmovement = {"product_id": id, "warehouse_id": 1, "qty": products[composant]["quantite"],
                                         "price": price}
                        if common.PUB:
                            status = requests.post(config.url + "stockmovements", json=stockmovement,
                                                   headers=config.headers)
                            products_add[composant] = products[composant]
                    else:
                        # create dolibarr product and stockmovement
                        content = {
                            'label': products[composant]["product"]["title"],
                            'description': products[composant]["product"]["attributes"],
                            'other': None,
                            'type': '0',
                            'cost_price': float(products[composant]["product"]["price"].replace("€", "").replace(",",
                                                                                                                 ".").replace(
                                " ", "")),
                            'status_buy': '1',
                            'url': str(products[composant]["product"]["links_ref"]),
                            'accountancy_code_buy': str(products[composant]["product"]["ref"]),
                            'barcode': str(products[composant]["product"]["ref"]),
                            'barcode_type': '1',
                            'ref': str(products[composant]["product"]["ref"]),
                            'price': '0.00',
                            'price_ttc': '0.00',
                            'price_min': '0.00000000',
                            'price_min_ttc': '0.00000000',
                            'price_base_type': 'TTC',
                            'multiprices': [],
                            'multiprices_ttc': [],
                            'multiprices_base_type': [],
                            'multiprices_min': [],
                            'multiprices_min_ttc': [],
                            'multiprices_tva_tx': [],
                            'prices_by_qty': [],
                            'prices_by_qty_list': [],
                            'multilangs': [],
                            'default_vat_code': None,
                            'tva_tx': '0.000',
                            'localtax1_tx': '0.000',
                            'localtax2_tx': '0.000',
                            'localtax1_type': '0',
                            'localtax2_type': '0',
                            'lifetime': None,
                            'qc_frequency': None,
                            'stock_reel': '10',
                            'stock_theorique': None,
                            'pmp': '0.00000000',
                            'seuil_stock_alerte': '0',
                            'desiredstock': None,
                            'duration_value': False,
                            'duration_unit': '',
                            'status': '0',
                            'finished': None,
                            'fk_default_bom': None,
                            'status_batch': '0',
                            'batch_mask': '',
                            'customcode': '',
                            'weight': None,
                            'weight_units': '0',
                            'length': None,
                            'length_units': '-3',
                            'width': None,
                            'width_units': '-3',
                            'height': None,
                            'height_units': '-3',
                            'surface': None,
                            'surface_units': '-6',
                            'volume': None,
                            'volume_units': '-9',
                            'net_measure': None,
                            'net_measure_units': None,
                            'accountancy_code_sell': '',
                            'accountancy_code_sell_intra': '',
                            'accountancy_code_sell_export': '',
                            'accountancy_code_buy_intra': '',
                            'accountancy_code_buy_export': '',
                            'date_creation': None,
                            'date_modification': None,
                            'stock_warehouse': [],
                            'fk_default_warehouse': '1',
                            'fk_price_expression': None,
                            'fk_unit': None,
                            'price_autogen': '0',
                            'is_object_used': None,
                            'mandatory_period': '0',
                            'entity': '1',
                            'validateFieldsErrors': [],
                            'import_key': None,
                            'array_options': [],
                            'array_languages': None,
                            'linkedObjectsIds': None,
                            'canvas': '',
                            'ref_ext': None,
                            'country_id': None,
                            'country_code': '',
                            'state_id': None,
                            'region_id': None,
                            'barcode_type_coder': None,
                            'last_main_doc': None,
                            'note_public': None,
                            'note_private': '',
                            'total_ht': None,
                            'total_tva': None,
                            'total_localtax1': None,
                            'total_localtax2': None,
                            'total_ttc': None,
                            'date_validation': None,
                            'specimen': 0,
                            'duration': ''
                        }
                        if common.PUB:
                            status = requests.post(config.url + "products", json=content, headers=config.headers)
                            if status.status_code == 200:
                                id = status.json()
                                stockmovement = {"product_id": id, "warehouse_id": 1,
                                                 "qty": products[composant]["quantite"],
                                                 "price": float(
                                                     products[composant]["product"]["price"].replace("€", "").replace(
                                                         ",", ".").replace(" ", ""))}
                                status = requests.post(config.url + "stockmovements", json=stockmovement,
                                                       headers=config.headers)
                                products_add[composant] = products[composant]
                            else:
                                products[composant]["status"] = "Erreur Dolibarr"
                                products_error[composant] = products[composant]
            except KeyError:
                products[composant]["status"] = "Référence incorrecte"
                products_error[composant] = products[composant]
        print("products_add", products_add)
        print("products_error", products_error)
        return render_template('stock.html', arrivage_confirm=True,
                               products_add=products_add, products_error=products_error)
