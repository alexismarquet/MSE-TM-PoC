import paho.mqtt.client as mqtt
import time
import argparse
from tinydb import TinyDB, Query
from tinyrecord import transaction
import logging
import sys
import json
import threading

# init args parser
parser = argparse.ArgumentParser(description="Process some integers.")
parser.add_argument(
    "MQTT_broker", metavar="MQTT_broker", type=str, help="Address of the MQTT broker"
)
args = parser.parse_args()

# init logger
logFormatter = logging.Formatter(
    "%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s"
)
logger = logging.getLogger()
fileHandler = logging.FileHandler("{0}/{1}.log".format("log", f"agenceur"))
fileHandler.setFormatter(logFormatter)
logger.addHandler(fileHandler)
consoleHandler = logging.StreamHandler(sys.stdout)
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)
logger.setLevel(logging.INFO)

# init opaque DB
db_opaque = TinyDB("opaque.json")

# init clear measures DB
db_measures = TinyDB("measures.json")
db_measures.truncate()
lock = threading.Lock()  # on received message


def on_message(client, userdata, message):
    with lock:
        logger.debug(
            "rcvd: " + message.topic + "/" + str(message.payload.decode("utf-8"))
        )

        if message.topic == "addToPool":
            # store in DB
            logger.info("storing payload")
            db_opaque.insert({"entry": str(message.payload.decode("utf-8"))})

        if message.topic == "requestPool":
            asking = str(message.payload.decode("utf-8"))
            completePool = db_opaque.all()
            # dont sent if pool is empty
            if len(completePool):
                db_opaque.truncate()
                logger.info("publishing table to" + f"getPool{asking}")
                table_json = json.dumps(completePool)
                client.publish(f"getPool{asking}", table_json)

        if message.topic == "measures":
            logger.info(f"m: {message.payload}")
            db_measures.insert({"entry": message.payload.decode("utf-8")})
            logger.info(f"received measure {message.payload}")


# connecting to MQTT broker
logger.info(f"Connecting to broker at {args.MQTT_broker}")
client = mqtt.Client("Agenceur")
client.connect(args.MQTT_broker)
# client.enable_logger()

# start receive thread
client.loop_start()

# subscribe to
# * addToPool:      endpoint for opaque payload
# * requestPool:    endpoint for opaque pool request from devices
# * measures:       endpoint for clear-data measures
client.subscribe("addToPool")
client.subscribe("requestPool")
client.subscribe("measures")

# register receive routine
client.on_message = on_message

# only on event execution
while True:
    time.sleep(1)

client.loop_stop()
