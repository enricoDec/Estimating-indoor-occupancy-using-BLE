from umqtt.simple import MQTTClient
from util import wifiManager
from util import utils
from util.utils import log
from binascii import hexlify
from bleScanner import bleScanner
import machine
import time
import ujson
import config

scanTopic = config.MQTT_BASE_TOPIC + "scans/" + config.MQTT_ROOM_NAME
triggerTopic = config.MQTT_BASE_TOPIC + "doScan"
brokerAddr = config.MQTT_BROKER_ADDRESS
mqttc = MQTTClient(hexlify(machine.unique_id()),
                   brokerAddr, port=1883, keepalive=60)

scanTrigger = None
current_try = 0
max_retries = 5


def MQTTConnect():
    global current_try
    if current_try == 0:
        log("MQTT > Broker Address: " + str(brokerAddr))
        log("MQTT TOPIC > Scan result will be published to: " + str(scanTopic))
    mqttc.set_callback(sub_cb)
    mqttc.connect()
    mqttc.set_last_will(scanTopic, "Offline", retain=True)
    log("MQTT > Connected to Broker!")
    mqttc.subscribe(triggerTopic.encode())
    log("MQTT > Subscribed to: " + str(triggerTopic))
    utils.free()


def errorFallback():
    global current_try
    global max_retries
    if (current_try < max_retries):
        log("Failed to connect to MQTT. Reconnecting... ({} / {})".format(
            current_try + 1, max_retries))
        time.sleep(5)
        current_try = current_try + 1
        try:
            MQTTConnect()
        except OSError:
            errorFallback()
    else:
        log("Max Retries reached. Scan results will not be sent to MQTT")
        config.SEND_MQTT = False


def sub_cb(topic, msg):
    msgJSon = ujson.loads(msg)
    log("MQTT > Trigger received: " + str(topic.decode()) + " " + str(msgJSon))
    if "all" in msgJSon["room"] or config.MQTT_ROOM_NAME in msgJSon["room"]:
        global scanTrigger
        scanTrigger = msgJSon
        log("MQTT > Scan Triggered!")


async def check_for_message() -> list:
    try:
        mqttc.check_msg()
    except OSError:
        # ignore mqtt.simple throws OSError -1 when a message is received but is empty?
        return None
    global scanTrigger
    if scanTrigger != None:
        scan_result = await bleScanner.do_scan(
            scanTrigger["uuid"],
            config.ACTIVE_SCAN,
            config.SCAN_DURATION_MS,
            config.SCAN_CONNECTION_TIMEOUT_MS,
            config.FILTER_RSSI
        )
        scanTrigger = None
        return scan_result


def send_data(data):
    if data is None:
        return None
    buffer = ujson.dumps(data)
    log("MQTT > Sending Data: " + str(buffer) + " to " + str(scanTopic))
    if (wifiManager.isConnected()):
        try:
            mqttc.publish(scanTopic, buffer.encode('UTF8'))
            utils.free()
        except OSError:
            log("Publishing failed. Retrying...")
            time.sleep(3)
            MQTTConnect()
            send_data(buffer)
    else:
        log("MQTT > No Connection. Reconnecting...")
        wifiManager.connect()
        send_data(buffer)
