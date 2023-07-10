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
    msgJSon = ujson.loads(msg)
    log("MQTT > Trigger received: " + str(topic.decode()) + " " + str(msgJSon))
    if "all" in msgJSon["room"] or config.MQTT_ROOM_NAME in msgJSon["room"]:
        global scanTrigger
        scanTrigger = msgJSon


async def check_for_message():
    try:
        mqttc.check_msg()
    except OSError:
        # ignore mqtt.simple throws OSError -1 when a message is received but is empty?
        return None
    global scanTrigger
    if scanTrigger != None:
        scan_result = await bleScanner.do_scan_and_connect(
            scanTrigger["uuid"],
            config.ACTIVE_SCAN,
            config.SCAN_DURATION,
            config.SCAN_CONNECTION_TIMEOUT,
            config.FILTER_RSSI
        )
        utils.free()
        if (config.MQTT):
            send_data(scan_result)
        utils.free()
        scanTrigger = None
        log("MQTT > Waiting for scan trigger...")


def send_data(data):
    if data is None:
        return None
    
    buffer = ujson.dumps(data)
    log("MQTT > Sending Data: " + str(buffer) + " to " + str(scanTopic))

    if (wifiManager.isConnected()):
        try:
            mqttc.publish(scanTopic, buffer.encode())
            utils.free()
        except OSError:
            log("Publishing failed. Retrying...")
            time.sleep(3)
            MQTTConnect()
            send_data(buffer)
    else:
        log("MQTT > Lost Network Connection ...")
        wifiManager.connect()
        send_data(buffer)
