import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from dotenv import load_dotenv

load_dotenv()

APS_USERNAME = os.getenv("APS_USERNAME")
APS_PASSWORD = os.getenv("APS_PASSWORD")

def run_scraper():
    print("Running APS scraper...")

    chrome_options = Options()
    # Use chromium installed by apt
    chrome_options.binary_location = os.getenv("CHROME_BIN", "/usr/bin/chromium")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    chromedriver_path = os.getenv("CHROMEDRIVER_BIN", "/usr/bin/chromedriver")
    service = Service(chromedriver_path)

    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get("https://www.aps.com/")
        # TODO: Add your login and scraping code here using APS_USERNAME and APS_PASSWORD
        print("Logged in and captured data... (implement this)")
    finally:
        driver.quit()
        print("Browser closed.")

if __name__ == "__main__":
    run_scraper()
