#!/usr/bin/python3
# Coding: utf-8

# vinted.py

import csv
import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Set

import requests
import schedule
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

logging.basicConfig(format="%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                    level=logging.INFO,
                    filename="vinted.log")

logger = logging.getLogger("vinted_scraper")

BOT_TOKEN = 'YOUR BOT TOKEN HERE'
BOT_CHATID = 'YOUR CHAT ID HERE'


def get_all_items(url: str) -> List[Dict]:
    """Function that returns a dictionary list of all items on the url page.
    
    Args:
        url (str): URL of the page to scrap.

    Returns:
        List: return a list of all items
    """
    
    options = Options()
    options.headless = True
    driver = webdriver.Firefox(options=options)
    driver.get(url)

    article_body = driver.find_element_by_class_name('feed-grid')
    articles = article_body.find_elements_by_class_name("feed-grid__item")
    
    list_of_items = []

    for article in articles:
        try:
                
            user, price, size, brand = [elem.text for elem in article.find_elements_by_class_name('Text_text__QBn4-')]
            link = article.find_element_by_class_name('c-box__overlay').get_attribute('href')

            item = dict()
            
            user = user.strip()
            price = price.strip()
            size = size.strip()
            brand = brand.strip()
            link = link.strip()
            name = " ".join(link.split("/")[-1].split("-")[1:]).title()
            id_ = link.split('/')[-1].split('-')[0]
            
            item['user'] = user
            item['price'] = price
            item['size'] = size
            item['name'] = name
            item['brand'] = brand
            item['link'] = link
            item['id'] = id_
            item['datetime'] = datetime.now().isoformat()
            
            list_of_items.append(item)

        except ValueError:
            pass
    
    driver.quit()
        
    return list_of_items


def get_all_ids(filename: str) -> Set:
    """Function that returns the set of all ids of all items saved in the file.

    Args:
        filename (str): File where items are saved.

    Returns:
        Set: Set of ids.
    """    
    
    ids = set()
    with open(filename, mode="r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            ids.add(row['id'])
    return ids
    
    
def create_csv_file(filename: str, fieldnames: List[str]) -> None:
    """Function that creates the backup file.

    Args:
        filename (str): File where items are saved.
        fieldnames (List): List containing item headers.
    """    
    
    with open(filename, mode="w", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(fieldnames)
        
        
def add_item_to_file(item: Dict, filename: str, fieldnames: List[Dict]) -> None:
    """Function that adds an item to the file.

    Args:
        item (Dict): Dictionary representing an item.
        filename (str): File where items are saved.
        fieldnames (List): List containing item headers.
    """    
    
    with open(filename, mode="a", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writerow(item)
        
def format_notification(list_of_items):
    message = []
    
    if len(list_of_items) == 0:
        return "<p>Aucun nouvel article &#128533;</p>"

    elif len(list_of_items) == 1:
        message.append('<strong>1 nouvel article disponible sur Vinted &#128512;</strong>')
        
    else:
        message.append(f"<strong>{len(list_of_items)} nouveaux articles disponibles sur Vinted &#129321;</strong>")
        message.append('<ul>')
        
    for item in list_of_items:
        message.append(f"<li><a href=\"{item['link']}\">{item['name']}</a>, {item['price']}</li>")

    message.append('</ul>')
    return ''.join(message)

def telegram_bot_sendtext(bot_message: str, *, bot_token: str, bot_chatid: str):
    """Send a notification to a telegram channel.

    Args:
        bot_message (str): Message you want to send.

    Returns:
        [request]: Returns a request object which is the response to send to the channel.
    """    

    send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + bot_chatid + '&parse_mode=html&text=' + bot_message

    response = requests.get(send_text)

    return response.json()


def main():
    FILENAME = "vinted.csv"
    FIELDNAMES = ['id', 'user', 'price', 'size', 'name', 'brand', 'link', 'datetime']
    URL = "https://www.vinted.fr/vetements?size_id[]=207&catalog[]=79&brand_id[]=304&price_to=20&status[]=1&status[]=6&status[]=2&order=newest_first"

    # Création du fichier dans lequel on stockera nos articles
    if not os.path.exists(FILENAME):
        create_csv_file(FILENAME, FIELDNAMES)
        logger.info(f"Creating the file `{FILENAME}`.")
        
    # Récupération de tous les ID
    set_of_ids = get_all_ids(FILENAME)
    logger.info(f"Recovery of all the IDs of the `{FILENAME}` file.")

    new_items = []
    for item in get_all_items(URL):
        
        # Si l'ID de l'article n'est pas dans le fichier, on ne l'a pas encore scrapé.
        if item['id'] not in set_of_ids:  
            add_item_to_file(item, FILENAME, FIELDNAMES)
            logger.info(f"New item, added to the file `{FILENAME}` : `{item}`.")
            new_items.append(item)
            
        else:
            logger.info(f"Item already saved in the file `{FILENAME}` : `{item}`.")

    # S'il y a des nouveaux items, on envoie une notification.
    if new_items:
        logger.info("New items saved, preparation of the telegram notification.")
        message = format_notification(new_items)

        # telegram_bot_sendtext(message, bot_token="BOTTOKENID", bot_chatid="BOTCHATID")
        # logger.info(f"Notification has been sent with message: `{message}`")
    
    # On vide la liste des nouveaux items
    new_items.clear()

if __name__ == "__main__":

    # On exécute le script directement (test et debugging)
    main()
    
    # On exécute le script tous les jours à 18H00.
    # schedule.every().day.at("18:00").do(main)
    
    # On exécute le script toutes les heures.
    # schedule.every(60).minutes.do(main)
    
    # while True:
    #     schedule.run_pending()
    #     time.sleep(1)
