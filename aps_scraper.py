import os
import json
import logging
import random
import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
import paho.mqtt.client as mqtt

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
        "state_class": "total",  # ✅ Needed for Energy Dashboard
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
    client = mqtt.Client(protocol=mqtt.MQTTv5)
    if MQTT_USERNAME and MQTT_PASSWORD:
        client.username_pw_set(username=MQTT_USERNAME, password=MQTT_PASSWORD)
    client.connect(MQTT_HOST, MQTT_PORT, 60)

    # Publish discovery messages
    publish_discovery(client, "generated", "Total Energy Generated", "kWh", "aps_energy_generated")
    publish_discovery(client, "sold", "Total Energy Sold To APS", "kWh", "aps_energy_sold")
    publish_discovery(client, "used", "Total APS Energy Used", "kWh", "aps_energy_used")

    # Publish sensor values
    for key, value in message.items():
        client.publish(f"aps_energy/{key}", value)

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

        # Accept cookie banner
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

        logging.info(f"📆 Date: {date_text}")
        logging.info(f"🔋 Total Energy Generated: {energy_data.get('Total Energy Generated', 'N/A')}")
        logging.info(f"🔄 Total Energy Sold To APS: {energy_data.get('Total Energy Sold To APS', 'N/A')}")
        logging.info(f"⚡ Total APS Energy Used: {energy_data.get('Total APS Energy Used', 'N/A')}")

        mqtt_payload = {
            "generated": energy_data.get("Total Energy Generated", "0"),
            "sold": energy_data.get("Total Energy Sold To APS", "0"),
            "used": energy_data.get("Total APS Energy Used", "0")
        }

        publish_to_mqtt(mqtt_payload)

    except Exception as e:
        logging.error(f"❌ Scraper failed: {e}")
    finally:
        driver.quit()

def wait_until_target_time():
    now = datetime.now()

    # Define earliest and latest run times today (7:30 and 7:40 AM)
    today_730 = now.replace(hour=7, minute=30, second=0, microsecond=0)
    today_740 = now.replace(hour=7, minute=40, second=0, microsecond=0)

    if now > today_740:
        # If current time is after 7:40 AM, schedule for tomorrow 7:30-7:40
        target_day = now + timedelta(days=1)
        today_730 = target_day.replace(hour=7, minute=30, second=0, microsecond=0)
        today_740 = target_day.replace(hour=7, minute=40, second=0, microsecond=0)

    # Pick random time between 7:30 and 7:40
    delta_seconds = int((today_740 - today_730).total_seconds())
    random_offset = random.randint(0, delta_seconds)
    run_time = today_730 + timedelta(seconds=random_offset)

    wait_seconds = (run_time - now).total_seconds()
    logging.info(f"Waiting {wait_seconds:.0f} seconds until next run at {run_time.strftime('%Y-%m-%d %H:%M:%S')}")
    time.sleep(wait_seconds)

def main_loop():
    while True:
        wait_until_target_time()
        run_scraper()
        # Sleep until next day’s 7:30 AM (minimum ~21h)
        now = datetime.now()
        next_run = (now + timedelta(days=1)).replace(hour=7, minute=30, second=0, microsecond=0)
        sleep_seconds = (next_run - now).total_seconds()
        logging.info(f"Run complete. Sleeping {sleep_seconds/3600:.2f} hours until next scheduled run.")
        time.sleep(sleep_seconds)

if __name__ == "__main__":
    main_loop()