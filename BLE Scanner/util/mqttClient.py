from umqtt.simple import MQTTClient
from bleScanner.deviceInfo import DeviceInfo
from util import wifiManager
from util import utils
from util.utils import log
from binascii import hexlify
from primitives import Queue
from primitives.queue import QueueFull
from asyncio import Lock
import uasyncio as asyncio
import machine
import time
import ujson
import config

SCAN_TOPIC = config.get(config.MQTT_BASE_TOPIC) + "scans/" + utils.get_room()
TRIGGER_TOPIC = config.get(config.MQTT_BASE_TOPIC) + "doScan"
UPDATE_TOPIC = config.get(config.MQTT_BASE_TOPIC) + "updateConfig"
BROKER_ADDR = config.get(config.MQTT_BROKER_ADDRESS)
MQTT_USER = config.get(config.MQTT_USER)
MQTT_PWD = config.get(config.MQTT_PASSWORD)
mqttc = None
connection_current_try = 0
connection_max_retries = 5

topic_subscribers: dict[str, Queue] = {}
topic_subscribers_lock = Lock()


def MQTTConnect():
    global mqttc
    mqttc = MQTTClient(hexlify(machine.unique_id()),
                       BROKER_ADDR, port=1883, user=MQTT_USER, password=MQTT_PWD, keepalive=60)
    global connection_current_try
    if connection_current_try == 0:
        log("MQTT > Broker Address: " + str(BROKER_ADDR))
        log("MQTT > Scan result will be published to: " + SCAN_TOPIC)
    mqttc.set_callback(sub_cb)
    mqttc.connect()
    mqttc.set_last_will(SCAN_TOPIC.encode(), "Offline", retain=True)
    log("MQTT > Connected to Broker!")
    mqttc.subscribe(TRIGGER_TOPIC.encode())
    if config.ALLOW_CONFIG_UPDATE:
        mqttc.subscribe(UPDATE_TOPIC.encode())
    log("MQTT > Subscribed to: " + TRIGGER_TOPIC)
    utils.free()


async def subscribe_topic(topic) -> Queue:
    async with topic_subscribers_lock:
        messageQueue = Queue()  # for now we only have one subscriber per topic
        topic_subscribers[topic] = messageQueue
    return messageQueue


async def check_messages():
    while True:
        try:
            mqttc.check_msg()
            await asyncio.sleep_ms(500)
        except OSError:
            # ignore mqtt.simple throws OSError -1 when a message is received but is empty?
            pass


def sub_cb(topic, msg):
    topic = topic.decode()
    log("MQTT > Message received on topic: " + str(topic))
    if topic in topic_subscribers:
        try:
            msgJSon = ujson.loads(msg)
            # trigger scan
            if (topic == TRIGGER_TOPIC):
                scansonTrigger = config.get(config.TIME_BETWEEN_SCANS_MS) != -1
                if (scansonTrigger and "all" in msgJSon["room"] or utils.get_room() in msgJSon["room"]):
                    topic_subscribers[topic].put_nowait(msgJSon)
            # update config
            elif (topic == UPDATE_TOPIC and config.ALLOW_CONFIG_UPDATE):
                topic_subscribers[topic].put_nowait(msgJSon)
        except QueueFull:
            log("MQTT > " + str(topic) + " Queue is full, dropping message")
        except ValueError:
            log("MQTT > " + str(topic) + " Message is not valid JSON")


def send_data(uuid, device_infos: list[DeviceInfo]):
    if device_infos is None or config.get(config.SEND_MQTT) == False:
        log("MQTT > No data send")
        return None
    utils.free()
    total_parts = (len(device_infos) + 9) // 10  # ceil(len(device_infos) / 10)
    for i in range(0, len(device_infos), 10):
        current_part = int(i/10) + 1  # starts at 1
        data = {
            'timestamp_utc': utils.get_timestamp(),
            'scanresult': [device_info.__dict__ for device_info in device_infos[i:i+10]],
            'uuid': str(uuid),
            'room': utils.get_room(),
            'part': current_part,
            'totalParts': total_parts
        }
        data = ujson.dumps(data)
        log("MQTT > Sending Data Part ({}/{}) to {}".format(current_part,
            total_parts, SCAN_TOPIC))
        if (wifiManager.isConnected()):
            try:
                global mqttc
                mqttc.publish(SCAN_TOPIC.encode(), data.encode())
            except OSError as e:
                log("Publishing failed\n: " + str(e))
                errorFallback()
                send_data(uuid, device_infos[i:])
        else:
            log("MQTT > No Connection. Reconnecting...")
            wifiManager.connect()
            send_data(uuid, device_infos[i:])
        utils.free()


def errorFallback():
    global connection_current_try
    global connection_max_retries
    if (connection_current_try < connection_max_retries):
        log("Failed to connect to MQTT. Reconnecting... ({} / {})".format(
            connection_current_try + 1, connection_max_retries))
        time.sleep(5)
        connection_current_try = connection_current_try + 1
        try:
            MQTTConnect()
            connection_current_try = 0
        except OSError:
            errorFallback()
    else:
        log("Max Retries reached, rebooting...")
        utils.reboot()
