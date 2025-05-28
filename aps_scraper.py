import os
import time
import logging
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

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

def save_debug(driver, label):
    """Save a screenshot and page source with a label."""
    try:
        driver.save_screenshot(f"/tmp/debug_{label}.png")
        with open(f"/tmp/debug_{label}.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        logging.info(f"🖼️ Screenshot and page source saved: {label}")
    except Exception as e:
        logging.warning(f"Could not save debug info for {label}: {e}")

def run_scraper():
    logging.info("Running APS scraper...")

    options = Options()
    options.binary_location = os.getenv("CHROME_BIN", "/usr/bin/chromium")
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = Service(os.getenv("CHROMEDRIVER_BIN", "/usr/bin/chromedriver"))
    driver = webdriver.Chrome(service=service, options=options)

    try:
        # Step 1: Open APS home page
        logging.info("Opening APS homepage...")
        driver.get("https://www.aps.com/en/Residential/Home")
        save_debug(driver, "home_page_loaded")

        # Step 2: Click Sign In
        logging.info("Waiting for Sign In button...")
        sign_in_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'Sign In')]"))
        )
        sign_in_button.click()
        logging.info("Clicked Sign In.")
        save_debug(driver, "sign_in_clicked")

        # Step 3: Enter credentials
        logging.info("Waiting for login form...")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "username")))
        driver.find_element(By.ID, "username").send_keys(APS_USERNAME)
        driver.find_element(By.ID, "password").send_keys(APS_PASSWORD)
        save_debug(driver, "credentials_entered")

        driver.find_element(By.ID, "login-submit").click()
        logging.info("Submitted login form.")

        # Step 4: Wait for dashboard
        logging.info("Waiting for dashboard page...")
        WebDriverWait(driver, 20).until(EC.url_contains("/Dashboard"))
        logging.info("✅ Successfully logged in.")
        save_debug(driver, "dashboard_loaded")

        # Step 5: Go to usage page
        driver.get("https://www.aps.com/en/Residential/Account/Overview/Dashboard?origin=usage")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//span[contains(text(),'Hourly')]"))
        )
        logging.info("Usage dashboard loaded.")
        save_debug(driver, "usage_dashboard")

        # Step 6: Click Hourly tab
        driver.find_element(By.XPATH, "//span[contains(text(),'Hourly')]").click()
        logging.info("Clicked Hourly tab.")

        # Step 7: Get date
        date_span = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "span.css-geyj4e"))
        )
        date_text = date_span.text
        logging.info(f"Date captured: {date_text}")

        # Step 8: Get data
        energy_generated = driver.find_element(By.XPATH, "//span[contains(text(),'Total Energy Generated')]/following-sibling::span").text
        energy_sold = driver.find_element(By.XPATH, "//span[contains(text(),'Total Energy Sold to APS')]/following-sibling::span").text
        energy_used = driver.find_element(By.XPATH, "//span[contains(text(),'Total APS Energy Used')]/following-sibling::span").text

        logging.info("✅ Data Captured:")
        logging.info(f"  Total Energy Generated: {energy_generated}")
        logging.info(f"  Total Energy Sold to APS: {energy_sold}")
        logging.info(f"  Total APS Energy Used: {energy_used}")

    except Exception as e:
        logging.error(f"❌ Error: {e}")
        save_debug(driver, "error")
    finally:
        driver.quit()
        logging.info("Browser closed.")

if __name__ == "__main__":
    run_scraper()
