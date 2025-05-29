import logging
import time
from datetime import datetime
import paho.mqtt.client as mqtt
from paho.mqtt.client import CallbackAPIVersion

# Your scraping logic (this is just placeholder — replace with your real logic)
def scrape_aps_data():
    return {
        "date": datetime.now().strftime("%B %d, %Y"),
        "total_generated": 57.95,
        "total_sold": 37.00,
        "total_used": 13.82
    }

# MQTT Settings
MQTT_BROKER = "host.docker.internal"
MQTT_PORT = 1883
MQTT_TOPIC = "aps/energy"
MQTT_CLIENT_ID = "aps_scraper"

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        logging.info("✅ Connected to MQTT broker")
    else:
        logging.error(f"❌ Failed to connect to MQTT broker, return code {rc}")

def main():
    try:
        # FIX: use correct CallbackAPIVersion enum to eliminate deprecation warning
        client = mqtt.Client(
            client_id=MQTT_CLIENT_ID,
            protocol=mqtt.MQTTv5,
            callback_api_version=CallbackAPIVersion.V5
        )

        client.on_connect = on_connect
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()

        # Simulate delay for stable connection
        time.sleep(2)

        data = scrape_aps_data()
        logging.info(f"📆 Date: {data['date']}")
        logging.info(f"🔋 Total Energy Generated: {data['total_generated']}")
        logging.info(f"🔄 Total Energy Sold To APS: {data['total_sold']}")
        logging.info(f"⚡ Total APS Energy Used: {data['total_used']}")

        payload = (
            f"{{\"date\": \"{data['date']}\", "
            f"\"total_generated\": {data['total_generated']}, "
            f"\"total_sold\": {data['total_sold']}, "
            f"\"total_used\": {data['total_used']}}}"
        )
        client.publish(MQTT_TOPIC, payload)

    except Exception as e:
        logging.error(f"❌ Scraper failed: {e}")

    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()
