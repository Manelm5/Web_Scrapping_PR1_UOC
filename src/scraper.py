import requests
from bs4 import BeautifulSoup
from category.category import Category
from product.item import Item


class Scraper:

    def __init__(self):
        self.url = ""
        self.data = []
        self.items = []

    def save_html(self, html, path):
        with open(path, 'wb') as f:
            f.write(html)

    def open_html(self, path):
        with open(path, 'rb') as f:
            return f.read()

    def get_links(self, html):
        bs = BeautifulSoup(html, 'html.parser')

        #Cogemos los divs con este class ya que son los que tienen los links que deseamos obtener (links de menú)
        divs = bs.select(".cize-custommenu")

        all_Tags = []
        for div in divs:
            categories = div.select("ul li")
            category_list = [category.text.strip() for category in categories]
            a_tags = [category.select_one("a", href=True) for category in categories]
            for tag in a_tags:
                all_Tags.append(tag)

        return all_Tags

    def scrape_product(self, product):

        r = requests.get(product["href"])
        bs = BeautifulSoup(r.content, 'html.parser')

        print("Web Scraping product: " + product["href"] + "...")

        main_data = bs.find_all("span", class_="woocommerce-Price-amount amount")

        if main_data is not None:
            price = [i.text.split("\xa0")[0] for i in main_data]
            # Partimos de la premisa que price[0] es el precio original y price[1] el descontado
            orig_price = price[0]
            if len(price) == 1:
                dte_price = orig_price
            else:
                dte_price = price[1]

            figure_tag = bs.find("figure", class_="woocommerce-product-gallery__wrapper")

            # Seleccionamos el objeto img que contendrá el link de la imagen del producto
            img = figure_tag.select_one("img")

            # Recogemos las capacidades del item si existen
            capacity = bs.find("p", class_="cap-variation")

            # No todos los links disponen de la capacity del producto, si no disponemos dejamos el atributo vacío
            if capacity is not None:
                capacity_txt = capacity.text.strip()
            else:
                capacity_txt = ""

            # Cogemos el porcentaje de descuento
            dte_percentage = bs.find("div", class_="discper")

            # Cogemos categorías
            span_cat = bs.select_one(".posted_in")

            # No todos los links disponen de la categoria del producto, si no disponemos dejamos el atributo vacío
            if span_cat is not None:
                categories = span_cat.select("a")
            else:
                categories = []

            category = [category.text.strip() for category in categories]

            # Añadimos un item a la lista de items
            self.items.append(Item(product.text.strip(), orig_price, dte_price, img["data-src"], capacity_txt, dte_percentage, category))

    def scrape_category(self, link):

        category = Category(link.text.strip(), link['href'], [])

        r = requests.get(category.link)
        bs = BeautifulSoup(r.content, 'html.parser')

        product_links = bs.select(".inner-product-title")

        for product in product_links:
            self.scrape_product(product.select_one("a"))

    def scrape(self, url):

        r = requests.get(url)
        self.save_html(r.content, "docs/tecnomari")

        html = self.open_html("docs/tecnomari")

        print("Web Scraping of Tecnomari products from  + self.url + ...")

        tag_links = self.get_links(html)

        # Bucle que procesa por cada categoría, todos los productos de cada una de ellas
        for link in tag_links:
            print("A link was found: " + link['href'] + " - Scrapping link data...")

            r = requests.get(link['href'])
            self.save_html(r.content, "docs/" + link['href'].split("/")[-2])

            self.scrape_category(link)

        filename = "data.csv"
        with open(filename, "w", encoding="utf-8") as file:
            # Añadimos la cabecera de las variables que añadiremos al csv
            file.write("Name" + "," + "Price" + "," + "Discount Price" + "," + "Product link" + "," + "Capacity" + "," + "Discount Percentage" + "," + "Categories")
            file.write("\n")

            # Para cada uno de nuestros items, escribimos su correspondiente linea en el csv
            for item in self.items:
                category_txt = ""
                for c in item.categories:
                    category_txt = c + "-" + category_txt

                print("Writing " + item.name + " in " + filename)
                file.write(
                    item.name + "," + item.price + "," + item.discount_price + "," + item.link + "," + item.capacity + "," + category_txt)
                file.write("\n")

