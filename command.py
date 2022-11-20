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
        self.bp.route('/generate')(self.generate)

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

        products = sorted(products, key=lambda k: k['array_options'] != [] and k['array_options'][
            'options_command'] is not None and json.loads(k['array_options']['options_command'])['status']=="pending",
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

    def generate(self):
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
                if json_product['status'] == "waiting":
                    waiting_product.append(product)

        total = 0
        with open('/opt/wolf/fournisseurs.json', 'r') as f:
            fournisseurs = json.load(f)
            for product in waiting_product:
                product['cost_price'] = str(round(float(product['cost_price']), 2))
                total += float(product['cost_price'])
                product['fournisseur'] = fournisseurs[product['accountancy_code_buy_intra']] if product[
                                                                                                    'accountancy_code_buy_intra'] in fournisseurs else {
                    'name': product['accountancy_code_buy_intra'], 'image': ""}
            total = str(round(total, 2))
        return render_template('stock.html', generate=True, products=waiting_product, total=total)
