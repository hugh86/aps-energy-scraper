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
        # Step 1: Open APS residential home page
        driver.get("https://www.aps.com/en/Residential/Home")
        logging.info("Opened APS residential home page.")

        # Optional: accept cookie banner if present
        try:
            cookie_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Accept All Cookies')]"))
            )
            cookie_button.click()
            logging.info("Accepted cookie banner.")
        except:
            logging.info("No cookie banner found.")

        # Step 2: Click Sign In to open the login dropdown
        sign_in_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'Sign In')]"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", sign_in_button)
        sign_in_button.click()
        logging.info("Clicked Sign In button.")

        # Step 3: Wait for login dropdown to appear
        WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located((By.ID, "emailAddress"))
        )
        logging.info("Login dropdown appeared.")

        # Step 4: Enter credentials and submit
        driver.find_element(By.ID, "emailAddress").send_keys(APS_USERNAME)
        driver.find_element(By.ID, "password").send_keys(APS_PASSWORD)
        driver.find_element(By.ID, "login-submit").click()
        logging.info("Entered credentials and submitted login form.")

        # Step 5: Wait for dashboard page
        WebDriverWait(driver, 30).until(EC.url_contains("/Dashboard"))
        logging.info("✅ Successfully logged in, dashboard page reached.")

        # Step 6: Navigate to usage dashboard page
        driver.get("https://www.aps.com/en/Residential/Account/Overview/Dashboard?origin=usage")
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//span[contains(text(),'Hourly')]"))
        )
        logging.info("Navigated to usage dashboard page.")

        # Step 7: Click the Hourly tab
        hourly_tab = driver.find_element(By.XPATH, "//span[contains(text(),'Hourly')]")
        hourly_tab.click()
        logging.info("Clicked Hourly tab.")

        # Step 8: Capture the date span text
        date_span = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "span.css-geyj4e"))
        )
        date_text = date_span.text
        logging.info(f"Date captured: {date_text}")

        # Step 9: Capture energy data spans
        energy_generated = driver.find_element(By.XPATH, "//span[contains(text(),'Total Energy Generated')]/following-sibling::span").text
        energy_sold = driver.find_element(By.XPATH, "//span[contains(text(),'Total Energy Sold to APS')]/following-sibling::span").text
        energy_used = driver.find_element(By.XPATH, "//span[contains(text(),'Total APS Energy Used')]/following-sibling::span").text

        logging.info("✅ Data Captured:")
        logging.info(f"  Total Energy Generated: {energy_generated}")
        logging.info(f"  Total Energy Sold to APS: {energy_sold}")
        logging.info(f"  Total APS Energy Used: {energy_used}")

    except Exception as e:
        logging.error(f"❌ Error during scraping: {e}", exc_info=True)
        driver.save_screenshot("debug_screenshot.png")
        logging.info("Saved screenshot: debug_screenshot.png")

    finally:
        driver.quit()
        logging.info("Browser closed.")

if __name__ == "__main__":
    run_scraper()
