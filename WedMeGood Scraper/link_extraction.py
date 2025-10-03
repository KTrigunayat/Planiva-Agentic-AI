from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# The URL of the webpage from which to extract links
url = "https://www.wedmegood.com/vendors/bangalore/bridal-makeup/?page=5"
# Set up the Chrome driver
# This will automatically download and manage the chromedriver
try:
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    print("WebDriver initialized successfully.")
except Exception as e:
    print(f"Error initializing WebDriver: {e}")
    exit()

# Navigate to the URL
print(f"Navigating to: {url}")
driver.get(url)

try:
    # Find all the anchor elements (links) on the page by their tag name
    link_elements = driver.find_elements(By.TAG_NAME, 'a')

    # Extract the href attribute from each link element
    links = [link.get_attribute('href') for link in link_elements if link.get_attribute('href')]

    # Print all the extracted links
    print("\n--- All Links Found on the Page ---")
    for link in links:
        print(link)
    print(f"\nTotal links found: {len(links)}")

except Exception as e:
    print(f"An error occurred while extracting links: {e}")

finally:
    # Close the browser window
    driver.quit()
    print("\nBrowser closed.")