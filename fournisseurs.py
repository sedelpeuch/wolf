import json
import threading

import requests
from bs4 import BeautifulSoup

import barcode
import config
import rfid

product = {}


class Fournisseurs:
    def __init__(self):
        self.url_rs = "http://fr.rs-online.com/web/search/searchBrowseAction.html?method=searchProducts&searchTerm="
        self.url_otelo = "https://www.otelo.fr/is-bin/INTERSHOP.enfinity/WFS/Otelo-France-Site/fr_FR/-/EUR/Navigation" \
                         "-Dispatch?Ntk=Default_OTFR&Ntt="
        self.url_makershop = "https://www.makershop.fr/recherche?search_query="
        self.rfid = rfid.Serial()
        self.barcode = barcode.BarcodeReader()

    def find(self, ref=None):
        global product
        product = {}
        if ref is None:
            return None, None
        else:
            result, id = self.find_dolibarr(ref)
            thread_rs = threading.Thread(target=self.rs, args=(ref,))
            thread_rs.start()

            thread_otelo = threading.Thread(target=self.otelo, args=(ref,))
            thread_otelo.start()

            thread_makershop = threading.Thread(target=self.makershop, args=(ref,))
            thread_makershop.start()

            thread_rs.join()
            thread_otelo.join()
            thread_makershop.join()

            self.makershop(ref)
            return result, product

    def find_dolibarr(self, ref):
        # remove '-' from ref
        ref = ref.replace('-', '')
        products = requests.get(config.url + config.url_product, headers=config.headers).text
        products = json.loads(products)
        for product in products:
            if product["accountancy_code_buy"] == ref:
                return True, product["id"]
        return False, None

    def rs(self, ref):
        global product
        html = requests.get(self.url_rs + ref).text
        try:
            parsed_html = BeautifulSoup(html, "html.parser")
        except AttributeError:
            return
        try:
            title = parsed_html.body.find('h1', attrs={'data-testid': 'long-description'}).text
        except AttributeError:
            title = ""
        try:
            price = parsed_html.body.find('p', attrs={'data-testid': 'price-inc-vat'}).text
        except AttributeError:
            price = ""
        try:
            links = parsed_html.body.find('ul', attrs={'data-testid': 'technical-documents'}).find_all('a')[0].get(
                'href')
        except AttributeError:
            links = ""
        try:
            image = parsed_html.find('script', attrs={'data-testid': 'product-list-script'}).text
            image = dict(json.loads(image))['image']
        except AttributeError:
            image = ""
        try:
            dict_attributes = {}
            for row in parsed_html.body.find('table', attrs={'data-testid': 'specification-attributes'}).find(
                    'tbody').find_all('tr'):
                dict_attributes[row.find('td', attrs={'data-testid': 'specification-attributes-key'}).text] = \
                    row.find('td', attrs={'data-testid': 'specification-attributes-value'}).text
        except AttributeError:
            dict_attributes = {}
        with open('/opt/wolf/fournisseurs.json', 'r') as f:
            data = json.load(f)
            product['rs'] = {"fournisseur": data['rs'], "title": title, "price": price, "links": links,
                             "attributes": dict_attributes, "ref": ref.replace('-', ''), "image": image,
                             "links_ref": self.url_rs + ref}
            return product

    def otelo(self, ref):
        global product
        html = requests.get(self.url_otelo + ref).text
        html = html.replace('\n', '')
        html = html.replace('\t', '')
        try:
            parsed_html = BeautifulSoup(html, "html.parser")
        except AttributeError:
            return

        try:
            title = parsed_html.body.find('h1', attrs={'id': 'sku_Title'}).text
        except AttributeError:
            title = ""
        try:
            price = parsed_html.body.find('p', attrs={'class': 'PriceGris'}).text
        except AttributeError:
            price = ""
        try:
            links = parsed_html.body.find('div', attrs={'class': 'skuTabsDocIMG'}).find_all('a')[0].get('href')
        except AttributeError:
            links = ""
        try:
            image = "https://www.otelo.fr/" + parsed_html.body.find('img', attrs={'class': 'ChangePhoto'}).get('src')
        except AttributeError:
            image = ""
        dict_attributes = {}
        try:
            for tr in parsed_html.body.find('table', attrs={'class': 'CaracTable'}).find_all('tr'):
                if len(tr.find_all('td')) == 2:
                    dict_attributes[tr.find_all('td')[0].text] = tr.find_all('td')[1].text
        except AttributeError:
            dict_attributes = {}

        with open('/opt/wolf/fournisseurs.json', 'r') as f:
            data = json.load(f)
            product['otelo'] = {"fournisseur": data['otelo'], "title": title, "price": price, "links": links,
                                "attributes": dict_attributes, "ref": ref, "image": image,
                                "links_ref": self.url_otelo + ref}
            return product

    def makershop(self, ref):
        global product
        html = requests.get(self.url_makershop + ref).text
        try:
            parsed_html = BeautifulSoup(html, "html.parser")
            parsed_html = parsed_html.body.find('a', attrs={'class': 'product_img_link'}).get('href')
            html = requests.get(parsed_html).text
            parsed_html = BeautifulSoup(html, "html.parser")
        except AttributeError:
            return
        try:
            title = parsed_html.body.find('h1', attrs={'class': 'product-name pull-right col-xs-12 col-md-7'}).text
        except AttributeError:
            title = ""
        try:
            price = parsed_html.body.find('span', attrs={'class': 'col-xs-4 price'}).text
        except AttributeError:
            price = ""
        links = ""
        dict_attributes = {}
        try:
            dict_attributes["description"] = parsed_html.body.find('div',
                                                                   attrs={'id': 'short_description_content'}).text
        except AttributeError:
            dict_attributes["description"] = ""
        try:
            image = parsed_html.body.find('a', attrs={'class': 'fancybox shown'}).get('href')
        except AttributeError:
            image = ""
        with open('/opt/wolf/fournisseurs.json', 'r') as f:
            data = json.load(f)
            product['makershop'] = {"fournisseur": data['makershop'], "title": title, "price": price,
                                    "links": links,
                                    "attributes": dict_attributes, "ref": ref, "image": image,
                                    "links_ref": self.url_otelo + ref}
            return product
