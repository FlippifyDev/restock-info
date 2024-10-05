from dotenv import load_dotenv
from datetime import datetime, timezone
import urllib.parse
from pymongo import UpdateOne

import logging
import pymongo
import os

logger = logging.getLogger("PING-MANAGER")

load_dotenv()


class Database():
    def __init__(self) -> None:
        # Config
        db_deployment =  os.getenv("DB_DEPLOYMENT")
        db_name =        os.getenv("DB_NAME")
        username =       os.getenv("DB_USERNAME")
        password =       os.getenv("DB_PASSWORD")

        # Config - Collections Names
        results_col =              os.getenv("COL_RESULTS")

        # Connection
        conn_string = f"mongodb+srv://{username}:{password}@{db_deployment}.mongodb.net/"
        self.client = pymongo.MongoClient(conn_string)
        self.db = self.client[db_name]

        # Collections
        self.results_col = self.db[results_col]

        # Create or modify the collection with changeStreamPreAndPostImages enabled
        try:
            self.db.create_collection(results_col, changeStreamPreAndPostImages={"enabled": True})
        except pymongo.errors.CollectionInvalid:
            # Collection already exists, so modify it to enable pre- and post-images
            self.db.command({
                'collMod': results_col,
                'changeStreamPreAndPostImages': {'enabled': True}
            })


    def fetch_docs(self, query, projection):
        return list(self.results_col.find(query, projection))
    

    def add_products(self, products_to_add): 
        try:
            for product in products_to_add:
                # Check if a product with the same 'deal-link' already exists
                if self.results_col.find_one({"link": product['link']}):
                    continue

                # Insert product if it's not a duplicate
                self.results_col.insert_one(product)

            return True
        except pymongo.errors.PyMongoError as e:
            logger.error(f"Error while adding products to the database: {e}")
            return False

  
    def add_timestamps_to_existing_products(self):
        try:
            # Create a filter to find documents that don't have a 'timestamp' field
            query = {"region": {"$exists": False}}

            # Define the update operation to add the current timestamp (UTC)
            update = {"$set": {"region": "uk"}}

            # Update all documents that match the query
            result = self.results_col.update_many(query, update)

            logger.info(f"Updated {result.modified_count} products with a timestamp.")
            return True
        except pymongo.errors.PyMongoError as e:
            logger.error(f"Error while updating timestamps for products: {e}")
            return False
        

    def add_type_to_existing_products(self):
        try:
            # Create a filter to find documents that don't have a 'timestamp' field
            query = {"last_updated": {"$exists": True}}

            # Define the update operation to add the current timestamp (UTC)
            update = {"$unset": {"last_updated": ""}}

            # Update all documents that match the query
            result = self.results_col.update_many(query, update)

            logger.info(f"Updated {result.modified_count} products with a timestamp.")
            return True
        except pymongo.errors.PyMongoError as e:
            logger.error(f"Error while updating timestamps for products: {e}")
            return False
        



    def add_ebay_links_to_existing_products(self):
        try:
            # Fetch all products from the database
            products = self.fetch_docs({"website": "Playstation Direct"}, {})
            updates = []

            # Iterate over each product
            for prod in products:
                # Generate the eBay search URL using the product name (converted to lowercase and URL-encoded)
                product_name = prod["product_name"].lower()
                encoded_product_name = urllib.parse.quote_plus(product_name)
                ebay_url = f"https://www.ebay.co.uk/sch/i.html?_nkw={encoded_product_name}&_sacat=0&rt=nc&LH_Sold=1&LH_Complete=1"

                # Check if the product already has the eBay link, if not, or if it's outdated, update it
                if "ebay_link" not in prod or prod["ebay_link"] != ebay_url:
                    update = {
                        "$set": {
                            "ebay_link": ebay_url,
                        }
                    }
                    updates.append(UpdateOne({"_id": prod["_id"]}, update))

            # Perform the bulk update if there are any updates
            if updates:
                result = self.results_col.bulk_write(updates)
                print(f"{result.modified_count} products updated with eBay links.")
            else:
                print("No products needed an eBay link update.")
        
        except pymongo.errors.PyMongoError as e:
            logger.error(f"Error while adding eBay links to products: {e}")