from .headers import headers
from .scraper_ebay import fetch_products_info

from datetime import datetime, timezone
from pymongo import UpdateOne
import urllib.parse

import tls_client
import logging
import json


logger = logging.getLogger("RESTOCK_INFO")


def run_add_products(db):
    root_api = "https://api.direct.playstation.com/commercewebservices/ps-direct-gb/users/anonymous/products/productList?lang=en_GB&productCodes="
    root_api2 = "https://api.direct.playstation.com/commercewebservices/ps-direct-gb/products/1000046525-GB"

    requested_products = send_request(root_api2)["baseOptions"][0]["options"]
    prod_codes = []
    prod_codes_url = {}
    for prod in requested_products:
        prod_codes.append(prod["code"])
        prod_codes_url[prod["code"]] = "https://direct.playstation.com"+prod["url"]

    product_codes_url_param = ",".join(prod_codes)


    #products = db.fetch_docs({"website": "Playstation Direct"}, {"_id": 0})
    #product_dict = {prod["product_code"]: prod for prod in products}
    #product_codes_url_param = ",".join(list(product_dict.keys()))
    url = root_api + product_codes_url_param
    requested_products = send_request(url)["products"]
    
    products_to_add = []
    for prod in requested_products:
        release_date = prod.get("releaseDateDisplay")
        if release_date is not None:
            release_date.replace("\t", "")

        product_name = prod["name"].lower()
        encoded_product_name = urllib.parse.quote_plus(product_name)
        
        products_to_add.append(
            {
                "product_code": prod["code"],
                "product_name": prod["name"],
                "link": prod_codes_url[prod["code"]],
                "image": prod["images"][0]["url"],
                "website": "Playstation Direct",
                "price": prod["price"]["value"],
                "stock_available": prod["stock"]["stockLevelStatus"] == "inStock",
                "stock_level": "Low Stock" if prod["stock"]["isProductLowStock"] == True else "Normal",
                "maxOrderQuantity": prod["maxOrderQuantity"],
                "release_date": release_date,
                "ebay_mean_price": None,
                "sold_last_7_days": None,
                "sold_last_month": None,
                "ebay_url": f"https://www.ebay.co.uk/sch/i.html?_nkw={encoded_product_name}&_sacat=0&rt=nc&LH_Sold=1&LH_Complete=1",
                "timestamp": datetime.now(timezone.utc),
                "type": "Restock-Info"
            }
        )
    
    db.add_products(products_to_add)


def playstation_run(db):
    try:
        root_api = "https://api.direct.playstation.com/commercewebservices/ps-direct-gb/users/anonymous/products/productList?lang=en_GB&productCodes="
        products = db.fetch_docs({"website": "Playstation Direct"}, {})
        product_dict = {prod["product_code"]: prod for prod in products}
        product_codes_url_param = ",".join(list(product_dict.keys()))
        ebay_urls = [prod["ebay_link"] for prod in products]
        ebay_data = fetch_products_info(ebay_urls)

        url = root_api + product_codes_url_param
        requested_products = send_request(url)["products"]

        updates = []
        for new_prod in requested_products:
            try:
                old_prod = product_dict.get(new_prod["code"])
                prod_ebay_data = ebay_data[old_prod["ebay_link"]]

                old_stock = old_prod["stock_available"]
                new_stock = new_prod["stock"]["stockLevelStatus"] == "inStock"
                change_in_stock = new_stock != old_stock

                old_price = old_prod["price"]
                new_price = new_prod["price"]["value"]
                change_in_price = new_price != old_price

                old_stock_level = old_prod["stock_level"]
                new_stock_level = "Low Stock" if new_prod["stock"]["isProductLowStock"] == True else "Normal"
                change_in_stock_level = new_stock_level != old_stock_level

                old_ebay_price = old_prod["ebay_mean_price"]
                new_ebay_price = prod_ebay_data["ebay_mean_price"]
                change_in_stock_level = new_ebay_price != old_ebay_price

                if any([change_in_stock, change_in_price, change_in_stock_level]):
                    update = {
                        "$set": {
                            "stock_available": new_stock,
                            "price": new_price,
                            "stock_level": new_stock_level,
                            "ebay_mean_price": new_ebay_price,
                            "sold_last_7_days": prod_ebay_data["sold_last_7_days"],
                            "sold_last_month": prod_ebay_data["sold_last_month"],
                            "timestamp": datetime.now(timezone.utc)
                        }
                    }
                    updates.append(UpdateOne({"product_code": new_prod["code"]}, update))
            
            except Exception as error:
                logger.error(error)

        # Perform the bulk update if there are any updates
        if updates:
            result = db.results_col.bulk_write(updates)
            logger.info(f"{result.modified_count} products updated.")
        

    except Exception as error:
        logger.error(error)


def send_request(url):
    session = tls_client.Session(
        client_identifier="firefox_104"
    )

    res = session.get(url, headers=headers())
    if res.status_code != 200:
        logger.warning(f"Recieved status code ({res.status_code})")

    return json.loads(res.content)