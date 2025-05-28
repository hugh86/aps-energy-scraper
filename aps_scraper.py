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

    chrome_options = Options()
    # Use chromium installed by apt
    chrome_options.binary_location = os.getenv("CHROME_BIN", "/usr/bin/chromium")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    chromedriver_path = os.getenv("CHROMEDRIVER_BIN", "/usr/bin/chromedriver")
    service = Service(chromedriver_path)

    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get("https://www.aps.com/en/Account/Sign-In")

        # Login
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "username")))
        driver.find_element(By.ID, "username").send_keys(APS_USERNAME)
        driver.find_element(By.ID, "password").send_keys(APS_PASSWORD)
        driver.find_element(By.ID, "login-submit").click()

        # Wait for login to complete
        WebDriverWait(driver, 15).until(EC.url_contains("dashboard"))

        # Navigate to usage page (update this URL if needed)
        driver.get("https://www.aps.com/en/Residential/Account/Usage")

        # Wait for data to load — inspect APS site to get the correct selectors
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, "//div[contains(text(),'Total Energy')]")))

        # Extract data — update these XPaths based on actual APS HTML structure
        energy_generated = driver.find_element(By.XPATH, "//div[@id='energyGenerated']").text
        energy_sold = driver.find_element(By.XPATH, "//div[@id='energySold']").text
        energy_used = driver.find_element(By.XPATH, "//div[@id='energyUsed']").text

        print("✅ Data Captured:")
        print(f"  Total Energy Generated: {energy_generated}")
        print(f"  Total Energy Sold to APS: {energy_sold}")
        print(f"  Total APS Energy Used: {energy_used}")

    except Exception as e:
        print(f"❌ Error during scraping: {e}")

    finally:
        driver.quit()
        print("Browser closed.")

if __name__ == "__main__":
    while True:
        run_scraper()
        print("Pausing for 1 minute before next run...")
        time.sleep(60)
