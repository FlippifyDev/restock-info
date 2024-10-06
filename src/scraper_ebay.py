from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime, timedelta
from webscraper import html_session

import numpy as np
import logging
import string
import json
import re

logger = logging.getLogger("RESTOCK_INFO")


ebay_config = {
    "website": "eBay",
    "root": "https://www.ebay.co.uk",
    "region": "uk",
    "search-command": "/sch/i.html?_from=R40&_nkw=",
    "search-params": "&_sacat=0&rt=nc&LH_Sold=1&LH_Complete=1",
    "type": "html",
    "config": {
       "products": {
            "element-config": [
                {
                    "tag": "li",
                    "class": "s-item s-item__pl-on-bottom",
                    "max": 30
                }
            ],
            "title": {
                "element-config": [
                    {
                        "tag": "div",
                        "class": "s-item__title",
                        "attr": ".text"
                    }
                ]
            },
            "price": {
                "element-config": [
                    {
                        "tag": "span",
                        "class": "s-item__price",
                        "attr": ".text"
                    }
                ]
            },
            "sell-date": {
                "element-config": [
                    {
                        "tag": "span",
                        "class": "s-item__caption--signal POSITIVE",
                        "attr": ".text"
                    }
                ]
            }
        }
    }
}


def fetch_constants(key):
    with open("data/constants.json", "r") as file:
        return json.load(file)[key]

NORMALISE_TITLE_BLACKLISTED_WORDS = fetch_constants("normalise-title-blacklisted-words")


def fetch_products_info(urls):
    if len(urls) == 0:
        return {}
    
    scraped_data = html_session.run(urls, {"ebay": ebay_config}, batch_size=20, batch_delay_seconds=1)
    product_info = {}

    # Define the time frames
    today = datetime.now()
    last_7_days = today - timedelta(days=7)
    last_month = today - timedelta(days=30)

    for url, data in scraped_data.items():
        products = data.get("products", [])

        # Initialize counters for sold products
        sold_last_7_days = 0
        sold_last_month = 0
        
        # Extract product prices and clean them
        prices = []
        for product in products:
            price_str = product.get("price", "")
            sell_date_str = product.get("sell-date", "")
            if sell_date_str is None:
                continue
            sell_date_str = sell_date_str.replace("Sold ", "").strip()

            # Convert sell date to datetime object
            if sell_date_str:
                try:
                    sell_date = datetime.strptime(sell_date_str, '%d %b %Y')
                except ValueError:
                    continue  # If parsing fails, skip this product

                # Increment the counters based on the sell date
                if sell_date >= last_7_days:
                    sold_last_7_days += 1
                if sell_date >= last_month:
                    sold_last_month += 1

            
            # Handle price ranges like '£42.99 to £44.99'
            if 'to' in price_str:
                price_str = price_str.split('to')[-1].strip()  # Take the upper range price

            # Remove any non-numeric characters like currency symbols
            cleaned_price = re.sub(r'[^\d.]', '', price_str)
            
            # Convert to float if it's a valid number
            if cleaned_price:
                try:
                    price = float(cleaned_price)
                    prices.append(price)
                except ValueError:
                    continue

        # If no valid prices are found, skip this URL
        if not prices:
            continue
        
        # Filter out the top 20% and bottom 20% of prices
        filtered_prices = filter_prices(prices)
        
        if filtered_prices:
            # Calculate the mean of the filtered prices
            mean_price = np.mean(filtered_prices)
            product_info[url] = {
                "ebay_mean_price": round(float(mean_price), 2),
                "sold_last_7_days": sold_last_7_days,
                "sold_last_month": sold_last_month
            }
        else:
            product_info[url] = {
                "ebay_mean_price": None,  # No valid prices after filtering
                "sold_last_7_days": sold_last_7_days,
                "sold_last_month": sold_last_month
            }

    return product_info


def is_black_listed(title):
    black_listed_words = fetch_constants("black-listed-words")
    for word in black_listed_words:
        if word.lower() in title.lower():
            return True
    return False


def preprocess_text(text):
    text = text.lower()
    text = re.sub(f"[{string.punctuation}]", "", text)
    return text


def filter_matching_products(keyword, products, similarity_threshold=0.4):
    # Get all product titles
    product_titles = [product['title'] for product in products]
    
    # Determine the length of the longest product title
    max_title_length = max(len(title) for title in product_titles)
    
    # Adjust the keyword to match the length of the longest title
    if len(keyword) < max_title_length:
        keyword = keyword.ljust(max_title_length)  # Pad with spaces
    elif len(keyword) > max_title_length:
        keyword = keyword[:max_title_length]  # Truncate to max title length
    
    # Create a TF-IDF vectorizer and transform the product titles and keyword
    tfidf_vectorizer = TfidfVectorizer(stop_words='english', preprocessor=preprocess_text)
    tfidf_matrix = tfidf_vectorizer.fit_transform(product_titles + [keyword])
    
    # Compute cosine similarity between the keyword and product titles
    cosine_similarities = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1]).flatten()
    
    # Find matching products based on a similarity threshold
    matching_products = []
    for i, product in enumerate(products):
        if cosine_similarities[i] >= similarity_threshold:
            matching_products.append(product)
    
    return matching_products


def filter_prices(results):
    """Filter prices to remove the top 20% and bottom 20%."""
    if not results:
        return results

    # Calculate the 20th and 80th percentiles
    lower_bound = np.percentile(results, 20)
    upper_bound = np.percentile(results, 80)

    # Filter the prices
    filtered_prices = [price for price in results if lower_bound <= price <= upper_bound]
    return filtered_prices