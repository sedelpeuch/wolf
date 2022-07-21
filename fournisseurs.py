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
        self.url_makershop = "https://www.makershop.fr/recherche?search_query="

    def find(self, ref=None):
        global product
        product = {}
        if ref is None:
            return None, None
        else:
            result = self.find_dolibarr(ref)
            thread_rs = threading.Thread(target=self.rs, args=(ref,))
            thread_rs.start()

            thread_otelo = threading.Thread(target=self.otelo, args=(ref,))
            thread_otelo.start()

            thread_makershop = threading.Thread(target=self.makershop, args=(ref,))
            thread_makershop.start()

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
        try:
            parsed_html = BeautifulSoup(html, "html.parser")
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
            with open('/opt/wolf/fournisseurs.json', 'r') as f:
                data = json.load(f)
                product['rs'] = {"fournisseur": data['rs'], "title": title, "price": price, "links": links,
                                 "attributes": dict_attributes, "ref": ref, "image": image,
                                 "links_ref": self.url_rs + ref}
        except AttributeError:
            pass

    def otelo(self, ref):
        global product
        html = requests.get(self.url_otelo + ref).text
        try:
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

            with open('/opt/wolf/fournisseurs.json', 'r') as f:
                data = json.load(f)
                product['otelo'] = {"fournisseur": data['otelo'], "title": title, "price": price, "links": links,
                                    "attributes": dict_attributes, "ref": ref, "image": image,
                                    "links_ref": self.url_otelo + ref}
        except AttributeError:
            pass

    def makershop(self, ref):
        global product
        html = requests.get(self.url_makershop + ref).text
        try:
            parsed_html = BeautifulSoup(html, "html.parser")
            parsed_html = parsed_html.body.find('a', attrs={'class':'product_img_link'}).get('href')
            html = requests.get(parsed_html).text
            parsed_html = BeautifulSoup(html, "html.parser")

            # <h1 class="product-name pull-right col-xs-12 col-md-7" itemprop="name"> Scanner 3D EinScan H <span
            # class="product-longname">Scanner 3D</span></h1>
            title = parsed_html.body.find('h1', attrs={'class': 'product-name pull-right col-xs-12 col-md-7'}).text
            # <span class="col-xs-4 price"> <span>5 518€<sup>80 TTC </sup></span> <span class="price-ecotax-sm"
            # data-duplicate="#buy_block p.price-ecotax">comprenant <span id="ecotax_price_display">0,04 €</span>
            # d'écotaxe</span> </span>
            price = parsed_html.body.find('span', attrs={'class': 'col-xs-4 price'}).text
            links = ""
            # <div id="short_description_content" class="rte text-justify" itemprop="description"><p>Le PolyLite PLA
            # Orange se caractérise par une très <strong>haute qualité au meilleur prix</strong>. Doté du Jam-Free,
            # il permet une extrusion continue sans risquer de boucher la buse. Livré en <strong>bobine plastique de
            # 1Kg</strong>, il est disponible en diamètre 1.75mm ou 2.85mm.</p></div>
            dict_attributes = {}
            dict_attributes["description"] = parsed_html.body.find('div', attrs={'id': 'short_description_content'}).text
            # <a href="https://cdn-2.makershop.fr/9469-thickbox_default/polylite-pla-orange-polymaker.jpg"
            # data-fancybox-group="other-views" class="fancybox shown" title="PolyLite PLA Orange "> <img
            # class="img-responsive" id="left_crsl_9469"
            # src="https://cdn-3.makershop.fr/9469-large_default/polylite-pla-orange-polymaker.jpg" alt="PolyLite PLA
            # Orange " title="PolyLite PLA Orange " itemprop="image"> </a>
            image = parsed_html.body.find('a', attrs={'class': 'fancybox shown'}).get('href')
            with open('/opt/wolf/fournisseurs.json', 'r') as f:
                data = json.load(f)
                product['makershop'] = {"fournisseur": data['makershop'], "title": title, "price": price, "links": links,
                                        "attributes": dict_attributes, "ref": ref, "image": image,
                                        "links_ref": self.url_otelo + ref}
        except AttributeError:
            pass

    def recherche(self):
        composant_eirlab, recherche_composant = self.find(request.form['ref'])
        if recherche_composant == {}:
            return render_template('stock.html', unknow_composant=True)
        else:
            return render_template('stock.html', recherche_composant=recherche_composant, recherche=True,
                                   composant_eirlab=composant_eirlab)


if __name__ == "__main__":
    four = Fournisseurs()
    print(four.find("POL-LIT-ORA-PLA"))
