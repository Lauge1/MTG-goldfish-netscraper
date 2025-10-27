#net scraper for MTG card prices to use in data analysis
import requests
from bs4 import BeautifulSoup
import pandas as pd
import urllib.parse
import unicodedata
import re

total_price = 0

def load_Cards_from_excel(file_path):
    df = pd.read_excel(file_path)
    df['Card Name'] = df['Card Name'].astype(str).str.replace(',', '', regex=False).str.replace('-', ' ', regex=False)# Remove commas from card names, convert hyphens to spaces, keep special characters
    df['Set Name'] = df['Set Name'].astype(str).str.replace(':', '', regex=False).str.replace('-', ' ', regex=False)# Remove colons from set names, convert hyphens to spaces, keep other special characters
    return list(zip(df['Card Name'], df['Set Name'])) # Return both card names and set names as a list of tuples

def find_Card_information(url, card_name, set_name):
    global total_price
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Referer': 'https://www.google.com/'
    }
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            if response.status_code == 404:
                print(f"{card_name} ({set_name}): Card not found (404) at URL:", url)
                # why is the card name already lower case but not in the url?
                words = card_name.title().split()
                newList = []
                for word in words:
                    newList.append(word.lower())                   
                words = newList[0].capitalize() + ' ' + ' '.join(newList[1:])
                #need to rerun html request here to get the real result if above note can't fix it
                return
            else: print(f"{card_name} ({set_name}): HTTP error {response.status_code}")
            return
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        price_box = soup.find('div', class_='price-box-container')
        if price_box:
            price_span = price_box.find('div', class_='price-box-price')
            if price_span:
                price_text = price_span.get_text(strip=True)
                price_numbers = re.findall(r'\d+\.\d+|\d+', price_text)
                if price_numbers:
                    price_value = float(price_numbers[0])
                    total_price += price_value
                    print(f"{card_name} ({set_name}): {price_value}")
                else:
                    print(f"{card_name} ({set_name}): Price not found")
            else:
                print("Price not found.")
        else:
            print("Price box not found.")
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

def normalize_special_characters(text):
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')# Replace special characters with their closest ASCII equivalent
    text = text.replace("'", "") # Remove apostrophes and convert hyphens to spaces
    return text.replace('-', ' ')

def title_case_for_url(text):
    text = normalize_special_characters(text)
    words = text.title().split()
    result = []
    for i, w in enumerate(words):
        if i == 0:
            result.append(w)  # Always capitalize the first word
        elif w.lower() in ['of', 'the']:
            result.append(w.lower())
        else:
            result.append(w)
    return ' '.join(result)

excel_path = '' #Enter file path here
card_info_list = load_Cards_from_excel(excel_path)

base_url = 'https://www.mtggoldfish.com/price/{set}/{card}#paper' # URL HTTP creation for goldfish

for card_name, set_name in card_info_list:
    card_url_name = urllib.parse.quote_plus(title_case_for_url(str(card_name)))
    set_url_name = urllib.parse.quote_plus(title_case_for_url(str(set_name)))
    target_url = base_url.format(set=set_url_name, card=card_url_name)
    find_Card_information(target_url, card_name, set_name)

print(f"Total price in $: {total_price}")
