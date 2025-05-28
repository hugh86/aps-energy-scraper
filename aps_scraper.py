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
LAST_RUN_FILE = "/tmp/aps_scraper_last_run.txt"
RUN_INTERVAL_SECONDS = 4 * 60 * 60  # 4 hours

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

def already_ran_recently():
    try:
        with open(LAST_RUN_FILE, "r") as f:
            last_run = float(f.read().strip())
        return (time.time() - last_run) < RUN_INTERVAL_SECONDS
    except:
        return False

def save_last_run_time():
    with open(LAST_RUN_FILE, "w") as f:
        f.write(str(time.time()))

def wait_for_spinner_to_disappear(driver, timeout=15):
    try:
        WebDriverWait(driver, timeout).until(
            EC.invisibility_of_element_located((By.ID, "spinnerFocus"))
        )
    except:
        pass

def run_scraper():
    options = Options()
    options.binary_location = os.getenv("CHROME_BIN", "/usr/bin/chromium")
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = Service(os.getenv("CHROMEDRIVER_BIN", "/usr/bin/chromedriver"))
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get("https://www.aps.com/Authorization/Login")

        # Cookie banner
        try:
            WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Accept')]"))
            ).click()
        except:
            pass

        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "emailAddress")))
        driver.find_element(By.ID, "emailAddress").send_keys(APS_USERNAME)
        driver.find_element(By.ID, "password").send_keys(APS_PASSWORD)
        driver.find_element(By.XPATH, "//button[@aria-label='Sign In' or contains(text(),'Sign In')]").click()

        WebDriverWait(driver, 30).until(EC.url_contains("/Dashboard"))
        logging.info("✅ Successfully logged in.")

        driver.get("https://www.aps.com/en/Residential/Account/Overview/Dashboard?origin=usage")
        wait_for_spinner_to_disappear(driver)

        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, "//span[contains(text(),'Hourly')]"))).click()
        wait_for_spinner_to_disappear(driver)

        date_text = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "span.css-geyj4e"))
        ).text

        container = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.css-6req3m > div.css-15bvg19"))
        )
        data_spans = container.find_elements(By.CSS_SELECTOR, "span.css-1c4vfd5")

        energy_data = {}
        for span in data_spans:
            value = span.find_element(By.CSS_SELECTOR, "span.css-pzpy3e").text.strip()
            label = span.find_element(By.CSS_SELECTOR, "span.css-1wwo9nq").text.strip()
            energy_data[label] = value

        logging.info(f"📆 Date: {date_text}")
        logging.info(f"🔋 Total Energy Generated: {energy_data.get('Total Energy Generated', 'N/A')}")
        logging.info(f"🔄 Total Energy Sold To APS: {energy_data.get('Total Energy Sold To APS', 'N/A')}")
        logging.info(f"⚡ Total APS Energy Used: {energy_data.get('Total APS Energy Used', 'N/A')}")

    except Exception as e:
        logging.error(f"❌ Scraper failed: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    if not already_ran_recently():
        run_scraper()
        save_last_run_time()
