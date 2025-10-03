import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def fetch_page_html(url: str, output_filename: str = "caterer_page.html"):
    """
    Navigates to a URL using Selenium, waits for dynamic content, 
    and saves the complete page HTML to a file.
    """
    print("Setting up WebDriver...")
    # --- Configure Chrome Options ---
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run without opening a visible browser window
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--log-level=3") # Suppress non-essential console logs
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    # --- Initialize WebDriver ---
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    print(f"WebDriver setup complete.")

    try:
        print(f"\nNavigating to: {url}")
        driver.get(url)
        
        # --- Wait for Dynamic Content ---
        # Adjust this wait time if the page is very slow to load
        wait_time = 8 
        print(f"Waiting for {wait_time} seconds for the page to load completely...")
        time.sleep(wait_time)
        
        # --- Get Page Source ---
        print("Retrieving the final page HTML...")
        html_content = driver.page_source
        
        # --- Save to File ---
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        print(f"\nSUCCESS: The complete HTML has been saved to '{output_filename}'")

    except Exception as e:
        print(f"\nAn error occurred: {e}")
        
    finally:
        # --- Clean Up ---
        print("Closing WebDriver.")
        driver.quit()

if __name__ == "__main__":
    # --- IMPORTANT: PASTE THE CATERER'S URL HERE ---
    # Example URL is provided, replace it with the one you want to scrape.
    target_url = "https://www.wedmegood.com/profile/PC-Makeover-Studio-24599993"
    
    fetch_page_html(url=target_url)