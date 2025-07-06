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
from paho.mqtt.client import CallbackAPIVersion  # ✅ Correct Enum import
from datetime import datetime, timedelta
import time

from runtime_controller import wait_until_random_time

ENERGY_TOTALS_FILE = "energy_totals.json"

def load_totals():
    if os.path.exists(ENERGY_TOTALS_FILE):
        with open(ENERGY_TOTALS_FILE, "r") as f:
            return json.load(f)
    return {"generated": 0.0, "sold": 0.0, "used": 0.0}

def save_totals(totals):
    with open(ENERGY_TOTALS_FILE, "w") as f:
        json.dump(totals, f)

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

def publish_discovery(client, topic_suffix, name, unit, unique_id):
    discovery_topic = f"homeassistant/sensor/aps_energy_{topic_suffix}/config"
    payload = {
        "name": name,
        "state_topic": f"aps_energy/{topic_suffix}",
        "unit_of_measurement": unit,
        "device_class": "energy",
        "state_class": "total_increasing",
        "value_template": "{{ value | float }}",
        "unique_id": unique_id,
        "device": {
            "identifiers": ["aps_energy_scraper"],
            "name": "APS Energy Scraper",
            "manufacturer": "Custom",
            "model": "Web Scraper"
        }
    }
    client.publish(discovery_topic, json.dumps(payload), retain=True)

def publish_to_mqtt(message):
    client = mqtt.Client(
        protocol=mqtt.MQTTv5,
        callback_api_version=CallbackAPIVersion.V5  # ✅ Correct usage
    )
    if MQTT_USERNAME and MQTT_PASSWORD:
        client.username_pw_set(username=MQTT_USERNAME, password=MQTT_PASSWORD)
    client.connect(MQTT_HOST, MQTT_PORT, 60)

    publish_discovery(client, "generated", "Total Energy Generated", "kWh", "aps_energy_generated")
    publish_discovery(client, "sold", "Total Energy Sold To APS", "kWh", "aps_energy_sold")
    publish_discovery(client, "used", "Total APS Energy Used", "kWh", "aps_energy_used")
    publish_discovery(client, "own_used", "Total APS Energy Own Used", "kWh", "aps_energy_own_used")

    logging.info(f"📤 Publishing to MQTT: {message}")
    for key, value in message.items():
        client.publish(f"aps_energy/{key}", value, retain=True)

    client.disconnect()

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
            value = span.find_element(By.CSS_SELECTOR, "span.css-pzpy3e").text.strip()
            label = span.find_element(By.CSS_SELECTOR, "span.css-1wwo9nq").text.strip()
            energy_data[label] = value

        generated = float(energy_data.get("Total Energy Generated", "0").replace(",", ""))
        sold = float(energy_data.get("Total Energy Sold To APS", "0").replace(",", ""))
        used = float(energy_data.get("Total APS Energy Used", "0").replace(",", ""))
        own_used = generated - sold

        logging.info(f"📆 Date: {date_text}")
        logging.info(f"🔋 Total Energy Generated: {generated}")
        logging.info(f"🔄 Total Energy Sold To APS: {sold}")
        logging.info(f"⚡ Total APS Energy Used: {used}")
        logging.info(f"🏠 Total APS Energy Own Used: {own_used}")

        # Load, update, and save cumulative totals
        totals = load_totals()
        totals["generated"] += generated
        totals["sold"] += sold
        totals["used"] += used
        totals["own_used"] = totals["generated"] - totals["sold"]
        save_totals(totals)

        mqtt_payload = {
            "generated": f"{totals['generated']:.2f}",
            "sold": f"{totals['sold']:.2f}",
            "used": f"{totals['used']:.2f}",
            "own_used": f"{totals['own_used']:.2f}"
        }

        publish_to_mqtt(mqtt_payload)

    except Exception as e:
        logging.error(f"❌ Scraper failed: {e}")
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