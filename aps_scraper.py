import time
import paho.mqtt.client as mqtt
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# MQTT Setup
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_PREFIX = "homeassistant"

# APS Login Info
APS_USERNAME = "your_username"
APS_PASSWORD = "your_password"

# Headless browser setup
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")

# Start driver
driver = webdriver.Chrome(options=chrome_options)
driver.get("https://www.aps.com/myaccount")

try:
    # Accept cookies if needed
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
    ).click()
except:
    pass  # Cookie banner may not be present

# Login
WebDriverWait(driver, 15).until(
    EC.presence_of_element_located((By.ID, "login"))
).click()

WebDriverWait(driver, 15).until(
    EC.presence_of_element_located((By.NAME, "username"))
).send_keys(APS_USERNAME)

driver.find_element(By.NAME, "password").send_keys(APS_PASSWORD)
driver.find_element(By.NAME, "login-submit").click()

# Wait until the dashboard loads
WebDriverWait(driver, 20).until(
    EC.presence_of_element_located((By.CLASS_NAME, "dashboard-usage"))
)

# Simulated scraping – replace with actual selectors for your usage data
total_generated = 1234.56  # kWh - scrape this dynamically
total_exported = 789.01    # kWh
total_imported = 567.89    # kWh

# MQTT publish helper
def publish_sensor(client, sensor_id, name, value):
    state_topic = f"{MQTT_PREFIX}/sensor/{sensor_id}/state"
    config_topic = f"{MQTT_PREFIX}/sensor/{sensor_id}/config"

    config_payload = {
        "name": name,
        "state_topic": state_topic,
        "unit_of_measurement": "kWh",
        "device_class": "energy",
        "state_class": "total_increasing",
        "value_template": "{{ value | float }}",
        "unique_id": sensor_id,
        "device": {
            "identifiers": ["aps_energy_scraper"],
            "name": "APS Energy Scraper",
            "manufacturer": "Custom",
            "model": "Web Scraper"
        }
    }

    client.publish(config_topic, json.dumps(config_payload), retain=True)
    client.publish(state_topic, value, retain=True)

# Connect to MQTT and publish data
import json
client = mqtt.Client()
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_start()

publish_sensor(client, "aps_energy_generated", "Total Energy Generated", total_generated)
publish_sensor(client, "aps_energy_exported", "Total Energy Sold to APS", total_exported)
publish_sensor(client, "aps_energy_imported", "Total APS Energy Used", total_imported)

client.loop_stop()
client.disconnect()

# Cleanup
driver.quit()
