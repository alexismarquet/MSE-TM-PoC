import paho.mqtt.client as mqtt
from random import randrange, uniform, randint, shuffle
import time
import sys
import argparse
import hashlib
from Crypto.Cipher import AES
import struct
from measure import Measure
import logging
from tinydb import TinyDB, Query
from tinyrecord import transaction
import json

# init args parser
parser = argparse.ArgumentParser(description="Process some integers.")
parser.add_argument(
    "DeviceID", metavar="DeviceID", type=str, help="Identifier of the device"
)
parser.add_argument(
    "MQTT_broker", metavar="MQTT_broker", type=str, help="Address of the MQTT broker"
)
parser.add_argument("SF_key", metavar="Sf", type=str, help="Swarm shared secret")
args = parser.parse_args()

# init cipher & decipher, in case there is a init vector int the chosen algo
cipher = AES.new(args.SF_key, AES.MODE_ECB)
decipher = AES.new(args.SF_key, AES.MODE_ECB)

# init logger, logging both to file and to stdout
logFormatter = logging.Formatter(
    "%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s"
)
logger = logging.getLogger()
fileHandler = logging.FileHandler("{0}/{1}.log".format("log", f"device{args.DeviceID}"))
fileHandler.setFormatter(logFormatter)
logger.addHandler(fileHandler)
consoleHandler = logging.StreamHandler(sys.stdout)
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)
logger.setLevel(logging.INFO)

# receive routine
def on_message(client, userdata, message):
    logger.debug("in: " + message.topic + "/" + str(message.payload.decode("utf-8")))

    # only message should be receiving data pool
    if message.topic == f"getPool{args.DeviceID}":
        logger.info(f"recieved pool")
        # load json data as object
        dic = json.loads(message.payload)
        # shuffle data to obscure in-order matching for AG
        shuffle(dic)
        logger.debug(dic)
        for entry in dic:
            logger.debug(f"treating {entry}")
            # get payload
            payload = entry["entry"]
            # convert to bytes
            as_bytes = bytes.fromhex(payload)
            # decipher payload
            res = decipher.decrypt(as_bytes)
            # interpret as measure
            m = Measure("none")
            m.unpack(res)

            logger.info(f"publishing measure {m.MUID}")
            client.publish("measures", str(m))


# padding function for cipher
def pad16(s):
    l = len(s)
    if l % 16 == 0:
        return s
    else:
        r = 16 - (l % 16)
        res = s + bytes(r)
        return res


# check for SF length
if len(args.SF_key) != 16:
    raise Exception("SF_key needs to be 16 bytes long")
    exit(1)

# connecting to MQTT broker
logger.info(f"Connecting to broker at {args.MQTT_broker}")
client = mqtt.Client(f"device-{args.DeviceID}")
# client.enable_logger()
client.connect(args.MQTT_broker)
client.loop_start()

# subscribing to pool receiving endpoint
logger.info("Subscribing to " + f"getPool{args.DeviceID}")
client.subscribe(f"getPool{args.DeviceID}")

# register receive routine
client.on_message = on_message

# db to log generated data
db = TinyDB(f"log/device{args.DeviceID}.json")

# mainloop
while True:
    # generate measure
    measure = Measure(args.DeviceID)
    # pack and pad payload
    payload = pad16(measure.pack())
    logger.info(f"produced {measure}")
    # log generated data for testing
    db.insert({"entry": str(measure)})

    logger.debug(f"payload: {payload.hex()}")

    # encrypt payload using SF
    encrypted = cipher.encrypt(payload)

    # publish data to AG
    client.publish("addToPool", encrypted.hex())

    logger.debug("publishing " + encrypted.hex() + " to topic /addToPool")

    time.sleep(5 + uniform(0, 1))

    # 10% chance of asking for table
    if randint(0, 10) < 1:
        # request pool. Data will be sent to appropriate endpoint by AG
        # and will be treated in the `on_message` routine
        client.publish("requestPool", f"{args.DeviceID}")