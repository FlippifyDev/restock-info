from .headers import headers
from .scraper_ebay import fetch_products_info

from datetime import datetime, timezone
from pymongo import UpdateOne

import tls_client
import logging
import json


logger = logging.getLogger("RESTOCK_INFO")


custom_headers = {
  "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
  "Accept": "application/json",
  "Accept-Language": "en-GB,en;q=0.5",
  "Accept-Encoding": "gzip, deflate, br, zstd",
  "Referer": "https://www.argos.co.uk/product/",
  "X-NewRelic-ID": "VQEPU15SARAGV1hVDgMBUVY=",
  "DNT": "1",
  "Sec-Fetch-Dest": "empty",
  "Sec-Fetch-Mode": "cors",
  "Sec-Fetch-Site": "same-origin",
  "Connection": "keep-alive",
  "Cookie": "analytics_channel=ecomm; _abck=06B8AAC72D6057650FDEAC69F2B7870B~0~YAAQ5hp7XOS3r3GSAQAA6M3egAwozCEYGxLS/R7rTrSZFUqfIPqC8JvjWQSPYftiVUiOnP5N6csl6WWNo8HGaMOCvgD6K2rOwzLXozqpyKLawhoe0p+BGZvANSS2wipzNfz7iVa1xDXl2kRzQlA1WGzWT6OEKn8brNW7syq45OmZguPwrXQydfPIaK1AF1NW5Uk2ObvJQacWCa8o7jWUi95d5D5VVfE+puCs78pUaovtFOblndR40bG9LXkIiVNGaCBAA4oCyFYaaWTlQd0W0GzXCdWH8Dg/t66LZRT8iPky9A+PhM8FM3Nq6aHT9Pq1j4jkr4qRWnELI33xqhRvcshBb7J0YmBWT8rXFuRUESwTicnSAJY++BECc3NkuiJE/EnNCjj648CmURoTEqKkqA3pbfMTbkt0AeHk5BLJF2xGUwJE+oLufoReWCn2eXEN9HMG8gzevG3X8XqyxBj15gcK90epxHfH5iawl+82Fcp91qcXUO8z3m39UakcBZUdDuzkDZQOicWMNsNAKDzeiiEbOw3xEZZU2/H7Qp4mNSzoStkYJJKH92ywTnsEygujrXrO98iZ6gG+5GgyynZNFUdBDohCd9bhOdbr/D2CtUsu6/rZ8EGfUtB3yJusNMe0wWqvTLMpX0BqZJjp3Nqr7QB/EpRaDAunNKo=~-1~-1~-1; bm_s=YAAQ5hp7XKy3r3GSAQAAEcregAJV8FTtmbvfITvb1BT6bIRSFnQOb1NoB4jiIajOH1je8fA2ycpfTwXx2xL8alC49MghxQG/juZSMFDY7Xkkf322LNC4OFJUHKiVXWaAd84HhTsAylgnom1vBla+sthie0a3vpwVlFQNp9xffstrgrgt7EjDKwJOF20kwWyhXISySszcKvRHx8wfXsuXacJTUYOwhGL/WDzcaQdL86Rp/Y9q3+MMWrRdokOW8c6mH80pz3iOazAGustcSad3DJt80tZRvWEfev7HcHNKl3QZiynVJu/qMVhRDB3ANweGidFxfjYHbLAIItWsULD9k+oxH9z6A9zA; umdid=NTVkY2RiZDktN2QyNy00OWU4LTk1ODItMTA3OGIyMGVmMjE0fDhkNmRiN2RjLTdiNzctNGM2Yy04NzNkLTA0MGMwYTU5NTNhZHww; utag_main=v_id:019242fe04e80032f6ed4864fb2805050002700d00bd0$vapi_domain:argos.co.uk$_sn:7$_se:105$_ss:0$_st:1728740742192$dc_visit:7$ses_id:1728737623787%3Bexp-session$_pn:12%3Bexp-session$dc_event:84%3Bexp-session; Checkout_Test_Group_2=NEW_HD|NEW_HD_SI|NEW_HD_LI; akaas_arg_uk_global=1736514937~rv=46~id=a9575258b9ff3ef7e28bf74de86a7a18; AMCV_095C467352782EB30A490D45%40AdobeOrg=179643557%7CMCIDTS%7C20009%7CMCMID%7C45699738190180800510663221527467466931%7CMCAID%7CNONE%7CMCOPTOUT-1728746068s%7CNONE%7CvVersion%7C5.5.0; syte_uuid=f84462c0-7f2a-11ef-9376-e751a8baffe5; _taggstar_vid=f8cb48ec-7f2a-11ef-aa68-e777e56d0a0d; _taggstar_exp=v:3|id:tvt12|group:control; PDP_Test_Group_1=2; dclid=CKy8y8OL-ogDFSyP_QcdvGgHhQ; Basket_Checkout_Test_Group_2=2; Checkout_Segment=2; AWSALB=B/8W/odfQC+eVY2NE/AdWA062nOIlRQwfm0sglfvcsTSOBp6u2akTgIl2L5R26HhMN10S34qTMMG8XrmQ0S9cXlbcypPnUbig+lfP/ZQz5lznjP1DI3eEDQfI+ST; AWSALBCORS=B/8W/odfQC+eVY2NE/AdWA062nOIlRQwfm0sglfvcsTSOBp6u2akTgIl2L5R26HhMN10S34qTMMG8XrmQ0S9cXlbcypPnUbig+lfP/ZQz5lznjP1DI3eEDQfI+ST; WC_PERSISTENT=Gudr0zsUzc4ZL%2B9kAOM4XFLQltc%3D%0A%3B2024-10-07+13%3A52%3A20.792_1728154173409-43781026_10151_14696843760%2C110%2CGBP_10151; PostCodeSessionCookie=%2C%2C; UserPersistentSessionCookie=14696843760%3BNicholas%3BRECOGNISED%3BloggedIn%3BGIFT_NO%3B10.102.16.62.1728545262761530%3BREMEMBER_NO%3B%3Bfalse%3B; pwd_email=new; sessionId=ZtEzJvQuHLVSk3PzYmnXg5SBhatDrnRiXFyaU2p1HYDf1xlRP2yEGXd4sFw+gK6Z; cisId=1246539d8a954150a8b0bf2900b6b400; LastUrlCookie=/webapp/wcs/stores/servlet/OrderSummary; CONSENTMGR=consent:true%7Cts:1728744948028%7Cid:019242fe04e80032f6ed4864fb2805050002700d00bd0; Search_Test_Group_1=2; akavpau_vpc_gcd=1728739279~id=bc9ae3a6e68597b12f996dbc77146a1c; akavpau_vpc_pdpcd=1728739537~id=1595f5b5800c72c077b34c35a0a5ec62; PIM-SESSION-ID=fKZSi8YdW0m6VGj6; prev_vals=ar%3Apdp%3A4370011%3Aps5dualsensecontroller30thanniveraryltdednpre-order%3A*%7C*ar%3Aproductdetails%3A; ArgosPopUp_customer1=orderID=3582856851%3BaccountID=14696843760%3BcallbackID=0"
}



def stock_available_link(products):
    stock_root_api = "https://www.argos.co.uk/stores/api/orchestrator/v0/cis-locator/availability?skuQty="
    product_dict = {prod["product_code"]+"_1": prod for prod in products}
    product_codes_url_param = ",".join(list(product_dict.keys()))
    
    return stock_root_api + product_codes_url_param


def product_data_link(products):
    product_root_api = "https://www.argos.co.uk/product-api/pdp-service/partNumber/"
    product_dict = {prod["product_code"]: prod for prod in products}
    product_codes_url_param = ",".join(list(product_dict.keys()))  

    return product_root_api + product_codes_url_param



def argos_run(db):
    try:
        products = db.fetch_docs({"website": "Argos"}, {})
        
        stock_link = stock_available_link(products)
        stock_data = send_request(stock_link, custom_headers)["delivery"][0]["availability"]
        stock_dict = {prod["sku"]: prod for prod in stock_data}

        updates_dict = {}
        for old_prod in products:
            new_stock = stock_dict[old_prod["product_code"]]["quantityAvailable"] > 0
            if new_stock == old_prod["stock_available"]:
                continue
            updates_dict[old_prod["product_code"]] = {"stock_available": new_stock}

        product_link = product_data_link(products)
        product_data = send_request(product_link)
        product_dict = {prod["id"]: prod for prod in product_data["data"]}
        
        for old_prod in products:
            max_order_quanitity = product_dict[old_prod["product_code"]]["attributes"]["maximumQuantity"]
            new_prod = updates_dict.get("product_code")
            if new_prod is None:
                continue
            
            updates_dict["product_code"]["maxOrderQuantity"] = max_order_quanitity

            for item in product_data["included"]:
                if (item["id"] == old_prod["product_code"]) and (item["type"] == "prices"):
                    price = item["attributes"]["now"]
                    updates_dict[old_prod["product_code"]]["price"] = price
                    break
                continue
        
        updates = []
        for product_code, update in updates_dict.items():
            updates.append(UpdateOne({"product_code": product_code}, {"$set": update}))

        # Perform the bulk update if there are any updates
        if updates:
            result = db.results_col.bulk_write(updates)
            logger.info(f"{result.modified_count} products updated.")

    except Exception as error:
        logger.error(error)


def send_request(url, custom_headers=headers()):
    session = tls_client.Session(
        client_identifier="firefox_104"
    )
    
    logger.info(f"Scraping ({url})")
    res = session.get(url, headers=custom_headers)
    if res.status_code != 200:
        logger.warning(f"Recieved status code ({res.status_code})")

    return json.loads(res.content)