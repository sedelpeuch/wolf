import json

import requests
from flask import Blueprint, render_template, request

import common
import config
import fournisseurs

product_command = {}


class Command:
    def __init__(self):
        self.id_warehouse = None
        self.products = None
        self.bp = Blueprint('command', __name__, url_prefix='/command')
        self.bp.route('/', methods=['GET'])(self.command)
        self.bp.route('/warehouse', methods=['POST'])(self.warehouse)
        self.bp.route('/add/<id_product>', methods=['POST'])(self.add)
        self.bp.route('/remove/<id_product>', methods=['GET'])(self.remove)
        self.bp.route('/generate')(self.generate)
        self.bp.route('/confirm', methods=['POST'])(self.confirm)

        self.suppliers = fournisseurs.Fournisseurs()
        self.warehouses = None

    def command(self):
        self.fabmanager = None
        self.job = ""

        lock, member, user, status = common.unlock("ConseilAdministration", self.suppliers.rfid, request.remote_addr)

        if not lock:
            with open('/opt/wolf/fournisseurs.json', 'r') as f:
                self.warehouses = requests.get(config.url + config.url_warehouse, headers=config.headers).text
                self.warehouses = json.loads(self.warehouses)

                warehouse_command = {}
                for warehouse in self.warehouses:
                    warehouse_command[warehouse['id']] = {'warehouse': warehouse, 'command': 0}
                products = requests.get(config.url + config.url_product, headers=config.headers).text
                products = json.loads(products)
                print(products[154])
                for product in products:
                    if product['array_options']:
                        if product['array_options']['options_command'] is not None:
                            try:
                                array_options = json.loads(product['array_options']['options_command'])
                            except json.decoder.JSONDecodeError:
                                array_options = product['array_options']['options_command'].split(',')
                                array_options[0] = array_options[0][1:]
                                array_options[-1] = array_options[-1][:-1]
                                array_options = [element.split(':') for element in array_options]
                                for elt in array_options:
                                    elt[0] = elt[0].replace("'", "")
                                    elt[0] = elt[0].replace(' ', '')
                                    elt[1] = elt[1].replace(' ', '')
                                    elt[1] = elt[1].replace("'", '"')
                                array_options = {element[0]: element[1] for element in array_options}
                                array_options = {element[0]: element[1].replace("'", '"') for element in
                                                 array_options.items()}
                            if array_options['status'] == "pending":
                                warehouse_command[product['fk_default_warehouse']]['command'] += 1
                return render_template('stock.html', command=True, warehouses=warehouse_command)
        else:
            return render_template('stock.html', command_error="Vous n'êtes pas autorisé à accéder à cette page")

    def warehouse(self):
        try:
            id_warehouse = request.form['warehouse']
            id_warehouse = str(id_warehouse.split('-')[-1])
        except KeyError:
            if self.id_warehouse is not None:
                id_warehouse = self.id_warehouse
            else:
                return render_template('stock.html', command_error="Vous n'avez pas sélectionné de stock")
        # remove space
        id_warehouse = id_warehouse.replace(' ', '')
        products = requests.get(config.url + config.url_product, headers=config.headers).text
        products = json.loads(products)

        # get all products whith product[fk_default_warehouse] == id_warehouse
        products = [product for product in products if product['fk_default_warehouse'] == id_warehouse]
        print(products)

        products = sorted(products, key=lambda k: k['array_options'] != [] and k['array_options'][
            'options_command'] is not None and json.loads(k['array_options']['options_command'])['status'] == "pending",
                          reverse=True)
        # put product['stock_warehouse'][fk_default_warehouse] == None in top of list
        products = sorted(products,
                          key=lambda k: k['stock_warehouse'] == [] or id_warehouse not in k['stock_warehouse'],
                          reverse=True)
        # put product['stock_warehouse'][fk_default_warehouse] == 1 after
        products = sorted(products,
                          key=lambda k: k['stock_warehouse'] == [] or id_warehouse not in k['stock_warehouse'] or
                                        k['stock_warehouse'][id_warehouse]['real'] == '1', reverse=True)

        for k in products:
            if k['array_options'] != [] and k['array_options']['options_command'] is not None:
                k['array_options']['options_command'] = json.loads(k['array_options']['options_command'])
            else:
                k['array_options'] = {}
                k['array_options']['options_command'] = {"status": "stored"}

        # round all cost_price to 2 decimals
        for product in products:
            try:
                product['cost_price'] = str(round(float(product['cost_price']), 2))
            except TypeError:
                product['cost_price'] = "N/A"

        self.products = products
        self.id_warehouse = id_warehouse

        return render_template('stock.html', command=True, warehouses=self.warehouses, product_command=products,
                               id_warehouse=id_warehouse)

    def add(self, id_product):
        product = requests.get(config.url + "products/" + id_product, headers=config.headers).text
        product = json.loads(product)
        try:
            identity = product['array_options']['options_command']['identity']
            description = product['array_options']['options_command']['description']
            quantity = product['array_options']['options_command']['quantity']
        except TypeError:
            identity = ""
            description = ""
            quantity = request.form['quantity']
        content = {"status": "waiting", "identity": identity, "description": description, "quantity": quantity}
        product = {"array_options": {"options_command": json.dumps(content)}}
        requests.put(config.url + "products/" + str(id_product), json=product, headers=config.headers)

        return self.warehouse()

    def remove(self, id_product):
        product = requests.get(config.url + "products/" + id_product, headers=config.headers).text
        product = json.loads(product)
        try:
            identity = product['array_options']['options_command']['identity']
            description = product['array_options']['options_command']['description']
            quantity = product['array_options']['options_command']['quantity']
        except TypeError:
            identity = ""
            description = ""
            quantity = ""
        content = {"status": "stored", "identity": identity, "description": description, "quantity": quantity}
        product = {"array_options": {"options_command": json.dumps(content)}}
        requests.put(config.url + "products/" + str(id_product), json=product, headers=config.headers)

        return self.generate()

    def generate(self, error=""):
        products = requests.get(config.url + config.url_product, headers=config.headers).text
        products = json.loads(products)

        waiting_product = []
        for product in products:
            if product['array_options'] != [] and product['array_options']['options_command'] is not None:
                try:
                    json_product = json.loads(product['array_options']['options_command'])
                except json.decoder.JSONDecodeError:
                    json_product = product['array_options']['options_command'].split(',')
                    json_product[0] = json_product[0][1:]
                    json_product[-1] = json_product[-1][:-1]
                    json_product = [element.split(':') for element in json_product]
                    for elt in json_product:
                        elt[0] = elt[0].replace("'", "")
                        elt[0] = elt[0].replace(' ', '')
                        elt[1] = elt[1].replace(' ', '')
                        elt[1] = elt[1].replace("'", '"')
                    json_product = {element[0]: element[1] for element in json_product}
                    json_product = {element[0]: element[1].replace("'", '"') for element in json_product.items()}
                if json_product['status'] == "waiting" or json_product['status'] == "shipping":
                    waiting_product.append(product)

        total = 0
        with open('/opt/wolf/fournisseurs.json', 'r') as f:
            fournisseurs = json.load(f)
            for product in waiting_product:
                try:
                    product['cost_price'] = str(round(float(product['cost_price']), 2))
                    total += float(product['cost_price'])
                except TypeError:
                    product['cost_price'] = "N/A"
                product['fournisseur'] = fournisseurs[product['accountancy_code_buy_intra']] if product[
                                                                                                    'accountancy_code_buy_intra'] in fournisseurs else {
                    'name': product['accountancy_code_buy_intra'], 'image': ""}
                product['array_options']['options_command'] = json.loads(product['array_options']['options_command'])
            total = str(round(total, 2))
        return render_template('stock.html', generate=True, products=waiting_product, total=total, error=error)

    def confirm(self):
        products = requests.get(config.url + config.url_product, headers=config.headers).text
        products = json.loads(products)

        request_product = [k for k in request.form]
        confirmed_product = {}
        for request_p in request_product:
            for product in products:
                if product['id'] == request_p:
                    confirmed_product[product['id']] = product

        thirdparties = requests.get(config.url + config.url_thirdparty_supplier, headers=config.headers).text
        thirdparties = json.loads(thirdparties)
        supplier = {}

        for product in confirmed_product:
            for thirdparty in thirdparties:
                if thirdparty['name_alias'] == confirmed_product[product]['accountancy_code_buy_intra']:
                    if confirmed_product[product]['accountancy_code_buy_intra'] not in supplier.keys():
                        supplier[confirmed_product[product]['accountancy_code_buy_intra']] = thirdparty

        supplierorder_dfaft = requests.get(config.url + config.url_supplierorder_draft, headers=config.headers).text
        supplierorder_dfaft = json.loads(supplierorder_dfaft)
        print(supplier)
        if supplier == {}:
            return self.generate(error="Aucun fournisseur n'a été trouvé pour les produits sélectionnés, "
                                       "veuillez compléter les informations fournisseurs dans dolibarr")

        command_empty = {}
        for supplier_name in supplier:
            command_empty[supplier_name] = {'thirdparty': supplier[supplier_name], 'draft': None}
            for draft in supplierorder_dfaft:
                if draft['fourn_id'] == supplier[supplier_name]['id']:
                    command_empty[supplier_name]['draft'] = draft

        for command in command_empty:
            if command_empty[command]['draft'] is None:
                command_json = {'entity': '1', 'validateFieldsErrors': [], 'import_key': None, 'array_options': [],
                                'array_languages': None, 'contacts_ids': None, 'linked_objects': [],
                                'linkedObjectsIds': None, 'linkedObjectsFullLoaded': [], 'canvas': None,
                                'fk_project': None, 'fk_projet': None, 'contact_id': None, 'user': None, 'origin': None,
                                'origin_id': None, 'ref_ext': None, 'statut': '0', 'status': '0', 'country_id': None,
                                'country_code': None, 'state_id': None, 'region_id': None, 'mode_reglement_id': None,
                                'cond_reglement_id': '1', 'demand_reason_id': None, 'transport_mode_id': None,
                                'shipping_method_id': None, 'model_pdf': 'muscadet', 'last_main_doc': None,
                                'fk_bank': None, 'fk_account': None, 'lines': [], 'name': None, 'lastname': None,
                                'firstname': None, 'civility_id': None, 'date_creation': 1670759966,
                                'date_validation': None, 'date_modification': None, 'date_cloture': None,
                                'user_author': None, 'user_creation': None, 'user_creation_id': None,
                                'user_valid': None, 'user_validation': None, 'user_validation_id': None,
                                'user_closing_id': None, 'user_modification': None, 'user_modification_id': None,
                                'specimen': 0, 'fk_incoterms': '0', 'label_incoterms': None, 'location_incoterms': '',
                                'ref_supplier': '', 'brouillon': 1, 'billed': '0',
                                'socid': int(command_empty[command]['thirdparty']['id']),
                                'fourn_id': int(command_empty[command]['thirdparty']['id']), 'date_valid': '',
                                'date_approve': '', 'date_approve2': '', 'date_commande': '', 'date_livraison': '',
                                'delivery_date': '', 'source': '0', 'cond_reglement_code': 'RECEP',
                                'cond_reglement_label': 'Due upon receipt', 'cond_reglement_doc': 'Due upon receipt',
                                'mode_reglement_code': None, 'methode_commande': None}
                for product in confirmed_product:
                    try:
                        quantity = confirmed_product[product]['array_options']['options_command']['quantity']
                    except TypeError:
                        quantity = "1"
                    if confirmed_product[product]['accountancy_code_buy_intra'] == command:
                        line = {'desc': confirmed_product[product]['description'],
                                'subprice': confirmed_product[product]['cost_price'], 'qty': quantity,
                                'tva_tx': confirmed_product[product]['tva_tx'],
                                'fk_product': confirmed_product[product]['id'], 'product_type': '0'}
                        command_json['lines'].append(line)

                status = requests.post(config.url + "supplierorders", headers=config.headers,
                                       data=json.dumps(command_json))
            else:
                for product in confirmed_product:
                    try:
                        quantity = confirmed_product[product]['array_options']['options_command']['quantity']
                    except TypeError:
                        quantity = "1"
                    if confirmed_product[product]['accountancy_code_buy_intra'] == command:
                        created = True
                        for l in command_empty[command]['draft']['lines']:
                            if l['fk_product'] == confirmed_product[product]['id']:
                                l['qty'] = int(l['qty']) + int(quantity)
                                created = False
                                break
                        if created:
                            line = {'desc': confirmed_product[product]['description'],
                                    'subprice': confirmed_product[product]['cost_price'], 'qty': quantity,
                                    'tva_tx': confirmed_product[product]['tva_tx'],
                                    'fk_product': confirmed_product[product]['id'], 'product_type': '0'}
                            command_empty[command]['draft']['lines'].append(line)
                    status = requests.delete(
                        config.url + "supplierorders/" + str(command_empty[command]['draft']['id']),
                        headers=config.headers)
                    print(status.text)
                    status = requests.post(config.url + "supplierorders/", headers=config.headers,
                                           data=json.dumps(command_empty[command]['draft']))
                    print(status.text)

        for product in confirmed_product:
            try:
                identity = confirmed_product[product]['array_options']['options_command']['identity']
            except TypeError:
                identity = ""
            try:
                description = confirmed_product[product]['array_options']['options_command']['description']
            except TypeError:
                description = ""
            try:
                quantity = confirmed_product[product]['array_options']['options_command']['quantity']
            except TypeError:
                quantity = "1"
            content = {"status": "shipping", "identity": identity, "description": description, "quantity": quantity}
            product_content = {"array_options": {"options_command": json.dumps(content)}}
            requests.put(config.url + "products/" + str(product), json=product_content, headers=config.headers)

        return self.generate(error="Commande mise à jour, veuillez continuer dans dolibarr")
