import json
import threading

import requests
from bs4 import BeautifulSoup
from flask import Blueprint, render_template, request

import config

product = {}


class Fournisseurs:
    def __init__(self):
        self.bp = Blueprint('fournisseur', __name__, url_prefix='/stock')
        self.bp.route('/recherche', methods=['POST'])(self.recherche)
        # self.bp.route('/arrivage', methods=['GET'])(self.rs)
        # self.bp.route('/inventaire', methods=['POST'])(self.arrivage)
        self.url_rs = "http://fr.rs-online.com/web/search/searchBrowseAction.html?method=searchProducts&searchTerm="
        self.url_otelo = "https://www.otelo.fr/is-bin/INTERSHOP.enfinity/WFS/Otelo-France-Site/fr_FR/-/EUR/Navigation" \
                         "-Dispatch?Ntk=Default_OTFR&Ntt="

    def find(self, ref=None):
        global product
        product = {}
        if ref is None:
            return None, None
        else:
            ref = ref.replace('-', '')
            result = self.find_dolibarr(ref)
            thread_rs = threading.Thread(target=self.rs, args=(ref,))
            thread_rs.start()

            thread_otelo = threading.Thread(target=self.otelo, args=(ref,))
            thread_otelo.start()

            thread_rs.join()
            thread_otelo.join()

            return result, product

    def find_dolibarr(self, ref):
        # remove '-' from ref
        ref = ref.replace('-', '')
        products = requests.get(config.url + config.url_product, headers=config.headers).text
        products = json.loads(products)
        for product in products:
            if product["accountancy_code_buy"] == ref:
                return True
        return False

    def rs(self, ref):
        global product
        html = requests.get(self.url_rs + ref).text
        parsed_html = BeautifulSoup(html, "html.parser")
        try:
            title = parsed_html.body.find('h1', attrs={'data-testid': 'long-description'}).text
            price = parsed_html.body.find('p', attrs={'data-testid': 'price-inc-vat'}).text
            links = parsed_html.body.find('ul', attrs={'data-testid': 'technical-documents'}).find_all('a')[0].get(
                'href')
            image = parsed_html.find('script', attrs={'data-testid': 'product-list-script'}).text
            image = dict(json.loads(image))['image']
            dict_attributes = {}
            for row in parsed_html.body.find('table', attrs={'data-testid': 'specification-attributes'}).find(
                    'tbody').find_all('tr'):
                dict_attributes[row.find('td', attrs={'data-testid': 'specification-attributes-key'}).text] = \
                    row.find('td', attrs={'data-testid': 'specification-attributes-value'}).text
            with open('fournisseurs.json', 'r') as f:
                data = json.load(f)
                product['rs'] = {"fournisseur": data['rs'], "title": title, "price": price, "links": links,
                                 "attributes": dict_attributes, "ref": ref, "image": image}
                return
        except AttributeError:
            return

    def otelo(self, ref):
        global product
        html = requests.get(self.url_otelo + ref).text
        html = html.replace('\n', '')
        html = html.replace('\t', '')
        parsed_html = BeautifulSoup(html, "html.parser")

        title = parsed_html.body.find('h1', attrs={'id': 'sku_Title'}).text
        price = parsed_html.body.find('p', attrs={'class': 'PriceGris'}).text
        try:
            links = parsed_html.body.find('div', attrs={'class': 'skuTabsDocIMG'}).find_all('a')[0].get('href')
        except AttributeError:
            links = ""
        image = "https://www.otelo.fr/" + parsed_html.body.find('img', attrs={'class': 'ChangePhoto'}).get('src')
        dict_attributes = {}

        for tr in parsed_html.body.find('table', attrs={'class': 'CaracTable'}).find_all('tr'):
            if len(tr.find_all('td')) == 2:
                dict_attributes[tr.find_all('td')[0].text] = tr.find_all('td')[1].text

        with open('fournisseurs.json', 'r') as f:
            data = json.load(f)
            product['otelo'] = {"fournisseur": data['otelo'], "title": title, "price": price, "links": links,
                                "attributes": dict_attributes, "ref": ref, "image": image}

    def recherche(self):
        composant_eirlab, recherche_composant = self.find(request.form['ref'])
        if recherche_composant is None:
            return render_template('stock.html', unknow_composant=True)
        else:
            return render_template('stock.html', recherche_composant=recherche_composant, recherche=True,
                                   composant_eirlab=composant_eirlab)


if __name__ == "__main__":
    four = Fournisseurs()
    print(four.find("72400640"))
