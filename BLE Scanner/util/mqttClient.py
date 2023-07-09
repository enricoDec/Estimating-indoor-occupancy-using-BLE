from umqtt.simple import MQTTClient
from util import wifiManager
from util import utils
from util.utils import log
from binascii import hexlify
from bleScanner import bleScanner
import uasyncio as asyncio
import machine
import time
import ujson
import config

scanTopic = config.MQTT_BASE_TOPIC + "scans/" + config.MQTT_ROOM_NAME
triggerTopic = config.MQTT_BASE_TOPIC + "doScan"
brokerAddr = config.MQTT_BROKER_ADDRESS
mqttc = MQTTClient(hexlify(machine.unique_id()),
                   brokerAddr, port=1883, keepalive=60)

encode = True
buffer = None


def MQTTConnect():
    try:
        log("MQTT > Broker Address: " + str(brokerAddr))
        log("MQTT TOPIC > Scan result published on: " + str(scanTopic))
        mqttc.set_callback(sub_cb)
        mqttc.connect()
        mqttc.set_last_will(scanTopic, "Offline", retain=True)
        log("MQTT > Connected to Broker!")
        mqttc.subscribe(triggerTopic.encode())
        log("MQTT > Subscribed to: " + str(triggerTopic))
        utils.free()
    except OSError:
        MQTTConnect()


def sub_cb(topic, msg):
    scanTrigger = ujson.loads(msg)
    log("MQTT > Message received: " + str(topic.decode()) + " " + str(scanTrigger))
    if "all" in scanTrigger["room"] or config.MQTT_ROOM_NAME in scanTrigger["room"]:
        scan_result = asyncio.run(bleScanner.do_scan_and_connect(
            scanTrigger["uuid"],
            config.ACTIVE_SCAN,
            config.SCAN_DURATION,
            config.SCAN_CONNECTION_TIMEOUT,
            config.FILTER_RSSI
        ))
        utils.free()
        if (config.MQTT):
            send_data(scan_result)
        utils.free()


def check_for_message():
    try:
        mqttc.check_msg()
    except OSError:
        # ignore lib throws OSError -1 when no message is received?!
        pass


def send_data(data):
    if data is None:
        return None
    global encode
    global buffer

    if encode:
        buffer = ujson.dumps(data)

    if (wifiManager.isConnected()):
        log(scanTopic + str("MQTT > Sending Data..."))
        try:
            mqttc.publish(scanTopic, buffer.encode())
            encode = True
            utils.free()
        except OSError:
            log("Publishing failed. Retrying...")
            time.sleep(3)
            MQTTConnect()
            encode = False
            send_data(buffer)

    else:
        log("MQTT > Lost Network Connection ...")
        wifiManager.connect()
        encode = False
        send_data(buffer)
