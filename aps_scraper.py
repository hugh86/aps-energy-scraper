import schedule
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from dotenv import load_dotenv

load_dotenv()

APS_USERNAME = os.getenv("APS_USERNAME")
APS_PASSWORD = os.getenv("APS_PASSWORD")
CHROMEDRIVER_BIN = os.getenv("CHROMEDRIVER_BIN", "/usr/lib/chromium/chromedriver")
CHROME_BIN = os.getenv("CHROME_BIN", "/usr/bin/chromium")

def run_scraper():
    print("Running APS scraper...")

    chrome_options = Options()
    chrome_options.binary_location = CHROME_BIN
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    service = Service(CHROMEDRIVER_BIN)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get("https://www.aps.com/")
        # TODO: Add login and scraping logic here
        print("Logged in and captured data... (implement this)")
    finally:
        driver.quit()
        print("Browser closed.")

# Run immediately
run_scraper()

# Optional: Schedule to run daily at 8:30 AM
schedule.every().day.at("08:30").do(run_scraper)

while True:
    schedule.run_pending()
    time.sleep(60)
