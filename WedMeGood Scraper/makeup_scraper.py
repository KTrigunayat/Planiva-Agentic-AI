import time
import json
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from typing import Dict, Any, List

# --- BS4 Parsing Function for Makeup Artist Page (Corrected) ---
def parse_makeup_artist_html(html_content: str) -> Dict[str, Any]:
    """
    Parses the HTML content of a single makeup artist's page and returns a structured dictionary.
    This version includes corrected logic for accurately parsing all pricing information.
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    # --- Name and Address Extraction ---
    name = soup.select_one('h1.h4.text-bold').get_text(strip=True) if soup.select_one('h1.h4.text-bold') else "N/A"
    address = soup.select_one('div.addr-right h6 > span').get_text(strip=True) if soup.select_one('div.addr-right h6 > span') else "N/A"

    # --- Pricing Extraction ---
    pricing_info = {}
    
    # 1. Extract the main bridal makeup price
    main_price_section = soup.select_one('div.VendorPricing div.f-space-between.sc-jzJRlG.emSbxZ')
    if main_price_section:
        price_tag = main_price_section.find('p', class_='h5')
        unit_tag = main_price_section.find('p', class_='regular')
        label_tag = main_price_section.find('h6', class_='regular')
        
        if label_tag and price_tag:
            key = label_tag.get_text(strip=True).lower().replace(' ', '_')
            price_val = price_tag.get_text(strip=True).replace(',', '')
            unit_val = unit_tag.get_text(strip=True).replace('\xa0', ' ').strip() if unit_tag else ""
            pricing_info[key] = f"₹{price_val} {unit_val}".strip()

    # 2. Extract additional prices from the "Pricing Info" dropdown
    additional_prices = soup.select('div.pricing-breakup div.grid__col--1-of-2')
    for item in additional_prices:
        title_tag = item.find('p', class_='text-bold')
        price_spans = item.find_all('span', class_='text-tertiary')
        
        if title_tag and len(price_spans) > 0:
            key = title_tag.get_text(strip=True).lower().replace('-', '_').replace(' ', '_')
            full_price_text = "".join(span.get_text(strip=True).replace('<!-- -->', '').replace('\xa0', ' ') for span in price_spans)
            
            match = re.match(r'₹([\d,]+)(.*)', full_price_text.strip())
            if match:
                value = match.group(1).strip()
                unit = match.group(2).strip()
                pricing_info[key] = f"₹{value} {unit}".strip()

    # --- Details Extraction (About & Services) ---
    about_text = "N/A"
    services_offered = []
    
    about_section = soup.find('div', class_='AboutSection')
    if about_section:
        full_details_text = ""
        info_div = about_section.find('div', class_='info')
        if info_div:
            full_details_text = info_div.get_text(separator=' ', strip=True)
            about_p_tag = info_div.find('p')
            about_text = about_p_tag.get_text(strip=True) if about_p_tag else full_details_text

        if full_details_text:
            PREDEFINED_SERVICES = {
                "Bridal Makeup", "Engagement Makeup", "Party Makeup", "Family Makeup", "Roka", 
                "Mehendi", "Receptions", "HD Makeup", "Airbrush Makeup", "Waterproof Makeup",
                "Sweat-resistant", "Glam Makeup", "Natural Makeup", "Draping", "Hair Styling",
                "False Lashes", "Extensions", "Chic hairstyles", "Travels to venue", "Paid trial"
            }
            found_services = set()
            text_lower = full_details_text.lower()
            for service in PREDEFINED_SERVICES:
                if re.search(r'\b' + re.escape(service.lower()) + r'\b', text_lower):
                    found_services.add(service.strip())
            services_offered = sorted(list(found_services))

    # --- Final JSON Structure ---
    return {
        "name": name,
        "location": address,
        "pricing": pricing_info,
        "details": {
            "about": about_text,
            "services_offered": services_offered
        }
    }

# --- Main Selenium Function to Fetch and Parse Multiple URLs ---
def fetch_and_parse_multiple_urls(urls: List[str], output_filename: str = "all_artists_data.json"):
    """
    Initializes a single WebDriver instance to navigate to a list of URLs,
    fetches the HTML for each, parses the data using BeautifulSoup, and saves all
    results into a single JSON file.
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
    
    all_artists_data = []

    try:
        for i, url in enumerate(urls):
            print("-" * 50)
            print(f"Processing URL {i+1}/{len(urls)}: {url}")
            
            try:
                driver.get(url)
                wait_time = 8 
                print(f"Waiting for {wait_time} seconds for dynamic content...")
                time.sleep(wait_time)
                
                print("Retrieving and parsing HTML...")
                html_content = driver.page_source
                
                artist_data = parse_makeup_artist_html(html_content)
                artist_data['source_url'] = url # Add the source URL for reference
                
                all_artists_data.append(artist_data)
                print(f"-> Successfully parsed data for: {artist_data.get('name', 'N/A')}")

            except Exception as e:
                print(f"-> FAILED to process URL {url}. Error: {e}")
                continue 

        if not all_artists_data:
            print("\nNo data was scraped. The output file will not be created.")
            return

        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(all_artists_data, f, indent=4, ensure_ascii=False)
            
        print("-" * 50)
        print(f"\nSUCCESS: Scraped data from {len(all_artists_data)} URL(s).")
        print(f"All results have been saved to '{output_filename}'")

    finally:
        print("Closing WebDriver.")
        driver.quit()

# --- Main execution block ---
if __name__ == "__main__":
    # --- PASTE THE LIST OF URLs YOU WANT TO SCRAPE HERE ---
    target_urls = [
    "https://www.wedmegood.com/profile/Anu-Chugh-57692",
    "https://www.wedmegood.com/profile/Makeup-by-Disha-701940",
    "https://www.wedmegood.com/profile/Makeup-by-Sweta-233084",
    "https://www.wedmegood.com/profile/varsha-s-214993",
    "https://www.wedmegood.com/profile/Vaibhav-Makeovers-1058877",
    "https://www.wedmegood.com/profile/Brushes-and-Lashes-115363",
    "https://www.wedmegood.com/profile/Parul-Khattar-Makeup-Artist-33244",
    "https://www.wedmegood.com/profile/Aura-by-Tama-Debb-443644",
    "https://www.wedmegood.com/profile/Makeup-by-Areebah-Gani-1942534",
    "https://www.wedmegood.com/profile/Makeup-By-Dev-216039",
    "https://www.wedmegood.com/profile/Dhanya-Raghavan-780054",
    "https://www.wedmegood.com/profile/Mohtarma-Makeup-by-somya-agrawal-248358",
    "https://www.wedmegood.com/profile/aadvika-makeovers-1838788",
    "https://www.wedmegood.com/profile/Rajz-Makeup-Artist-and-Hair-Stylist-1193108",
    "https://www.wedmegood.com/profile/Makeup-By-Suparna-412242",
    "https://www.wedmegood.com/profile/PC-Makeover-Studio-24599993",
    "https://www.wedmegood.com/profile/Brides-and-Sides-846741",
    "https://www.wedmegood.com/profile/Flawless-Makeover-With-Namratha-Sunil-25654075",
    "https://www.wedmegood.com/profile/Veda-Ragavendra-Artistry-4749015",
    "https://www.wedmegood.com/profile/ibbu-makeup-1821987",
    "https://www.wedmegood.com/profile/Brush-and-Blush-by-Ganavi-Gr-Gowda-674874",
    "https://www.wedmegood.com/profile/Surbhi-Varma-Makeup-and-Hair-204516",
    "https://www.wedmegood.com/profile/Kulsum-Parvez-Bridal-Makeup-5985",
    "https://www.wedmegood.com/profile/Artistry-by-Priya-Harsha-417024",
    "https://www.wedmegood.com/profile/Kislaya-Sinha-Makeup-1828037",
    "https://www.wedmegood.com/profile/V2-Makeover-2613859",
    "https://www.wedmegood.com/profile/Makeovers-by-Sudhanatesh-245767",
    "https://www.wedmegood.com/profile/Makeover-with-Monika-Gowda-24950527",
    "https://www.wedmegood.com/profile/Makeup-by-Magicbrush-2161923",
    "https://www.wedmegood.com/profile/Makeup-by-Divya-3212630",
    "https://www.wedmegood.com/profile/Makeup-by-Yashaswini-692326",
    "https://www.wedmegood.com/profile/Makeup-by-Anushka-Kukreja-244960",
    "https://www.wedmegood.com/profile/Get-Sparkled-by-Aenaz-Khan-572464",
    "https://www.wedmegood.com/profile/Dawn-Tobin-16868",
    "https://www.wedmegood.com/profile/Makeup-Artistry-by-Mousumi-549826",
    "https://www.wedmegood.com/profile/Makeover-By-Sunitha-Behura-241620",
    "https://www.wedmegood.com/profile/Makup-by-Heeer-Achpal-30323",
    "https://www.wedmegood.com/profile/Mua-Poonam-Jain-25600521",
    "https://www.wedmegood.com/profile/Bhavani-Kumar-83665",
    "https://www.wedmegood.com/profile/Get-Glam-With-Ayesha-3253559",
    "https://www.wedmegood.com/profile/Snigdha-Beauty-Studio-and-Academy-1763312",
    "https://www.wedmegood.com/profile/Geetha-Sampath-Makeup-Artist-403162",
    "https://www.wedmegood.com/profile/Brides-by-Sandy-940750",
    "https://www.wedmegood.com/profile/Aditi-Raman-507186",
    "https://www.wedmegood.com/profile/Monalisa-281173",
    "https://www.wedmegood.com/profile/Bhavya-Santosh-490661",
    "https://www.wedmegood.com/profile/Makeup-artist-zohara-shereen-59264",
    "https://www.wedmegood.com/profile/Embellish-by-Deepthi-612476",
    "https://www.wedmegood.com/profile/Glitz-by-Vaibhavi-426167",
    "https://www.wedmegood.com/profile/Makeup-Stories-by-Amrita-Durg-1850159",
    "https://www.wedmegood.com/profile/Beauty-by-Preeti-24269374",
    "https://www.wedmegood.com/profile/Achu-Artistry-1655205",
    "https://www.wedmegood.com/profile/Makeover-by-Priyanka-Sohan-25175511",
    "https://www.wedmegood.com/profile/Makeovers-by-Mahalakshmi-578112",
    "https://www.wedmegood.com/profile/artistry-chronicles-1744309",
    "https://www.wedmegood.com/profile/Makover-By-Shyla-Deepthi-3115117",
    "https://www.wedmegood.com/profile/Azmi-Glitz-Makeup-Artistry-184759",
    "https://www.wedmegood.com/profile/Sakshi-M-Banthia-4301223",
    "https://www.wedmegood.com/profile/Makeovers-By-Amitha-and-Lekha-519526",
    "https://www.wedmegood.com/profile/For-the-Love-of-Makeup-13644",
    "https://www.wedmegood.com/profile/Makeup-by-Shwetha-Chandu-371148",
    "https://www.wedmegood.com/profile/Artistry-By-Carmel-25509614",
    "https://www.wedmegood.com/profile/Siddiqua-Tarannum-Makeovers-1174918",
    "https://www.wedmegood.com/profile/Makeup-by-Chandrakala-Ravindran-411557",
    "https://www.wedmegood.com/profile/Makeup-Artist-Meghana-414420",
    "https://www.wedmegood.com/profile/Preeti-Punjabi-makeup-artist-n-hair-stylist-174242",
    "https://www.wedmegood.com/profile/Makeup-by-Rekha-B-Ramesh-390430",
    "https://www.wedmegood.com/profile/Makeup-by-Deepika-2120829",
    "https://www.wedmegood.com/profile/Elevate-Glam-Studio-25374061",
    "https://www.wedmegood.com/profile/Smriti-MUA-24668564",
    "https://www.wedmegood.com/profile/Strokes-and-Strands-3192236",
    "https://www.wedmegood.com/profile/rzee-makeovers-by-sofi-1569032",
    "https://www.wedmegood.com/profile/Makeover-by-Shwetha-Murali-178209",
    "https://www.wedmegood.com/profile/Blush-n-Blend-Makeover-24377289",
    "https://www.wedmegood.com/profile/Glam-Makeover-Guru-Chandana-Deepak-422283",
    "https://www.wedmegood.com/profile/Makeup-by-Kanika-526934",
    "https://www.wedmegood.com/profile/Diva-With-Deewa-442253",
    "https://www.wedmegood.com/profile/Priyanka-Sarmacharjee-402810",
    "https://www.wedmegood.com/profile/Makeover-by-Sahana-Shetty-4369212",
    "https://www.wedmegood.com/profile/Makeover-by-Aishwarya-Bharathraj-2641416",
    "https://www.wedmegood.com/profile/Nikki-Neeladri-12396",
    "https://www.wedmegood.com/profile/Makeup-by-Sumeeta-and-Namratha-468272",
    "https://www.wedmegood.com/profile/Makeup-by-Sahana-and-Kavya-1184476",
    "https://www.wedmegood.com/profile/Tejashree-Raj-Mua-2715020",
    "https://www.wedmegood.com/profile/makeup-artist-44528",
    "https://www.wedmegood.com/profile/Makeover-with-Pavi-1588994",
    "https://www.wedmegood.com/profile/Makeup-by-Haani-857324",
    "https://www.wedmegood.com/profile/Nadiya-Khan-Makeup-Artist-1416902",
    "https://www.wedmegood.com/profile/Makeovers-by-Sarayu-509806",
    "https://www.wedmegood.com/profile/Aarthies-Makeover-919077",
    "https://www.wedmegood.com/profile/amrita-jaiswal-makeup-25490513",
    "https://www.wedmegood.com/profile/The-Scarlet-Makeover-2588092",
    "https://www.wedmegood.com/profile/Shachi-Singh-124604",
    "https://www.wedmegood.com/profile/Twinkling-Makeup-Studio-528646",
    "https://www.wedmegood.com/profile/Raaga-MUA-1375820",
    "https://www.wedmegood.com/profile/Makeover-by-Susheela-25479780",
    "https://www.wedmegood.com/profile/Makeup-by-Mayuri-58083",
    "https://www.wedmegood.com/profile/Blush-Berry-Makeovers-2600518",
    "https://www.wedmegood.com/profile/Make-up-by-Tarika-Rajanna-629602",
    "https://www.wedmegood.com/profile/Makeup-by-Bhanu-416570",
    "https://www.wedmegood.com/profile/Lekha-and-Meghana-Bridal-Makeup--709",
    "https://www.wedmegood.com/profile/Makeup-by-Surabhi-Rajanna-1457763",
    "https://www.wedmegood.com/profile/Naaz-Makeover-583630",
    "https://www.wedmegood.com/profile/Makeup-by-Shreajha-1495106",
    "https://www.wedmegood.com/profile/Radiant-Beauty-611051",
    "https://www.wedmegood.com/profile/Velvet-Mizzle-227443",
    "https://www.wedmegood.com/profile/Makeover-by-Preethi-Naidu-3964656",
    "https://www.wedmegood.com/profile/Pooja-Arya-MUA-2931656",
    "https://www.wedmegood.com/profile/Mitali-Jain-Makeup-artist-1875171",
    "https://www.wedmegood.com/profile/Fusion-Makeup-586715",
    "https://www.wedmegood.com/profile/makeovers-by-gabriel-martha-115522",
    "https://www.wedmegood.com/profile/Meghana-MUA-577304"
]

    
    fetch_and_parse_multiple_urls(urls=target_urls)