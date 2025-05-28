import schedule
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from dotenv import load_dotenv

load_dotenv()

APS_USERNAME = os.getenv("APS_USERNAME")
APS_PASSWORD = os.getenv("APS_PASSWORD")

def run_scraper():
    print("Running APS scraper...")

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get("https://www.aps.com/")
        # Login and navigate steps go here
        # This is a placeholder
        print("Logged in and captured data... (implement this)")
    finally:
        driver.quit()

schedule.every().day.at("08:30").do(run_scraper)

print("Scheduler started. Waiting for next scheduled task...")
while True:
    schedule.run_pending()
    time.sleep(60)
