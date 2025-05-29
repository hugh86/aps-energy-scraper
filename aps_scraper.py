import time
import logging
import paho.mqtt.client as mqtt
from paho.mqtt.client import CallbackAPIVersion
from datetime import datetime
from aps_scraper_core import scrape_aps_data  # Assuming this is your scraping logic

# MQTT settings
MQTT_BROKER = "host.docker.internal"
MQTT_PORT = 1883
MQTT_TOPIC = "aps/energy"
MQTT_CLIENT_ID = "aps_scraper"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        logging.info("✅ Connected to MQTT Broker!")
    else:
        logging.error(f"❌ Failed to connect, reason code: {reason_code}")

def publish_aps_data(client, data):
    if not client.is_connected():
        logging.warning("⚠️ MQTT client not connected, attempting reconnect...")
        client.reconnect()

    payload = {
        "date": data['date'],
        "total_generated": data['total_generated'],
        "total_sold": data['total_sold'],
        "total_used": data['total_used']
    }

    client.publish(MQTT_TOPIC, str(payload))
    logging.info("📤 Data published to MQTT")

def main():
    client = mqtt.Client(
        client_id=MQTT_CLIENT_ID,
        protocol=mqtt.MQTTv5,
        callback_api_version=CallbackAPIVersion.V5
    )

    client.on_connect = on_connect

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
        client.loop_start()

        # Give MQTT a second to connect
        time.sleep(2)

        try:
            data = scrape_aps_data()
            logging.info(f"📆 Date: {data['date']}")
            logging.info(f"🔋 Total Energy Generated: {data['total_generated']}")
            logging.info(f"🔄 Total Energy Sold To APS: {data['total_sold']}")
            logging.info(f"⚡ Total APS Energy Used: {data['total_used']}")

            publish_aps_data(client, data)

        except Exception as e:
            logging.error(f"❌ Scraper failed: {e}")

    except Exception as e:
        logging.error(f"❌ MQTT connection failed: {e}")
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()
