import os
import time
import logging
import paho.mqtt.client as mqtt
from datetime import datetime
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

MQTT_HOST = os.getenv("MQTT_HOST")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "aps/energy")

def scrape_aps_data():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)

    try:
        driver.get("https://www.aps.com/myaccount/interruption")

        # Accept cookie banner if present
        try:
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
            ).click()
            logging.info("🍪 Accepted cookie banner.")
        except Exception:
            logging.info("🍪 No cookie banner found or already accepted.")

        # Wait for login button and click it
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "loginBtn"))
        ).click()

        # Enter credentials
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "username"))
        ).send_keys(os.getenv("APS_USERNAME"))
        driver.find_element(By.ID, "password").send_keys(os.getenv("APS_PASSWORD"))
        driver.find_element(By.ID, "loginBtn").click()

        logging.info("✅ Successfully logged in.")

        # Wait for the energy usage page to load
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "insights-card"))
        )

        # Scrape data
        date = driver.find_element(By.CLASS_NAME, "insights-date").text
        total_generated = driver.find_element(By.ID, "totalEnergyGenerated").text
        total_sold = driver.find_element(By.ID, "totalEnergySold").text
        total_used = driver.find_element(By.ID, "totalEnergyUsed").text

        logging.info(f"📆 Date: {date}")
        logging.info(f"🔋 Total Energy Generated: {total_generated}")
        logging.info(f"🔄 Total Energy Sold To APS: {total_sold}")
        logging.info(f"⚡ Total APS Energy Used: {total_used}")

        return {
            "date": date,
            "generated": total_generated,
            "sold": total_sold,
            "used": total_used
        }

    finally:
        driver.quit()

def publish_to_mqtt(data):
    client = mqtt.Client(protocol=mqtt.MQTTv5, callback_api_version=5)
    client.connect(MQTT_HOST, MQTT_PORT, 60)

    payload = {
        "date": data["date"],
        "total_generated": data["generated"],
        "total_sold_to_aps": data["sold"],
        "total_used": data["used"]
    }

    import json
    client.publish(MQTT_TOPIC, json.dumps(payload))
    client.disconnect()
    logging.info("📡 Data published to MQTT.")

if __name__ == "__main__":
    try:
        data = scrape_aps_data()
        publish_to_mqtt(data)
    except Exception as e:
        logging.error(f"❌ Scraper failed: {e}")
