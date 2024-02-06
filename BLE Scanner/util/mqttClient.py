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

scanTopic = config.MQTT_BASE_TOPIC + "scans/" + utils.get_room()
triggerTopic = config.MQTT_BASE_TOPIC + "doScan"
brokerAddr = config.MQTT_BROKER_ADDRESS
mqttUser = config.MQTT_USER
mqttPwd = config.MQTT_PASSWORD
mqttc = None

scanTrigger = None
current_try = 0
max_retries = 5


def MQTTConnect():
    global mqttc
    mqttc = MQTTClient(hexlify(machine.unique_id()),
                       brokerAddr, port=1883, user=mqttUser, password=mqttPwd, keepalive=60)
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
        log("Max Retries reached, rebooting...")
        machine.reset()


def sub_cb(topic, msg):
    msgJSon = ujson.loads(msg)
    if "all" in msgJSon["room"] or utils.get_room() in msgJSon["room"]:
        global scanTrigger
        scanTrigger = msgJSon


async def check_for_trigger() -> list:
    # this mess is necessary because mqtt.simple is a garbage library, might be worth looking into alternatives such as https://github.com/fizista/micropython-umqtt.simple2
    try:
        global mqttc
        mqttc.check_msg()
    except OSError:
        # ignore mqtt.simple throws OSError -1 when a message is received but is empty?
        return None
    global scanTrigger
    if (scanTrigger != None):
        trigger = scanTrigger
        scanTrigger = None
        return trigger


def send_data_if_enabled(data):
    if data is None or config.SEND_MQTT == False:
        return None
    utils.free()
    buffer = ujson.dumps(data)
    log("MQTT > Sending Data to " + str(scanTopic))
    if (wifiManager.isConnected()):
        try:
            global mqttc
            mqttc.publish(scanTopic, buffer.encode())
            utils.free()
        except OSError as e:
            log("Publishing failed\n: " + str(e))
            errorFallback()
            send_data_if_enabled(buffer)
    else:
        log("MQTT > No Connection. Reconnecting...")
        wifiManager.connect()
        send_data_if_enabled(buffer)
