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
        self.url_conrad = "https://www.conrad.fr/restservices/FR/products/"
        self.rfid = rfid.Serial()
        self.barcode = barcode.BarcodeReader()

    def find(self, ref=None):
        global product
        product = {}
        fournisseur = None
        id = None
        if ref is None:
            return None, None
        else:
            result, item, warehouse = self.find_dolibarr(ref)
            if item is not None:
                id = item["id"]
                fournisseur = item["accountancy_code_buy_intra"]
            thread_rs = threading.Thread(target=self.rs, args=(ref,))
            thread_rs.start()

            thread_otelo = threading.Thread(target=self.otelo, args=(ref,))
            thread_otelo.start()

            thread_makershop = threading.Thread(target=self.makershop, args=(ref,))
            thread_makershop.start()

            thread_conrad = threading.Thread(target=self.conrad, args=(ref,))
            thread_conrad.start()

            thread_rs.join()
            thread_otelo.join()
            thread_makershop.join()
            thread_conrad.join()

            for prod in product:
                try:
                    if product[prod]['fournisseur']['ref'] == fournisseur:
                        product[prod]['eirlab'] = True
                        product[prod]['warehouse'] = warehouse
                        product[prod]['dolibarr'] = item
                    else:
                        product[prod]['eirlab'] = False
                except KeyError:
                    product[prod]['eirlab'] = False

            return result, product

    def find_dolibarr(self, ref):
        # remove '-' from ref
        ref = ref.replace('-', '')
        products = requests.get(config.url + config.url_product, headers=config.headers).text
        products = json.loads(products)
        warehouses = requests.get(config.url + config.url_warehouse, headers=config.headers).text
        warehouses = json.loads(warehouses)
        for item in products:
            try:
                if item["accountancy_code_buy"] == ref:
                    for warehouse in warehouses:
                        if warehouse["id"] == item["fk_default_warehouse"]:
                            print(item)
                            return True, item, warehouse
            except TypeError:
                pass
        return False, None, None

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
                dict_attributes[row.find('td', attrs={'data-testid': 'specification-attributes-key'}).text] = row.find(
                        'td', attrs={'data-testid': 'specification-attributes-value'}).text
        except AttributeError:
            dict_attributes = {}
        if title == "" and price == "" and links == "" and image == "" and dict_attributes == {}:
            return
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
        if title == "" and price == "" and links == "" and image == "" and dict_attributes == {}:
            return
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
            price = price.replace('TTC', '')
            price = price.replace('€', ',')
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
        if title == "" and price == "" and links == "" and image == "" and dict_attributes == {}:
            return
        with open('/opt/wolf/fournisseurs.json', 'r') as f:
            data = json.load(f)
            product['makershop'] = {"fournisseur": data['makershop'], "title": title, "price": price, "links": links,
                                    "attributes": dict_attributes, "ref": ref, "image": image,
                                    "links_ref": self.url_makershop + ref}
            return product

    def conrad(self, ref):
        global product
        # remove all 0 at the beginning of the ref
        ref = ref.lstrip('0')
        try:
            json_product = requests.get(self.url_conrad + ref).json()['body']
        except KeyError:
            return
        try:
            title = json_product['title']
        except AttributeError:
            title = ""
        try:
            price = json_product['price']['unit']['gross']
        except AttributeError:
            price = ""
        try:
            links = json_product['productMedia'][0]['url']
        except AttributeError:
            links = ""
        try:
            image = json_product['image']['url']
        except AttributeError:
            image = ""
        dict_attributes = {}
        try:
            for tr in json_product['technicalAttributes']:
                dict_attributes[tr['name']] = tr['values'][0]['value']
        except AttributeError:
            dict_attributes = {}
        try:
            links_ref = "www.conrad.fr" + json_product['urlPath']
        except AttributeError:
            links_ref = ""

        if title == "" and price == "" and links == "" and image == "" and dict_attributes == {}:
            return
        with open('/opt/wolf/fournisseurs.json', 'r') as f:
            data = json.load(f)
            product['conrad'] = {"fournisseur": data['conrad'], "title": title, "price": price, "links": links,
                                 "attributes": dict_attributes, "ref": ref, "image": image, "links_ref": links_ref}
            return product


if __name__ == '__main__':
    four = Fournisseurs()
    four.conrad('001693994')
