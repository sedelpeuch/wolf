import json
import threading
import time

import requests
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer, util

import barcode
import config
import rfid

product = {}
name_product = {}


class Fournisseurs:
    def __init__(self):
        self.url_rs = "http://fr.rs-online.com/web/search/searchBrowseAction.html?method=searchProducts&searchTerm="
        self.url_otelo = "https://www.otelo.fr/is-bin/INTERSHOP.enfinity/WFS/Otelo-France-Site/fr_FR/-/EUR/Navigation" \
                         "-Dispatch?Ntk=Default_OTFR&Ntt="
        self.url_makershop = "https://www.makershop.fr/recherche?search_query="
        self.url_conrad = "https://www.conrad.fr/restservices/FR/products/"
        self.url_farnell = "https://fr.farnell.com/"
        self.rfid = rfid.Serial()
        self.barcode = barcode.BarcodeReader()

    def find(self, ref=None):
        global product
        product = {}
        fournisseur = None
        if ref is None:
            return None, None
        else:
            result, item, warehouse = self.find_dolibarr(ref)
            if item is not None:
                fournisseur = item["accountancy_code_buy_intra"]
            thread_rs = threading.Thread(target=self.rs, args=(ref,))
            thread_rs.start()

            thread_otelo = threading.Thread(target=self.otelo, args=(ref,))
            thread_otelo.start()

            thread_makershop = threading.Thread(target=self.makershop, args=(ref,))
            thread_makershop.start()

            thread_conrad = threading.Thread(target=self.conrad, args=(ref,))
            thread_conrad.start()

            thread_farnell = threading.Thread(target=self.farnell, args=(ref,))
            thread_farnell.start()

            thread_rs.join()
            thread_otelo.join()
            thread_makershop.join()
            thread_conrad.join()
            thread_farnell.join()
            emp = False
            for prod in product:
                try:
                    if product[prod]['fournisseur']['ref'] == fournisseur:
                        in_stock = requests.get(config.url + "products/" + item["id"] + "/stock",
                                                headers=config.headers).text
                        in_stock = json.loads(in_stock)
                        print(in_stock)
                        for stock in in_stock['stock_warehouses']:
                            if int(in_stock['stock_warehouses'][stock]['real']) > 0 and stock != '2':
                                product[prod]['eirlab'] = True
                            else:
                                emp = True
                                product[prod]['eirlab'] = False
                        product[prod]['warehouse'] = warehouse
                        product[prod]['dolibarr'] = item
                    else:
                        product[prod]['eirlab'] = False
                except KeyError:
                    product[prod]['eirlab'] = False
            # if all product[prod]['eirlab'] are False, return result, product, item else return result, product, None
            if all(product[prod]['eirlab'] == False for prod in product) and item is not None and not emp:
                product['eirlab'] = {
                    'fournisseur': {'name': 'EirLab', 'image': '/static/img/eirlab.png', 'id': '6', 'ref': 'eirlab'},
                    'title': item['label'], 'price': item['cost_price'], 'links': item['url'], 'attributes': {},
                    'ref': item['accountancy_code_buy'], 'image': '', 'links_ref': '', 'eirlab': True}
                product['eirlab']['warehouse'] = warehouse
                product['eirlab']['dolibarr'] = item
                return result, product, item
            return result, product, item

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
                            return True, item, warehouse
            except TypeError:
                pass
        return False, None, None

    def find_id(self, id):
        global name_product
        products = requests.get(config.url + config.url_product, headers=config.headers).text
        products = json.loads(products)
        for item in products:
            if item["id"] == id:
                fournisseur = item["accountancy_code_buy_intra"]
                ref = item["accountancy_code_buy"]
                product = getattr(self, fournisseur)(ref)[fournisseur]
                status, item, warehouse = self.find_dolibarr(ref)

                in_stock = requests.get(config.url + "products/" + item["id"] + "/stock", headers=config.headers).text
                in_stock = json.loads(in_stock)
                for stock in in_stock['stock_warehouses']:
                    if int(in_stock['stock_warehouses'][stock]['real']) > 0 and stock != '2':
                        product['eirlab'] = True
                    else:
                        product['eirlab'] = False
                product['warehouse'] = warehouse
                product['dolibarr'] = item
                name_product[id] = product

    def find_dolibarr_name(self, name):
        global name_product
        name_product = {}
        products = requests.get(config.url + config.url_product, headers=config.headers).text
        products = json.loads(products)
        embedder = SentenceTransformer('all-MiniLM-L6-v2')
        corpus = []
        corpus_item_id = []
        thread_pool = []
        for item in products:
            if item["type"] == '0':
                corpus.append(item["label"])
                corpus_item_id.append(item["id"])
        corpus_embeddings = embedder.encode(corpus, convert_to_tensor=True)
        query_embedding = embedder.encode([name], convert_to_tensor=True)
        cos_scores = util.semantic_search(query_embedding, corpus_embeddings)[0]
        for elt in cos_scores:
            thread_pool.append(threading.Thread(target=self.find_id, args=(corpus_item_id[elt['corpus_id']],)))
        for thread in thread_pool:
            thread.start()
        for thread in thread_pool:
            thread.join()
        return name_product

    def rs(self, ref):
        global product
        headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                                 'Chrome/51.0.2704.103 Safari/537.36', 'Upgrade-Insecure-Requests': '1',
                   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,'
                             '*/*;q=0.8,application/signed-exchange;v=b3;q=0.9', 'Accept-Encoding': 'gzip, deflate, br',
                   'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7'}

        begin = time.time()
        html = requests.get(self.url_rs + ref, headers=headers).text
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

        try:
            packaging = parsed_html.body.find('input', attrs={'id': 'quantity-input'}).get('value')
        except AttributeError:
            packaging = ""

        if title == "" and price == "" and links == "" and image == "" and dict_attributes == {} and packaging == "":
            return
        with open('/opt/wolf/fournisseurs.json', 'r') as f:
            data = json.load(f)
            product['rs'] = {"fournisseur": data['rs'], "title": title, "price": price, "links": links,
                             "attributes": dict_attributes, "ref": ref.replace('-', ''), "image": image,
                             "links_ref": self.url_rs + ref, "packaging": packaging}
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
                                "links_ref": self.url_otelo + ref, "packaging": "1"}
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
            title = parsed_html.body.find('h1', attrs={'class': 'product-name'}).text
        except AttributeError:
            title = ""
        try:
            price = parsed_html.body.find('span', attrs={'class': 'col-xs-4 price'}).text
            price = price.replace('TTC', '')
            price = price.replace('€', ',')
        except AttributeError:
            try:
                price = parsed_html.body.find('span', attrs={'class': 'our_price_display'}).text
                price = price.replace('TTC', '')
                price = price.replace('HT', '')
                price = price.replace('€', ',')
                price = price.split('/')[1]
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
                                    "links_ref": self.url_makershop + ref, "packaging": "1"}
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
        except KeyError:
            price = ""
        try:
            links = json_product['productMedia'][0]['url']
        except AttributeError:
            links = ""
        except IndexError:
            links = ""
        try:
            image = json_product['image']['url']
        except AttributeError:
            image = ""
        dict_attributes = {}
        try:
            for tr in json_product['technicalAttributes']:
                dict_attributes[tr['name']] = tr['values'][0]['value']
            if 'Contenu' in dict_attributes:
                packaging = dict_attributes["Contenu"].replace("pc(s)", "")
            else:
                packaging = "1"
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
                                 "attributes": dict_attributes, "ref": ref, "image": image, "links_ref": links_ref,
                                 "packaging": packaging}
            return product

    def farnell(self, ref):
        global product
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                                 'Chrome/83.0.4103.116 Safari/537.36'}
        html = requests.get(self.url_farnell + ref, headers=headers).text
        html = html.replace('\n', '')
        html = html.replace('\t', '')
        html = html.replace('\r', '')
        try:
            parsed_html = BeautifulSoup(html, "html.parser")
        except AttributeError:
            return

        try:
            title = parsed_html.body.find('h1', attrs={'class': 'pdpMainPartNumber'}).text
        except AttributeError:
            title = ""

        try:
            price = parsed_html.body.find('span', attrs={'class': 'price vatExcl'}).text
        except AttributeError:
            price = ""

        try:
            links = parsed_html.body.find('a', attrs={'rel': 'nofollow noopener'}).get('href')
        except AttributeError:
            links = ""

        try:
            image = parsed_html.body.find('img', attrs={'id': 'productMainImage'}).get('src')
        except AttributeError:
            image = ""

        try:
            table_label = []
            table_value = []
            dict_attributes = {}
            all_dl = parsed_html.find_all('dl')
            for dl in all_dl:
                dt = dl.find_all('dt')
                for element in dt:
                    label = element.find('label')
                    if label is not None:
                        table_label.append(label.text)
            all_dd = parsed_html.find_all('dd')
            for dd in all_dd:
                # check if id begin with descAttributeValue
                if dd.get('id') is not None and dd.get('id').startswith('descAttributeValue'):
                    table_value.append(dd.text)

            if len(table_label) != len(table_value):
                dict_attributes = {}
            else:
                for i in range(len(table_label)):
                    dict_attributes[table_label[i]] = table_value[i]
        except TypeError:
            dict_attributes = {}

        try:
            packaging = parsed_html.body.find('div', attrs={'class': 'multqty'}).find('strong').text
        except AttributeError:
            packaging = ""

        if title == "" and price == "" and links == "" and image == "" and dict_attributes == {}:
            return
        with open('/opt/wolf/fournisseurs.json', 'r') as f:
            data = json.load(f)
            product['farnell'] = {"fournisseur": data['farnell'], "title": title, "price": price, "links": links,
                                  "attributes": dict_attributes, "ref": ref, "image": image,
                                  "links_ref": self.url_farnell + ref, "packaging": packaging}
            return product


if __name__ == '__main__':
    four = Fournisseurs()
    print(four.find_dolibarr_name("Résistance"))
