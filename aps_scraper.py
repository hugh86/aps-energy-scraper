import os
import time
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

def run_scraper():
    print("Running APS scraper...")

    options = Options()
    options.binary_location = os.getenv("CHROME_BIN", "/usr/bin/chromium")
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = Service(os.getenv("CHROMEDRIVER_BIN", "/usr/bin/chromedriver"))
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get("https://www.aps.com/en/Account/Sign-In")
        print("Opened APS sign-in page.")

        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "username")))
        driver.find_element(By.ID, "username").send_keys(APS_USERNAME)
        driver.find_element(By.ID, "password").send_keys(APS_PASSWORD)
        driver.find_element(By.ID, "login-submit").click()
        print("Submitted login form.")

        WebDriverWait(driver, 15).until(EC.url_contains("dashboard"))
        print("Login successful, dashboard loaded.")

        driver.get("https://www.aps.com/en/Residential/Account/Overview/Dashboard?origin=usage")
        print("Navigated to usage overview page.")

        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(text(),'Total Energy')]"))
        )
        print("Usage overview loaded.")

        # Click the "Hourly" tab
        hourly_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//span[@class='inner-align' and text()='Hourly']"))
        )
        hourly_tab.click()
        print("Clicked 'Hourly' tab.")

        # Wait a moment for hourly data to load
        time.sleep(2)

        # Capture the date
        date_span = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "span.css-geyj4e"))
        )
        date_text = date_span.text
        print(f"Date captured: {date_text}")

        # Helper function to get value by label text
        def get_hourly_value(label_text):
            label = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, f"//span[@class='css-1wwo9nq' and text()='{label_text}']")
                )
            )
            value = label.find_element(By.XPATH, "./following-sibling::*[1]").text
            return value

        energy_generated = get_hourly_value("Total Energy Generated")
        energy_sold = get_hourly_value("Total Energy Sold")
        energy_used = get_hourly_value("Total APS Energy Used")

        print("✅ Hourly Data Captured:")
        print(f"  Total Energy Generated: {energy_generated}")
        print(f"  Total Energy Sold: {energy_sold}")
        print(f"  Total APS Energy Used: {energy_used}")

    except Exception as e:
        print(f"❌ Error during scraping: {e}")

    finally:
        driver.quit()
        print("Browser closed.")

if __name__ == "__main__":
    while True:
        run_scraper()
        print("⏱️ Waiting 24 hours until next run...")
        time.sleep(24 * 60 * 60)  # Sleep for 24 hours
