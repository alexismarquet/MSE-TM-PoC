# MSE TM Privacy PoC

This repository houses the proof of concept.

you will need a MQTT broker (eg: mosquitto), python3.9

## Device
1. generate measure
    * generate MUID
    * get data & metadata
2. pack measure
3. encrypt measure
    * use SF to encrypt usign AES-ECB
4. push measure
    * publish measure to `addToPool` as hex-encoded

also:

1. ask for pool
    * subscribe to `/getPool{$UID}`
    * publish `{$UID}` to `/requestPool`
2. get pool
    * wait for pool to be published on `/getPool{$UID}`
3. mix table
    * suffle
4. decrypt entries
    * Decrypt each entry using  AES-ECB
5. unpack entries
6. push unpacked entries as json? to `/measures`
    * Publish each entry individually


## AG

1. subscribe to pool endpoint
    * subscribe to `/addToPool`
2. subscribe to request endpoint
    * subscribe to `/requestPool`
3. store payloads
    * when something is published to `/addToPool`, store in DB
4. if someone asks for table, push table
    * when something is pushed to `requestPool`, push db entries to correct `/getPool{$UID}`
    * should we add header? like n of entries, or version of struct


## To run:

```shell
> mosquitto
```

```shell
> python3 agenceur.py localhost
```

```shell
> python3 device.py 1 localhost 0123456789012345 
```

where `1` is the device identifier, `0123456789012345` is the swarm key


## Run the demo 

```shell
> python3 demo.py 30 localhost 0123456789012345
```

where 30 is the number of devices in the swarm, localhost is the broker address, and `0123456789012345` is the swarm key.

stop the demo with ctrl+c and see the analysis of missing datapoints
