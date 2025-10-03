import json
import time
import re
from pathlib import Path
from typing import Dict, Any, Optional
from urllib.parse import urlparse

# Selenium Imports
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# BeautifulSoup Import
from bs4 import BeautifulSoup

# --- BeautifulSoup Helper Function ---
def convert_price_to_int(price_text: str) -> Optional[int]:
    """
    Converts a price string (e.g., "1,50,000", "₹15.00 Lakhs") into an integer.
    Returns None if conversion fails.
    """
    if not price_text:
        return None
    
    price_text = price_text.replace('₹', '').strip()
    numeric_part_search = re.search(r'[\d,]+\.?\d*', price_text)
    if not numeric_part_search:
        return None
        
    numeric_part = numeric_part_search.group(0).replace(',', '')
    number = float(numeric_part)
    
    lower_text = price_text.lower()
    if 'lakh' in lower_text:
        return int(number * 100000)
    elif 'crore' in lower_text:
        return int(number * 10000000)
    else:
        return int(number)


class HybridScraper:
    def __init__(self, debug: bool = True):
        self.debug = debug
        self.debug_dir = Path("debug_html")
        self.debug_dir.mkdir(exist_ok=True)
        self.driver = self._setup_driver()
        
    def _setup_driver(self):
        """Set up and configure the Chrome WebDriver."""
        print("Setting up WebDriver...")
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("WebDriver setup complete.")
        return driver
    
    def _save_debug_file(self, content: str, filename: str):
        """Save content to a debug file if debug mode is enabled."""
        if self.debug:
            filepath = self.debug_dir / f"{int(time.time())}_{filename}"
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return filepath
        return None

    def scrape_venue(self, url: str) -> Dict[str, Any]:
        """Scrapes venue information from a URL using BeautifulSoup on rendered HTML."""
        if not urlparse(url).scheme:
            print(f"Error: Invalid URL provided: {url}")
            return {}
            
        print(f"Loading page: {url}")
        try:
            self.driver.get(url)
            time.sleep(5)
            
            html_content = self.driver.page_source
            self._save_debug_file(html_content, 'rendered_page.html')
            
            print("Using BeautifulSoup to parse the rendered HTML.")
            venue_data = self._parse_html_with_bs4(html_content)
            
            if not venue_data or not venue_data.get("name") or venue_data.get("name") == "N/A":
                print("Error: HTML parsing failed to extract meaningful data.")
                return {}
            
            return venue_data
            
        except Exception as e:
            print(f"An unexpected error occurred during scraping: {e}")
            return {}

    def _parse_html_with_bs4(self, html_content: str) -> Dict[str, Any]:
        """Parses the rendered HTML content using BeautifulSoup to extract venue details."""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        name_tag = soup.find('title')
        name = name_tag.text.split('|')[0].strip() if name_tag else "N/A"

        address_tag = soup.find('div', class_='addr-right')
        address = address_tag.text.strip() if address_tag else "N/A"

        pricing_info = {}
        vendor_pricing_container = soup.find('div', class_='VendorPricing')
        if vendor_pricing_container:
            # Patterns 1 & 2: Veg/Non-Veg, Decor
            for div in vendor_pricing_container.find_all('div', class_='f-space-between'):
                if 'Veg price' in div.text:
                    veg_tag = div.find('p', class_='h5')
                    if veg_tag: pricing_info['veg_price_per_plate'] = convert_price_to_int(veg_tag.text)
                if 'Non Veg price' in div.text:
                    non_veg_tag = div.find('p', class_='h5')
                    if non_veg_tag: pricing_info['non_veg_price_per_plate'] = convert_price_to_int(non_veg_tag.text)
            
            decor_price_title = vendor_pricing_container.find('p', string='Starting Price of Decor')
            if decor_price_title:
                price_spans = decor_price_title.find_next_siblings('span')
                if len(price_spans) > 1:
                    pricing_info['starting_price_decor'] = convert_price_to_int(price_spans[1].text)
            
            # --- MODIFICATION START: MORE ROBUST RENTAL COST PATTERN ---
            # Pattern 3: Rental Cost / Price per function
            # This approach finds all potential price containers and checks their cleaned text.
            # This correctly handles cases with HTML comments or extra whitespace around the label.
            price_containers = vendor_pricing_container.find_all('div', class_='frow')
            for container in price_containers:
                container_text = container.get_text(strip=True).lower()
                if 'rental cost' in container_text or 'per function' in container_text:
                    price_tag = container.find('p', class_='h5')
                    if price_tag:
                        pricing_info['rental_cost'] = convert_price_to_int(price_tag.text)
                        break 
            # --- MODIFICATION END ---

        # Pattern 4: Destination Wedding Price
        dest_wedding_container = soup.find('div', class_='DestinationWeddingPricing')
        if dest_wedding_container:
            price_tag = dest_wedding_container.find('div', class_='price')
            if price_tag:
                pricing_info['destination_wedding_price'] = convert_price_to_int(price_tag.text)
        
        capacity = []
        areas_available = soup.find('div', class_='AreasAvailable')
        if areas_available:
            for area in areas_available.find_all(class_='flex-50'):
                details = {}
                seating_floating = area.find('h6')
                if seating_floating and '|' in seating_floating.text:
                    parts = seating_floating.text.split('|')
                    details['seating'] = int(re.search(r'\d+', parts[0]).group()) if re.search(r'\d+', parts[0]) else None
                    details['floating'] = int(re.search(r'\d+', parts[1]).group()) if len(parts) > 1 and re.search(r'\d+', parts[1]) else None
                
                details['area'] = area.find('p').text.strip() if area.find('p') else "N/A"
                details['type'] = area.find('div', class_='small').text.strip() if area.find('div', class_='small') else "N/A"
                capacity.append(details)
                
        policies = {}
        room_count = None
        about_section = soup.find('div', class_='AboutSection')
        if about_section and about_section.find('div', class_='faqs'):
            faqs = about_section.find('div', class_='faqs')
            policy_map = {'Catering policy': 'catering', 'Decor Policy': 'decor', 'Outside Alcohol': 'alcohol', 'DJ Policy': 'dj'}
            for title, key in policy_map.items():
                tag = faqs.find('p', string=title)
                if tag and tag.find_next_sibling('p'): policies[key] = tag.find_next_sibling('p').text.strip()

            room_tag = faqs.find('p', string='Room Count')
            if room_tag and room_tag.find_next_sibling('p'):
                room_text = room_tag.find_next_sibling('p').text
                room_digits = re.search(r'\d+', room_text)
                if room_digits: room_count = int(room_digits.group(0))

        return {
            "name": name,
            "location": address,
            "pricing": pricing_info,
            "capacity": capacity,
            "policies": policies,
            "room_count": room_count,
            "source_url": self.driver.current_url
        }

    def close(self):
        """Close the WebDriver."""
        if hasattr(self, 'driver'):
            self.driver.quit()

def main():
    """Main function to run the scraper."""
    urls_to_scrape = [
        "https://www.wedmegood.com/wedding-venues/Fiestaa-Resort-n-Events-Venue-409062",

]
    
    all_venues_data = []
    scraper = HybridScraper(debug=True)
    
    try:
        for url in urls_to_scrape:
            print(f"\n--- Starting to scrape: {url} ---")
            start_time = time.time()
            
            venue_data = scraper.scrape_venue(url)
            elapsed_time = time.time() - start_time
            
            if venue_data and (venue_data.get('pricing') or venue_data.get('capacity')):
                print(f"--- Scraping successful for {venue_data.get('name', 'N/A')} in {elapsed_time:.2f} seconds ---")
                print(f"    Found prices: {venue_data.get('pricing')}")
                all_venues_data.append(venue_data)
            else:
                print(f"--- Scraping failed or found no key data for {url} after {elapsed_time:.2f} seconds ---")

        if all_venues_data:
            output_file = "scraped_venues_data.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_venues_data, f, indent=4, ensure_ascii=False)
            print(f"\nSuccessfully scraped {len(all_venues_data)} venues. Results saved to: {output_file}")

    finally:
        scraper.close()
        print("\nScraping process finished and WebDriver closed.")

if __name__ == "__main__":
    main()