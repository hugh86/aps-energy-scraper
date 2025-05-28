import os
import time
import logging
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv

load_dotenv()

APS_USERNAME = os.getenv("APS_USERNAME")
APS_PASSWORD = os.getenv("APS_PASSWORD")
TIMESTAMP_FILE = "/tmp/aps_scraper_last_run.txt"

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')


def should_run():
    try:
        with open(TIMESTAMP_FILE, 'r') as f:
            last_run = datetime.fromisoformat(f.read().strip())
            if datetime.now() - last_run < timedelta(minutes=10):
                logging.info("⏱ Skipping run: last run was less than 10 minutes ago.")
                return False
    except FileNotFoundError:
        pass
    return True


def update_last_run():
    with open(TIMESTAMP_FILE, 'w') as f:
        f.write(datetime.now().isoformat())


def run_scraper():
    if not should_run():
        return

    logging.info("Running APS scraper...")

    options = Options()
    options.binary_location = os.getenv("CHROME_BIN", "/usr/bin/chromium")
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = Service(os.getenv("CHROMEDRIVER_BIN", "/usr/bin/chromedriver"))
    driver = webdriver.Chrome(service=service, options=options)

    try:
        # Step 1: Open APS landing page
        driver.get("https://www.aps.com/en/Residential/Save-Money-and-Energy/Home-Energy-Report")
        logging.info("Opened APS landing page.")

        # Step 2: Accept cookies if present
        try:
            accept_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Accept')]"))
            )
            accept_button.click()
            logging.info("Accepted cookie banner.")
        except Exception:
            logging.info("No cookie banner appeared.")

        # Step 3: Fill in login form directly
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//input[@aria-label='Email Address or Username']"))
        )
        driver.find_element(By.XPATH, "//input[@aria-label='Email Address or Username']").send_keys(APS_USERNAME)
        driver.find_element(By.ID, "password").send_keys(APS_PASSWORD)
        driver.find_element(By.ID, "login-submit").click()
        logging.info("Submitted login credentials.")

        # Step 4: Wait for login to complete and dashboard to load
        WebDriverWait(driver, 30).until(
            EC.url_contains("/Dashboard")
        )
        logging.info("✅ Logged in successfully.")

        # Step 5: Navigate to usage dashboard
        driver.get("https://www.aps.com/en/Residential/Account/Overview/Dashboard?origin=usage")
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//span[contains(text(),'Hourly')]"))
        )
        driver.find_element(By.XPATH, "//span[contains(text(),'Hourly')]").click()
        logging.info("Navigated to Hourly usage tab.")

        # Step 6: Extract energy data
        date_text = driver.find_element(By.CSS_SELECTOR, "span.css-geyj4e").text
        energy_generated = driver.find_element(By.XPATH, "//span[contains(text(),'Total Energy Generated')]/following-sibling::span").text
        energy_sold = driver.find_element(By.XPATH, "//span[contains(text(),'Total Energy Sold to APS')]/following-sibling::span").text
        energy_used = driver.find_element(By.XPATH, "//span[contains(text(),'Total APS Energy Used')]/following-sibling::span").text

        logging.info("✅ Data Captured:")
        logging.info(f"  Date: {date_text}")
        logging.info(f"  Total Energy Generated: {energy_generated}")
        logging.info(f"  Total Energy Sold to APS: {energy_sold}")
        logging.info(f"  Total APS Energy Used: {energy_used}")

        update_last_run()

    except Exception as e:
        logging.error(f"❌ Error during scraping: {e}")

    finally:
        driver.quit()
        logging.info("Browser closed.")


if __name__ == "__main__":
    run_scraper()
