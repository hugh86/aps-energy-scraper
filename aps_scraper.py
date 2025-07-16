import os
import json
import logging
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import paho.mqtt.client as mqtt
from datetime import datetime, timedelta
import socket
import time

from runtime_controller import wait_until_random_time

# Load environment variables
load_dotenv()

APS_USERNAME = os.getenv("APS_USERNAME")
APS_PASSWORD = os.getenv("APS_PASSWORD")

MQTT_HOST = os.getenv("MQTT_HOST", "172.17.0.1")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

def wait_for_spinner_to_disappear(driver, timeout=15):
    try:
        WebDriverWait(driver, timeout).until(
            EC.invisibility_of_element_located((By.ID, "spinnerFocus"))
        )
    except:
        pass

def publish_daily_discovery(client, topic_suffix, name, unique_id):
    discovery_topic = f"homeassistant/sensor/aps_energy_{topic_suffix}_today/config"
    payload = {
        "name": f"{name} Today",
        "state_topic": f"aps_energy/{topic_suffix}_today",
        "unit_of_measurement": "kWh",
        "device_class": "energy",
        "state_class": "measurement",
        "value_template": "{{ value | float }}",
        "unique_id": f"{unique_id}_today",
        "device": {
            "identifiers": ["aps_energy_scraper"],
            "name": "APS Energy Scraper",
            "manufacturer": "Custom",
            "model": "Web Scraper"
        }
    }
    client.publish(discovery_topic, json.dumps(payload), retain=True)

def publish_to_mqtt(daily):
    try:
        # DNS check
        try:
            socket.gethostbyname(MQTT_HOST)
        except socket.gaierror:
            logging.error(f"❌ DNS lookup failed for MQTT_HOST: {MQTT_HOST}")
            return

        client = mqtt.Client(protocol=mqtt.MQTTv311, callback_api_version=5)

        if MQTT_USERNAME and MQTT_PASSWORD:
            client.username_pw_set(username=MQTT_USERNAME, password=MQTT_PASSWORD)
        client.connect(MQTT_HOST, MQTT_PORT, 60)

        # Publish discovery
        publish_daily_discovery(client, "generated", "Total Energy Generated", "aps_energy_generated")
        publish_daily_discovery(client, "sold", "Total Energy Sold To APS", "aps_energy_sold")
        publish_daily_discovery(client, "used", "Total APS Energy Used", "aps_energy_used")
        publish_daily_discovery(client, "own_used", "Total APS Energy Own Used", "aps_energy_own_used")

        # Publish daily values
        logging.info(f"📆 Publishing daily sensors: {daily}")
        for key, value in daily.items():
            client.publish(f"aps_energy/{key}_today", value, retain=True)

        client.disconnect()

    except Exception as e:
        logging.error(f"❌ MQTT publish failed: {e}")

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

        WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Hourly')]"))).click()
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
            try:
                value = span.find_element(By.CSS_SELECTOR, "span.css-pzpy3e").text.strip()
                label = span.find_element(By.CSS_SELECTOR, "span.css-1wwo9nq").text.strip()
                energy_data[label] = value
            except Exception:
                logging.warning("⚠️ Skipped a span due to missing elements.")

        generated = float(energy_data.get("Total Energy Generated", "0").replace(",", ""))
        sold = float(energy_data.get("Total Energy Sold To APS", "0").replace(",", ""))
        used = float(energy_data.get("Total APS Energy Used", "0").replace(",", ""))
        own_used = generated - sold

        logging.info(f"📆 Date: {date_text}")
        logging.info(f"🔋 Generated: {generated}")
        logging.info(f"🔄 Sold: {sold}")
        logging.info(f"⚡ Used: {used}")
        logging.info(f"🏠 Own Used: {own_used}")

        daily = {
            "generated": f"{generated:.2f}",
            "sold": f"{sold:.2f}",
            "used": f"{used:.2f}",
            "own_used": f"{own_used:.2f}"
        }

        publish_to_mqtt(daily)

    except Exception as e:
        logging.error(f"❌ Scraper failed: {e}")
        try:
            driver.save_screenshot("error_screenshot.png")
        except:
            pass
    finally:
        driver.quit()

def main_loop():
    run_scraper()

    while True:
        wait_until_random_time(6, 30, 7, 40)
        run_scraper()
        next_run = (datetime.now() + timedelta(days=1)).replace(hour=6, minute=30, second=0, microsecond=0)
        sleep_seconds = (next_run - datetime.now()).total_seconds()
        logging.info(f"✅ Run complete. Sleeping {sleep_seconds / 3600:.2f} hours until next run.")
        time.sleep(sleep_seconds)

if __name__ == "__main__":
    main_loop()