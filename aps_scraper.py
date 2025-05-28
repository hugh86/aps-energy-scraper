from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os

def run_scraper():
    options = Options()
    options.add_argument("--headless=new")  # Remove for debugging
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = Service(os.getenv("CHROMEDRIVER_BIN", "/usr/bin/chromedriver"))
    driver = webdriver.Chrome(service=service, options=options)

    try:
        # Step 1: Open APS residential home page
        driver.get("https://www.aps.com/en/Residential/Home")
        print("Opened APS residential home page.")

        # Step 2: Click the Sign In button (wait until clickable)
        sign_in_btn = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'Sign In')]"))
        )
        sign_in_btn.click()
        print("Clicked Sign In button.")

        # Step 3: Wait for login page username field and enter credentials
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "username")))
        driver.find_element(By.ID, "username").send_keys(os.getenv("APS_USERNAME"))
        driver.find_element(By.ID, "password").send_keys(os.getenv("APS_PASSWORD"))
        driver.find_element(By.ID, "login-submit").click()
        print("Submitted login form.")

        # Add next steps here...

    except Exception as e:
        print(f"Error: {e}")

    finally:
        driver.quit()
        print("Browser closed.")

if __name__ == "__main__":
    run_scraper()
