import time
import os
import json
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional, List

# --- BS4 Helper Function (No changes) ---
def convert_price_to_int(price_text: str) -> Optional[int]:
    """
    Cleans a price string (e.g., "₹499<!-- -->&nbsp;") and converts it to an integer.
    Returns None if no digits are found.
    """
    if not price_text:
        return None
    
    price_digits = re.findall(r'\d+', price_text)
    
    if not price_digits:
        return None
        
    return int("".join(price_digits))

# --- BS4 Parsing Function (MODIFIED) ---
def parse_caterer_html(html_content: str) -> Dict[str, Any]:
    """
    Parses the HTML content of a single caterer page and returns a structured dictionary.
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    # --- Name Extraction ---
    name = "N/A"
    vendor_details_div = soup.select_one('div.vendor-details')
    if vendor_details_div:
        name_tag = vendor_details_div.find('h1')
        if name_tag:
            name = name_tag.get_text(strip=True)

    # --- Address Extraction ---
    address = "N/A"
    address_div = soup.select_one('div.addr-right')
    if address_div:
        address_span = address_div.find('span')
        if address_span:
            address = address_span.get_text(strip=True)

    # --- Pricing Extraction ---
    pricing_info = {}
    price_title_tags = soup.select('div.grid__col p.text-bold')
    for tag in price_title_tags:
        key = tag.get_text(strip=True).lower().replace(' ', '_')
        price_spans = tag.parent.find_all('span', class_='text-tertiary')
        if len(price_spans) > 1:
            pricing_info[key] = convert_price_to_int(price_spans[1].text)

    price_label_containers = soup.find_all('div', class_='frow')
    for container in price_label_containers:
        container_text = container.get_text(strip=True).lower()
        price_tag = container.find('p', class_='h5')
        if not price_tag:
            continue
        
        if 'veg price per plate' in container_text:
            pricing_info['veg_price_per_plate'] = convert_price_to_int(price_tag.text)
        elif 'non veg price per plate' in container_text:
            pricing_info['non_veg_price_per_plate'] = convert_price_to_int(price_tag.text)

    # --- Caterer Details Extraction ---
    about_text = None
    full_details_text = ""
    cuisines_set = set() 
    
    # --- The Master List of Cuisines to search for ---
    PREDEFINED_CUISINES = {
        "North Indian", "South Indian", "Chinese", "Italian", "Thai",
        "Desserts", "Rajasthani", "Maharashtrian", "Gujarati", "Bengali", "Japanese"
    }
    
    about_body = soup.find('div', class_='about-body border-t')
    
    if about_body:
        # --- Step 1: Extract all text from the relevant section ---
        info_div = about_body.find('div', class_='info padding-h-20 padding-v-20')
        if info_div:
            full_details_text = info_div.get_text(separator='\n', strip=True)
            
            # Cleanly extract the "About" text by splitting it from the cuisine list if present
            if re.search(r'Cuisines offered', full_details_text, re.IGNORECASE):
                about_text = re.split(r'Cuisines offered:?', full_details_text, flags=re.IGNORECASE, maxsplit=1)[0].strip()
            else:
                about_text = full_details_text
        
        # --- Step 2: Apply the Strict Rule-Based Approach ---
        # Search the extracted text for matches from our master list.
        if full_details_text:
            text_lower = full_details_text.lower()
            for cuisine in PREDEFINED_CUISINES:
                # Check if the predefined cuisine (e.g., "north indian") is in the text
                if cuisine.lower() in text_lower:
                    cuisines_set.add(cuisine) # Add the correctly capitalized version

    # --- Final JSON Structure ---
    return {
        "name": name,
        "location": address,
        "pricing": pricing_info,
        "details": {
            "about": about_text,
            "cuisines": sorted(list(cuisines_set)) 
        }
    }

# --- Selenium Function for Multiple URLs (No changes) ---
def fetch_and_parse_multiple_urls(urls: List[str], output_filename: str = "caterers_data.json"):
    """
    Initializes a single WebDriver instance to navigate to a list of URLs, 
    fetches the HTML for each, parses the data, and saves all results
    into a single JSON file.
    """
    print("Setting up WebDriver...")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    print(f"WebDriver setup complete.")
    
    all_caterers_data = []

    try:
        for i, url in enumerate(urls):
            print("-" * 50)
            print(f"Processing URL {i+1}/{len(urls)}: {url}")
            
            try:
                driver.get(url)
                wait_time = 8 
                print(f"Waiting for {wait_time} seconds...")
                time.sleep(wait_time)
                
                print("Retrieving and parsing HTML...")
                html_content = driver.page_source
                caterer_data = parse_caterer_html(html_content)
                
                caterer_data['source_url'] = url
                
                all_caterers_data.append(caterer_data)
                print(f"-> Successfully parsed data for: {caterer_data.get('name', 'N/A')}")

            except Exception as e:
                print(f"-> FAILED to process URL {url}. Error: {e}")
                continue

        if not all_caterers_data:
            print("\nNo data was scraped. The output file will not be created.")
            return

        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(all_caterers_data, f, indent=4, ensure_ascii=False)
            
        print("-" * 50)
        print(f"\nSUCCESS: Scraped data from {len(all_caterers_data)} URLs.")
        print(f"All results have been saved to '{output_filename}'")

    finally:
        print("Closing WebDriver.")
        driver.quit()

# --- Main Execution Block ---
if __name__ == "__main__":
    # --- IMPORTANT: PASTE THE CATERER'S URLs HERE ---
    target_urls = [
        "https://www.wedmegood.com/profile/Aahara-by-Siri-Weddings-25638716",
"https://www.wedmegood.com/profile/Sri-Annapoorneshwari-Catering-Services-in-Bangalore-411732",
"https://www.wedmegood.com/profile/herbs-and-spices-25885246",
"https://www.wedmegood.com/profile/Bliss-Catering-25208021",
"https://www.wedmegood.com/profile/a-v-caterers-24472221",
"https://www.wedmegood.com/profile/Kailash-Caterers-24992596",
"https://www.wedmegood.com/profile/All-India-Caterers-729451",
"https://www.wedmegood.com/profile/SS-Caterers-3253032",
"https://www.wedmegood.com/profile/MK-Your-Food-Destination-587986",
"https://www.wedmegood.com/profile/TechFork-129350",
"https://www.wedmegood.com/profile/Chefworks-25756346",
"https://www.wedmegood.com/profile/Masala-Mantraa-25470580",
"https://www.wedmegood.com/profile/The-BBQ-Catering-Company-4637718",
"https://www.wedmegood.com/profile/Bhojon-Roshik-Catering-Service-25623178",
"https://www.wedmegood.com/profile/Zigzag-Caterers-1068760",
"https://www.wedmegood.com/profile/Brahmi-Caterers-2529480",
"https://www.wedmegood.com/profile/Yoss-Hospitality-24736640",
"https://www.wedmegood.com/profile/Aroma-Wedding-caterer-19322",
"https://www.wedmegood.com/profile/Heera-Caterers-19163",
"https://www.wedmegood.com/profile/Ganis-Team-17249",
"https://www.wedmegood.com/profile/Ashirwad-Caterers-468200",
"https://www.wedmegood.com/profile/1947-Restaurant-Hennur-25015208",
"https://www.wedmegood.com/profile/Hanging-Crystals-Events-25640956",
"https://www.wedmegood.com/profile/Dindayal-Caterers-25515113",
"https://www.wedmegood.com/profile/Sri-Mookabika-Catering-Services-645445",
"https://www.wedmegood.com/profile/Pulse-Hospitality-24694428",
"https://www.wedmegood.com/profile/bbq-at-your-home-4519314",
"https://www.wedmegood.com/profile/BKG-Caterers-3288522",
"https://www.wedmegood.com/profile/Sri-Sai-Cuisines-1139782",
"https://www.wedmegood.com/profile/satayboyz-1385949",
"https://www.wedmegood.com/profile/rajwadi-caterers-bangalore-1899747",
"https://www.wedmegood.com/profile/Anisas-Kitchen-22962",
"https://www.wedmegood.com/profile/Narmada-Caterers-500343",
"https://www.wedmegood.com/profile/Balaji-Caterers-24758365",
"https://www.wedmegood.com/profile/pavithram-2651177",
"https://www.wedmegood.com/profile/Prakash-Caterers-403313",
"https://www.wedmegood.com/profile/Barbeque-Nation-424419",
"https://www.wedmegood.com/profile/Sri-Lakshmi-Narayan-Group-of-Catering-480458",
"https://www.wedmegood.com/profile/Button-Caterers-939851",
"https://www.wedmegood.com/profile/Torry-Harris-Restaurants-Pvt-ltd-605135",
"https://www.wedmegood.com/profile/Sagar-Caterers-19146",
"https://www.wedmegood.com/profile/Sri-Mayyia-Caterers-19140",
"https://www.wedmegood.com/profile/MSC-Cantering-Service-25872879",
"https://www.wedmegood.com/profile/PME-Events-Catering-1628694",
"https://www.wedmegood.com/profile/Foodiekapital-Caterers-24758090",
"https://www.wedmegood.com/profile/Billionsmiles-Hospitality-Pvt-Ltd-15784",
"https://www.wedmegood.com/profile/begum-paan-3047931",
"https://www.wedmegood.com/profile/Lucky-Tummy-431556",
"https://www.wedmegood.com/profile/Torry-Harris-Restaurent-Pvt-Ltd-763478",
"https://www.wedmegood.com/profile/Staytrendz-Events-246722",
"https://www.wedmegood.com/profile/Catering-inn-17255",
"https://www.wedmegood.com/profile/Sami-Caterers-3853513",
"https://www.wedmegood.com/profile/India-Kitchen-4512046",
"https://www.wedmegood.com/profile/goodlife-hospitality-24371320",
"https://www.wedmegood.com/profile/Smart-Chef-Catering-3059839",
"https://www.wedmegood.com/profile/Kvr-Foods-and-Caterers-4360111",
"https://www.wedmegood.com/profile/Sri-Aishwarya-Caterers-715082",
"https://www.wedmegood.com/profile/Sar-Catering-1808268",
"https://www.wedmegood.com/profile/Maa-Savitri-Caterers-688310",
"https://www.wedmegood.com/profile/Masterchef-Caterers-406799",
"https://www.wedmegood.com/profile/Adayar-Anadha-Bhavan-A2B-25785164",
"https://www.wedmegood.com/profile/MNJ-Groups-3524172",
"https://www.wedmegood.com/profile/s-m-caterers-3967198",
"https://www.wedmegood.com/profile/Suvaii-A-Pandyan-Legacy-25406338",
"https://www.wedmegood.com/profile/Green-Leaf-Catering-Services-691546",
"https://www.wedmegood.com/profile/Crowns-Catering-Services-2865689",
"https://www.wedmegood.com/profile/The-Royal-Caterers-And-Eventers-3130861",
"https://www.wedmegood.com/profile/A2s-Rasoi-860350",
"https://www.wedmegood.com/profile/Govind-Caterers-19221",
"https://www.wedmegood.com/profile/54-Gully-Kitchen-1582224",
"https://www.wedmegood.com/profile/Kalas-Kitchen-509968",
"https://www.wedmegood.com/profile/Diamond-Catering-245934",
"https://www.wedmegood.com/profile/Hallimane-Catering-4581738",
"https://www.wedmegood.com/profile/Mangalya-Caterers-3555462",
"https://www.wedmegood.com/profile/sarvam-upahar-25178200",
"https://www.wedmegood.com/profile/Peacock-Caterers-24638470",
"https://www.wedmegood.com/profile/Sri-Devi-Caterers-3524085",
"https://www.wedmegood.com/profile/Swad-Signal-3059819",
"https://www.wedmegood.com/profile/UK-Udupi-Caterers-672624",
"https://www.wedmegood.com/profile/SFM-Caterers-558573"
    ]
    
    fetch_and_parse_multiple_urls(urls=target_urls)