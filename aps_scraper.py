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

LAST_RUN_FILE = "/tmp/aps_scraper_last_run.txt"

def already_ran_recently():
    try:
        with open(LAST_RUN_FILE, "r") as f:
            last_run = float(f.read().strip())
        if time.time() - last_run < 600:  # 600 seconds = 10 minutes
            logging.info("Script ran less than 10 minutes ago. Exiting.")
            return True
    except FileNotFoundError:
        return False
    except Exception as e:
        logging.warning(f"Could not read last run time: {e}")
    return False

def save_last_run_time():
    with open(LAST_RUN_FILE, "w") as f:
        f.write(str(time.time()))

def wait_for_spinner_to_disappear(driver, timeout=15):
    try:
        WebDriverWait(driver, timeout).until(
            EC.invisibility_of_element_located((By.ID, "spinnerFocus"))
        )
        logging.info("Spinner disappeared, ready to interact with the page.")
    except Exception:
        logging.info("Spinner did not disappear within timeout or was not present.")

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
        # Step 1: Open login page directly
        driver.get("https://www.aps.com/Authorization/Login")
        logging.info("Opened APS login page.")

        # Step 2: Accept cookies if present
        try:
            cookie_accept = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Accept')]"))
            )
            cookie_accept.click()
            logging.info("Cookie banner accepted.")
        except Exception:
            logging.info("No cookie banner to accept.")

        # Step 3: Wait for login fields, enter credentials and submit login
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "emailAddress"))
        )
        driver.find_element(By.ID, "emailAddress").clear()
        driver.find_element(By.ID, "emailAddress").send_keys(APS_USERNAME)

        driver.find_element(By.ID, "password").clear()
        driver.find_element(By.ID, "password").send_keys(APS_PASSWORD)

        # Click the Sign In button below password input
        sign_in_btn = driver.find_element(By.XPATH, "//button[@aria-label='Sign In' or contains(text(),'Sign In')]")
        sign_in_btn.click()
        logging.info("Entered credentials and clicked Sign In.")

        # Step 4: Wait for dashboard page (confirm successful login)
        WebDriverWait(driver, 30).until(EC.url_contains("/Dashboard"))
        logging.info("✅ Successfully logged in, dashboard page reached.")

        # Step 5: Navigate to usage dashboard page
        driver.get("https://www.aps.com/en/Residential/Account/Overview/Dashboard?origin=usage")
        wait_for_spinner_to_disappear(driver)

        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//span[contains(text(),'Hourly')]"))
        )

        # Step 6: Click the Hourly tab
        hourly_tab = driver.find_element(By.XPATH, "//span[contains(text(),'Hourly')]")
        hourly_tab.click()
        logging.info("Clicked Hourly tab.")
        wait_for_spinner_to_disappear(driver)

        # Step 7: Capture the date span text
        date_span = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "span.css-geyj4e"))
        )
        date_text = date_span.text
        logging.info(f"Date captured: {date_text}")

        # Step 8: Capture energy data from structured div/span elements
        container = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.css-6req3m > div.css-15bvg19"))
        )

        data_spans = container.find_elements(By.CSS_SELECTOR, "span.css-1c4vfd5")

        energy_data = {}
        for span in data_spans:
            value = span.find_element(By.CSS_SELECTOR, "span.css-pzpy3e").text.strip()
            label = span.find_element(By.CSS_SELECTOR, "span.css-1wwo9nq").text.strip()
            energy_data[label] = value

        logging.info("✅ Data Captured:")
        logging.info(f"  Total Energy Generated: {energy_data.get('Total Energy Generated', 'N/A')}")
        logging.info(f"  Total Energy Sold To APS: {energy_data.get('Total Energy Sold To APS', 'N/A')}")
        logging.info(f"  Total APS Energy Used: {energy_data.get('Total APS Energy Used', 'N/A')}")

    except Exception as e:
        logging.error(f"❌ Error during scraping: {e}")

    finally:
        driver.quit()
        logging.info("Browser closed.")

if __name__ == "__main__":
    if not already_ran_recently():
        run_scraper()
        save_last_run_time()
