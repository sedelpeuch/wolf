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
                            array_options = json.loads(product['array_options']['options_command'])
                            if array_options['status'] == "pending" or array_options['status'] == "waiting":
                                warehouse_command[product['fk_default_warehouse']]['command'] += 1
                return render_template('stock.html', command=True, warehouses=warehouse_command)
        else:
            return render_template('stock.html', command_error="Vous n'êtes pas autorisé à accéder à cette page")

    def warehouse(self):
        id_warehouse = request.form['warehouse']
        id_warehouse = str(id_warehouse.split('-')[-1])
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
