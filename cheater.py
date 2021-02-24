import paho.mqtt.client as mqtt
import time
import argparse
from tinydb import TinyDB, Query
from Crypto.Cipher import AES
from measure import Measure
import logging
import sys

# Init args parser
parser = argparse.ArgumentParser(description="Process some integers.")
parser.add_argument(
    "MQTT_broker", metavar="MQTT_broker", type=str, help="Address of the MQTT broker"
)
parser.add_argument("SF_key", metavar="Sf", type=str, help="Swarm shared secret")

args = parser.parse_args()

# init logging facility
logFormatter = logging.Formatter(
    "%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s"
)
logger = logging.getLogger()

fileHandler = logging.FileHandler("{0}/{1}.log".format("log", f"cheater"))
fileHandler.setFormatter(logFormatter)
logger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler(sys.stdout)
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)
logger.setLevel(logging.DEBUG)

# init decipher
decipher = AES.new(args.SF_key, AES.MODE_ECB)

# on receive message
def on_message(client, userdata, message):
    logger.debug("rcvd: " + message.topic + "/" + str(message.payload.decode("utf-8")))

    if message.topic == "addToPool":
        as_bytes = bytes.fromhex(message.payload.decode("utf-8"))
        res = decipher.decrypt(as_bytes)
        m = Measure("none")
        m.unpack(res)
        logger.info(m)
        # decrypt


logger.info(f"Connecting to broker at {args.MQTT_broker}")

client = mqtt.Client("Cheater")
client.connect(args.MQTT_broker)

client.loop_start()

client.subscribe("addToPool")
client.on_message = on_message
while True:
    time.sleep(1)

client.loop_stop()
