import struct
import sys
import hashlib
from random import randint
import time
import json


class Measure(object):
    def __init__(self, DevID):
        self.DevID = DevID
        self.generate()

    # def __init__(self, MUID, timestamp, position, data, reliability):
    #    self.MUID = MUID
    #    self.timestamp = timestamp
    #    self.position = position
    #    self.data = data
    #    self.reliability = reliability

    def generate(self):
        # get timestamp
        self.timestamp = int(time.time())

        # add device unique ID, timestamp, and rand 64bit int
        unhashedMUID = str(self.DevID) + str(self.timestamp) + str(randint(0, 2 ** 64))

        # encode initial message to utf-8, hash, and then save as string
        self.MUID = hashlib.sha256(unhashedMUID.encode("utf-8")).hexdigest()
        self.position = [0.0, 1.0]
        self.data = randint(0, 1000)
        self.reliability = 1.0

    def __repr__(self):
        d = {}
        d["MUID"] = self.MUID  # .decode("utf-8")
        d["timestamp"] = self.timestamp
        d["position"] = self.position
        d["data"] = self.data
        d["reliability"] = self.reliability
        return str(json.dumps(d))
        # return f"MUID:{self.MUID:#0{16}x}, timestamp:{self.timestamp}"

    def pack(self):
        # QQddQf
        p = struct.pack(
            "64sQddQf",
            self.MUID.encode("utf-8"),
            self.timestamp,
            self.position[0],
            self.position[1],
            self.data,
            self.reliability,
        )
        return p

    def unpack(self, payload):
        (
            self.MUID,
            self.timestamp,
            self.position[0],
            self.position[1],
            self.data,
            self.reliability,
        ) = struct.unpack("64sQddQf", payload[: struct.calcsize("64sQddQf")])
        self.MUID = self.MUID.decode("utf-8")
        return self
