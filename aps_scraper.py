import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

def login_aps(driver, username, password):
    driver.get("https://www.aps.com/en/Residential/Home")
    logging.info("Opened APS residential home page.")

    try:
        # Click login button to open login overlay
        login_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.ID, "login-button"))
        )
        login_button.click()
        logging.info("Clicked login button to open login overlay.")

        # Wait for login inputs to appear
        email_input = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "emailAddress"))
        )
        password_input = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "password"))
        )

        email_input.clear()
        email_input.send_keys(username)
        password_input.clear()
        password_input.send_keys(password)
        logging.info("Entered username and password.")

        # Click Sign In button in overlay
        sign_in_submit = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div.log-btn > button.aps-btn-new"))
        )
        sign_in_submit.click()
        logging.info("Clicked Sign In submit button.")

        # Wait for dashboard page load after login
        WebDriverWait(driver, 30).until(
            EC.url_contains("/Residential/Account/Overview/Dashboard")
        )
        logging.info("Successfully logged in and dashboard loaded.")
        return True

    except TimeoutException:
        logging.error("Login failed: Timeout while waiting for elements or page.")
        return False
    except NoSuchElementException:
        logging.error("Login failed: Required element not found.")
        return False


def scrape_aps_data(driver):
    try:
        # Example selectors - adjust based on actual dashboard elements you want to scrape
        # These selectors should be updated to match the actual dashboard elements for:
        # - Total Energy Generated
        # - Total Energy Sold to APS
        # - Total APS Energy Used

        # Here are example placeholders; update accordingly:
        total_energy_generated = driver.find_element(By.XPATH, "//div[contains(text(),'Total Energy Generated')]/following-sibling::div").text
        total_energy_sold = driver.find_element(By.XPATH, "//div[contains(text(),'Total Energy Sold to APS')]/following-sibling::div").text
        total_energy_used = driver.find_element(By.XPATH, "//div[contains(text(),'Total APS Energy Used')]/following-sibling::div").text

        logging.info(f"Total Energy Generated: {total_energy_generated}")
        logging.info(f"Total Energy Sold to APS: {total_energy_sold}")
        logging.info(f"Total APS Energy Used: {total_energy_used}")

        return {
            "total_energy_generated": total_energy_generated,
            "total_energy_sold": total_energy_sold,
            "total_energy_used": total_energy_used,
        }

    except Exception as e:
        logging.error(f"Failed to scrape data: {e}")
        return None


def main():
    # Replace with your real APS credentials
    username = "your_username_here"
    password = "your_password_here"

    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")  # Uncomment if you want headless mode
    driver = webdriver.Chrome(options=options)

    try:
        if login_aps(driver, username, password):
            data = scrape_aps_data(driver)
            if data:
                logging.info("Data scraping complete.")
            else:
                logging.error("Data scraping failed.")
        else:
            logging.error("Login process failed; aborting data scrape.")

    finally:
        driver.quit()
        logging.info("Browser closed.")


if __name__ == "__main__":
    main()
