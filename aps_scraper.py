import schedule
import time
import os
import chromedriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from dotenv import load_dotenv

load_dotenv()

APS_USERNAME = os.getenv("APS_USERNAME")
APS_PASSWORD = os.getenv("APS_PASSWORD")

def run_scraper():
    print("Running APS scraper...")

    # Automatically install compatible ChromeDriver
    chromedriver_autoinstaller.install()

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get("https://www.aps.com/")
        # Placeholder for actual login & data scraping logic
        print("Logged in and captured data... (implement this)")
    finally:
        driver.quit()
        print("Browser closed.")

# Run once right away
run_scraper()
