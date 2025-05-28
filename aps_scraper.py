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

LOCKFILE = "/tmp/aps_scraper.lock"
MIN_INTERVAL_SECONDS = 600  # 10 minutes

def already_ran_recently():
    if not os.path.exists(LOCKFILE):
        return False
    last_run = os.path.getmtime(LOCKFILE)
    return (time.time() - last_run) < MIN_INTERVAL_SECONDS

def update_lockfile():
    with open(LOCKFILE, "w") as f:
        f.write(str(time.time()))

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
        # Step 1: Open APS login page
        driver.get("https://www.aps.com/Authorization/Login")
        logging.info("Opened APS login page.")

        # Step 2: Accept cookie banner if present
        try:
            cookie_accept_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Accept')]"))
            )
            cookie_accept_button.click()
            logging.info("Accepted cookie banner.")
        except Exception:
            logging.info("No cookie banner to accept.")

        # Step 3: Enter login credentials (field labeled "Email Address or Username")
        username_input = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "emailAddress"))
        )
        username_input.clear()
        username_input.send_keys(APS_USERNAME)

        password_input = driver.find_element(By.ID, "password")
        password_input.clear()
        password_input.send_keys(APS_PASSWORD)

        sign_in_button = driver.find_element(By.ID, "login-submit")
        sign_in_button.click()
        logging.info("Entered credentials and clicked Sign In.")

        # Step 4: Wait for dashboard page (confirm successful login)
        WebDriverWait(driver, 30).until(EC.url_contains("/Dashboard"))
        logging.info("✅ Successfully logged in, dashboard page reached.")

        # Step 5: Navigate to usage dashboard page
        driver.get("https://www.aps.com/en/Residential/Account/Overview/Dashboard?origin=usage")
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//span[contains(text(),'Hourly')]"))
        )
        logging.info("Navigated to usage dashboard page.")

        # Step 6: Wait for spinner gone, then click the Hourly tab
        WebDriverWait(driver, 20).until(
            EC.invisibility_of_element_located((By.ID, "spinnerFocus"))
        )

        hourly_tab = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Hourly')]"))
        )
        hourly_tab.click()
        logging.info("Clicked Hourly tab.")

        # Step 7: Capture the date span text
        date_span = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "span.css-geyj4e"))
        )
        date_text = date_span.text
        logging.info(f"Date captured: {date_text}")

        # Step 8: Capture energy data spans
        energy_generated = driver.find_element(By.XPATH, "//span[contains(text(),'Total Energy Generated')]/following-sibling::span").text
        energy_sold = driver.find_element(By.XPATH, "//span[contains(text(),'Total Energy Sold to APS')]/following-sibling::span").text
        energy_used = driver.find_element(By.XPATH, "//span[contains(text(),'Total APS Energy Used')]/following-sibling::span").text

        logging.info("✅ Data Captured:")
        logging.info(f"  Total Energy Generated: {energy_generated}")
        logging.info(f"  Total Energy Sold to APS: {energy_sold}")
        logging.info(f"  Total APS Energy Used: {energy_used}")

    except Exception as e:
        logging.error(f"❌ Error during scraping: {e}")

    finally:
        driver.quit()
        logging.info("Browser closed.")

if __name__ == "__main__":
    if already_ran_recently():
        logging.info("Skipping run: scraper ran less than 10 minutes ago.")
    else:
        run_scraper()
        update_lockfile()
