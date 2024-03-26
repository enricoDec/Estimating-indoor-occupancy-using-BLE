from bleScanner.deviceInfo import DeviceInfo
from util.mqtt_as import MQTTClient as _MQTTClient, config as mqtt_config
from util import utils
from util.utils import log
from primitives import Queue
from primitives.queue import QueueFull
from asyncio import Lock
import uasyncio as asyncio
import time
import ujson
import config


SCAN_TOPIC = config.get(config.MQTT_BASE_TOPIC) + "scans/" + utils.get_room()
TRIGGER_TOPIC = config.get(config.MQTT_BASE_TOPIC) + "doScan"
UPDATE_TOPIC = config.get(config.MQTT_BASE_TOPIC) + "updateConfig"
BROKER_ADDR = config.get(config.MQTT_BROKER_ADDRESS)
MQTT_USER = config.get(config.MQTT_USER)
MQTT_PWD = config.get(config.MQTT_PASSWORD)
mqtt_client = None

topic_subscribers: dict[str, Queue] = {}
topic_subscribers_lock = Lock()


async def connect():
    global mqtt_client
    mqtt_config['ssid'] = config.get(config.SSID)
    mqtt_config['wifi_pw'] = config.get(config.NETWORK_KEY)
    mqtt_config['server'] = BROKER_ADDR
    mqtt_config['user'] = MQTT_USER
    mqtt_config['password'] = MQTT_PWD
    mqtt_config["queue_len"] = 1
    mqtt_config['keepalive'] = 120
    mqtt_client = MQTTClient(mqtt_config)
    mqtt_client.DEBUG = True
    log("MQTT > Broker Address: " + str(BROKER_ADDR))
    log("MQTT > Scan result will be published to: " + SCAN_TOPIC)
    await mqtt_client.connect()
    utils.free()


async def up():  # Respond to connectivity being (re)established
    global mqtt_client
    while True:
        await mqtt_client.up.wait()  # Wait on an Event
        mqtt_client.up.clear()
        if config.get(config.TIME_BETWEEN_SCANS_MS) == -1:
            await mqtt_client.subscribe(TRIGGER_TOPIC, 1)
            log("MQTT > Subscribed to: " + TRIGGER_TOPIC)
        if config.get(config.ALLOW_CONFIG_UPDATE):
            await mqtt_client.subscribe(UPDATE_TOPIC, 1)
            log("MQTT > Subscribed to: " + UPDATE_TOPIC)


async def messages():  # Respond to incoming messages
    global mqtt_client
    async for topic, msg, retained in mqtt_client.queue:
        topic = topic.decode()
        log("MQTT > Message received on topic: " + str(topic))
        async with topic_subscribers_lock:
            global topic_subscribers
            if topic in topic_subscribers:
                try:
                    msgJSon = ujson.loads(msg)
                    # trigger scan
                    if (topic == TRIGGER_TOPIC):
                        scanOnTrigger = config.get(
                            config.TIME_BETWEEN_SCANS_MS) == -1
                        if (scanOnTrigger and ("all" in msgJSon["room"] or utils.get_room() in msgJSon["room"])):
                            topic_subscribers[topic].put_nowait(msgJSon)
                    # update config
                    elif (topic == UPDATE_TOPIC and config.get(config.ALLOW_CONFIG_UPDATE)):
                        topic_subscribers[topic].put_nowait(msgJSon)
                except QueueFull:
                    log("MQTT > " + str(topic) +
                        " Queue is full, dropping message")
                except ValueError:
                    log("MQTT > " + str(topic) + " Message is not valid JSON")


async def register_topic_subscriber(topic) -> Queue:
    async with topic_subscribers_lock:
        messageQueue = Queue()  # for now we only have one subscriber per topic
        global topic_subscribers
        topic_subscribers[topic] = messageQueue
    return messageQueue


async def send_data(uuid, device_infos: list[DeviceInfo]):
    if device_infos is None or config.get(config.SEND_MQTT) == False:
        log("MQTT > No data send")
        return None
    utils.free()
    total_parts = (len(device_infos) + 9) // 10  # ceil(len(device_infos) / 10)
    timestamp_utc = utils.get_timestamp_epoch()
    for i in range(0, len(device_infos), 10):
        current_part = int(i/10) + 1  # starts at 1
        data = {
            'timestamp_utc': timestamp_utc,
            'scanresult': [device_info.__dict__ for device_info in device_infos[i:i+10]],
            'uuid': str(uuid),
            'room': utils.get_room(),
            'part': current_part,
            'totalParts': total_parts
        }
        data = ujson.dumps(data)
        timeout = await mqtt_client.publish(SCAN_TOPIC, data, qos=1, timeout=config.get(config.MQTT_SEND_TIMEOUT_MS))
        if timeout:
            log("MQTT > Timeout while sending Part ({}/{}) to {}".format(current_part,
                                                                         total_parts, SCAN_TOPIC))
        else:
            log("MQTT > Sent Data Part ({}/{}) to {}".format(current_part,
                                                             total_parts, SCAN_TOPIC))
        utils.free()


def close():
    global mqtt_client
    if mqtt_client is not None:
        mqtt_client.close()
        mqtt_client = None
        log("MQTT > Disconnected from Broker")
    utils.free()


# (C) Copyright 2019 Kevin Köck.
# Released under the MIT licence.
class MQTTClient(_MQTTClient):
    _pub_task = None

    # Await broker connection. Subclassed to reduce canceling time from 1s to 50ms
    async def _connection(self):
        while not self._isconnected:
            await asyncio.sleep_ms(50)

    async def _publishTimeout(self, topic, msg, retain, qos):
        try:
            await super().publish(topic, msg, retain, qos)
        finally:
            self._pub_task = None

    async def publish(self, topic, msg, retain=False, qos=0, timeout=None):
        task = None
        start = time.ticks_ms()
        while timeout is None or time.ticks_diff(time.ticks_ms(), start) < timeout:
            # Can't use wait_for because cancelling a wait_for would cancel _publishTimeout
            # Also a timeout in wait_for would cancel _publishTimeout without waiting for
            # the socket lock to be available, breaking mqtt protocol.
            if self._pub_task is None and task is None:
                task = asyncio.create_task(
                    self._publishTimeout(topic, msg, retain, qos))
                self._pub_task = task
            elif task is not None:
                if self._pub_task != task:
                    return False  # published
            await asyncio.sleep_ms(20)
        if task is not None:
            async with self.lock:
                task.cancel()
                return True
