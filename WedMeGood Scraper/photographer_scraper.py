import time
import json
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from typing import Dict, Any, List

# --- BS4 Parsing Function for Photographer Page (MODIFIED) ---
def parse_photographer_html(html_content: str) -> Dict[str, Any]:
    """
    Parses the HTML content of a single photographer's page and returns a structured dictionary.
    This version relies exclusively on a predefined keyword list to extract services from the text.
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    # --- Name Extraction ---
    name = "N/A"
    name_tag = soup.select_one('h1.h4.text-bold')
    if name_tag:
        name = name_tag.get_text(strip=True)

    # --- Address Extraction ---
    address = "N/A"
    address_div = soup.select_one('div.addr-right h6 > span')
    if address_div:
        address = address_div.get_text(strip=True)

    # --- Pricing Extraction ---
    pricing_info = {}
    price_packages = soup.select('div.VendorPricing .f-space-between.sc-jzJRlG.emSbxZ div > div')
    for package in price_packages:
        label_tag = package.find('h6', class_='text-secondary')
        price_tag = package.find('p', class_='h5')
        unit_tag = package.find('p', class_='regular')
        if label_tag and price_tag:
            key = label_tag.get_text(strip=True).lower().replace(' + ', '_').replace(' ', '_')
            price_text = price_tag.get_text(strip=True).replace(',', '')
            unit_text = unit_tag.get_text(strip=True) if unit_tag else ""
            full_price_string = f"₹{price_text} {unit_text}".strip().replace('\xa0', ' ')
            pricing_info[key] = full_price_string

    additional_prices = soup.select('div.pricing-breakup div.grid__col--1-of-2')
    for item in additional_prices:
        title_tag = item.find('p', class_='text-bold')
        price_spans = item.find_all('span', class_='text-tertiary')
        if title_tag and len(price_spans) > 1:
            key = title_tag.get_text(strip=True).lower().replace('-', '_').replace(' ', '_')
            currency_symbol = price_spans[0].get_text(strip=True)
            value_text = price_spans[1].get_text(strip=True).replace('<!-- -->', '').replace('\xa0', ' ')
            pricing_info[key] = f"{currency_symbol}{value_text}".strip()

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
            if about_p_tag:
                about_text = about_p_tag.get_text(strip=True)
            else:
                about_text = full_details_text # Fallback to full text if no <p> tag

        # Sole Method: Search the full text for an expanded list of keywords.
        if full_details_text:
            PREDEFINED_SERVICES = {
                # Core Services
                "Candid Photography", "Traditional Photography", "Wedding Shoots",
                "Wedding Cinematography", "Cinematic Video", "Wedding Films",
                "Traditional Videography", "Bridal Photography", "Bridal Portraits",
                
                # Pre-Wedding
                "Pre-Wedding Shoots", "Pre-Wedding Films", "Couple Shoots",
                
                # Other Events
                "Engagement Photography", "Maternity Shoots", "Fashion Shoots",
                "Anniversary Shoots", "Newborn Photography", "Baby Shoots",
                
                # Deliverables
                "Albums", "Wedding Albums", "Photo Books", "Digital Albums", "Online Gallery",
                "Drone", "Crane", "Live Streaming", "Same Day Edit", "Teaser Videos", 
                "Highlight Reel", "Photo Booth",
                
                # Styles
                "Photojournalistic", "Fine Art Wedding Photography", "Documentary Photography",
                
                # General
                "Destination Wedding", "Event photography"
            }
            
            found_services = set()
            text_lower = full_details_text.lower()
            
            for service in PREDEFINED_SERVICES:
                if re.search(r'\b' + re.escape(service.lower()) + r'\b', text_lower):
                    # Standardize similar terms to avoid redundancy
                    if "album" in service.lower():
                        found_services.add("Albums")
                    elif any(term in service.lower() for term in ["cinematography", "films", "video"]):
                        if "pre-wedding" in service.lower():
                            found_services.add("Pre-Wedding Films")
                        else:
                            found_services.add("Wedding Cinematography / Films")
                    elif any(term in service.lower() for term in ["bridal photography", "bridal portraits"]):
                        found_services.add("Bridal Portraits")
                    else:
                        found_services.add(service)
            
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
def fetch_and_parse_multiple_urls(urls: List[str], output_filename: str = "photographers_data.json"):
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
    
    all_photographers_data = []

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
                
                photographer_data = parse_photographer_html(html_content)
                photographer_data['source_url'] = url
                
                all_photographers_data.append(photographer_data)
                print(f"-> Successfully parsed data for: {photographer_data.get('name', 'N/A')}")

            except Exception as e:
                print(f"-> FAILED to process URL {url}. Error: {e}")
                continue 

        if not all_photographers_data:
            print("\nNo data was scraped. The output file will not be created.")
            return

        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(all_photographers_data, f, indent=4, ensure_ascii=False)
            
        print("-" * 50)
        print(f"\nSUCCESS: Scraped data from {len(all_photographers_data)} URL(s).")
        print(f"All results have been saved to '{output_filename}'")

    finally:
        print("Closing WebDriver.")
        driver.quit()

# --- Main execution block ---
if __name__ == "__main__":
    target_urls = [
    "https://www.wedmegood.com/profile/Fog-Media-403780",
    "https://www.wedmegood.com/profile/Oaks-Wedding-240964",
    "https://www.wedmegood.com/profile/The-WEDNIX-Studios-6146",
    "https://www.wedmegood.com/profile/ThyWed-Stories-28102",
    "https://www.wedmegood.com/profile/artsylen-101980",
    "https://www.wedmegood.com/profile/The-Wedding-World-4310350",
    "https://www.wedmegood.com/profile/Living-Pixels-by-Ankit-Preksha-Photography-165429",
    "https://www.wedmegood.com/profile/3Knots-Photography-3307937",
    "https://www.wedmegood.com/profile/Shutter-Clicks-169161",
    "https://www.wedmegood.com/profile/lightbucketproductions-16201",
    "https://www.wedmegood.com/profile/Pixel-Chronicles-215098",
    "https://www.wedmegood.com/profile/Shutterbug-Film-Company-417629",
    "https://www.wedmegood.com/profile/Bonds-and-Tales-4566476",
    "https://www.wedmegood.com/profile/Frozen-in-Clicks-35527",
    "https://www.wedmegood.com/profile/The-Wedding-Fellas-713638",
    "https://www.wedmegood.com/profile/Dream-Galaxy-Photography-437532",
    "https://www.wedmegood.com/profile/Pixbricks-107941",
    "https://www.wedmegood.com/profile/Sihi-Moments-by-Siri-Weddings-25638713",
    "https://www.wedmegood.com/profile/Artistic-Pictures-38254",
    "https://www.wedmegood.com/profile/Shoot-At-Sight-Weddings-4600076",
    "https://www.wedmegood.com/profile/The-Shutter-House-435783",
    "https://www.wedmegood.com/profile/Focus-Wala-442728",
    "https://www.wedmegood.com/profile/Fest-India-83762",
    "https://www.wedmegood.com/profile/Pixelena-Studio-37801",
    "https://www.wedmegood.com/profile/HariPhoto-78870",
    "https://www.wedmegood.com/profile/Picsurely-Weddings-42931",
    "https://www.wedmegood.com/profile/North-Water-Star-6024",
    "https://www.wedmegood.com/profile/Journeys-of-Euphoria-47617",
    "https://www.wedmegood.com/profile/Frametastic-647184",
    "https://www.wedmegood.com/profile/The-Shutter-House-435783",
    "https://www.wedmegood.com/profile/Focus-Wala-442728",
    "https://www.wedmegood.com/profile/artsylen-101980",
    "https://www.wedmegood.com/profile/Fest-India-83762",
    "https://www.wedmegood.com/profile/Pixelena-Studio-37801",
    "https://www.wedmegood.com/profile/HariPhoto-78870",
    "https://www.wedmegood.com/profile/Picsurely-Weddings-42931",
    "https://www.wedmegood.com/profile/lightbucketproductions-16201",
    "https://www.wedmegood.com/profile/North-Water-Star-6024",
    "https://www.wedmegood.com/profile/Journeys-of-Euphoria-47617",
    "https://www.wedmegood.com/profile/Frametastic-647184",
    "https://www.wedmegood.com/profile/Mangotree-Photography-389478",
    "https://www.wedmegood.com/profile/Memorylane-Photography-7418",
    "https://www.wedmegood.com/profile/1plus1-Studio-68464",
    "https://www.wedmegood.com/profile/AKV-Photography-210942",
    "https://www.wedmegood.com/profile/Glamour-Photographics-786456",
    "https://www.wedmegood.com/profile/Creative-Chisel-461361",
    "https://www.wedmegood.com/profile/SnapAndVows-2854407",
    "https://www.wedmegood.com/profile/Oyster-Studios-619638",
    "https://www.wedmegood.com/profile/Photo-Alchemy-9717",
    "https://www.wedmegood.com/profile/Arun-Prabhu-Photography-116154",
    "https://www.wedmegood.com/profile/the-wedding-framer-1418443",
    "https://www.wedmegood.com/profile/Shot-by-K-492864",
    "https://www.wedmegood.com/profile/AD-Photography-879670",
    "https://www.wedmegood.com/profile/Click-Madi-625933",
    "https://www.wedmegood.com/profile/Happy-Weddings-553026",
    "https://www.wedmegood.com/profile/weddingcinemas-142067",
    "https://www.wedmegood.com/profile/AJ-Wedding-Studio-484956",
    "https://www.wedmegood.com/profile/SDS-Studio-445445",
    "https://www.wedmegood.com/profile/Journeys-By-Vivek-431649",
    "https://www.wedmegood.com/profile/Cinnamon-Pictures-355781",
    "https://www.wedmegood.com/profile/weddingsfoto-1841583",
    "https://www.wedmegood.com/profile/Patrick-Joseph-Photography-28139",
    "https://www.wedmegood.com/profile/Foto-Jet-Studios-2269321",
    "https://www.wedmegood.com/profile/Amrita-B-Nair-Photography-22375",
    "https://www.wedmegood.com/profile/Thaha-Rayan-Photography-3751400",
    "https://www.wedmegood.com/profile/Creating-Pal-966872",
    "https://www.wedmegood.com/profile/Weddings-by-Alpheus-10499",
    "https://www.wedmegood.com/profile/Saulats-Click-341",
    "https://www.wedmegood.com/profile/BiswaroopDe-Photography-2348780",
    "https://www.wedmegood.com/profile/Sudhir-Damerla-Photography-598202",
    "https://www.wedmegood.com/profile/Paparazzo-Creation-780451",
    "https://www.wedmegood.com/profile/one-horizon-productions-1678572",
    "https://www.wedmegood.com/profile/Frame-Shastra-513163",
    "https://www.wedmegood.com/profile/Classic-Moments-Photography-2936176",
    "https://www.wedmegood.com/profile/Oneiro-by-Anbu-Jawahar-345",
    "https://www.wedmegood.com/profile/Reve-Weddings-4363390",
    "https://www.wedmegood.com/profile/Studio-Shutterspeed-48948",
    "https://www.wedmegood.com/profile/Twin-Flame-Productions-6519",
    "https://www.wedmegood.com/profile/Raj-Photography-2787113",
    "https://www.wedmegood.com/profile/Grey-Media-Production-503274",
    "https://www.wedmegood.com/profile/Gautham-Gopi-Photography-474980",
    "https://www.wedmegood.com/profile/Nishat-Ahmed-9598",
    "https://www.wedmegood.com/profile/Boscos-Photography-48580",
    "https://www.wedmegood.com/profile/MeeraaNaada-Studios-1199572",
    "https://www.wedmegood.com/profile/one-love-films-2221128",
    "https://www.wedmegood.com/profile/lbh-studios-24643452",
    "https://www.wedmegood.com/profile/Suresh-Studio-1142589",
    "https://www.wedmegood.com/profile/Lucky-Malhotra-Photography-and-Films-13955",
    "https://www.wedmegood.com/profile/ConsciouSpace-166825",
    "https://www.wedmegood.com/profile/Anu-Jacob-Photography-71706",
    "https://www.wedmegood.com/profile/WeddingRaja-28101",
    "https://www.wedmegood.com/profile/Wedding-Photography-by-Raj-RJ-30859",
    "https://www.wedmegood.com/profile/Hanging-Crystals-Events-2523187",
    "https://www.wedmegood.com/profile/wtfun-bro-studios-1445671",
    "https://www.wedmegood.com/profile/SK-Dhananjay-Photography-743546"
]

    
    fetch_and_parse_multiple_urls(urls=target_urls)