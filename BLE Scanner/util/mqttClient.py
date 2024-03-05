from umqtt.simple import MQTTClient
from bleScanner.deviceInfo import DeviceInfo
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
updateTopic = config.MQTT_BASE_TOPIC + "updateConfig"
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
        log("MQTT TOPIC > Scan result will be published to: " + scanTopic)
    mqttc.set_callback(sub_cb)
    mqttc.connect()
    mqttc.set_last_will(scanTopic.encode(), "Offline", retain=True)
    log("MQTT > Connected to Broker!")
    mqttc.subscribe(triggerTopic.encode())
    if config.ALLOW_CONFIG_UPDATE:
        mqttc.subscribe(updateTopic.encode())
    log("MQTT > Subscribed to: " + triggerTopic)
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
            current_try = 0
        except OSError:
            errorFallback()
    else:
        log("Max Retries reached, rebooting...")
        machine.reset()


def sub_cb(topic, msg):
    # trigger received
    topic = topic.decode()
    if (topic == triggerTopic):
        msgJSon = ujson.loads(msg)
        if "all" in msgJSon["room"] or utils.get_room() in msgJSon["room"]:
            global scanTrigger
            scanTrigger = msgJSon
    # update config
    if (config.ALLOW_CONFIG_UPDATE and topic == updateTopic):
        newConfig = ujson.loads(msg)
        utils.update_config(newConfig)
        log("MQTT > Configuration updated: \n" + str(newConfig))


async def check_for_trigger() -> list:
    # this mess is necessary because mqtt.simple is a wonderful library, might be worth looking into alternatives such as https://github.com/fizista/micropython-umqtt.simple2
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


def send_data(uuid, device_infos: list[DeviceInfo]):
    if device_infos is None or config.SEND_MQTT == False:
        log("MQTT > No data send")
        return None
    utils.free()
    total_parts = (len(device_infos) + 9) // 10 # ceil(len(device_infos) / 10)
    for i in range(0, len(device_infos), 10):
        current_part = int(i/10) + 1 # starts at 1
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
            total_parts, scanTopic))
        if (wifiManager.isConnected()):
            try:
                global mqttc
                mqttc.publish(scanTopic.encode(), data.encode())
            except OSError as e:
                log("Publishing failed\n: " + str(e))
                errorFallback()
                send_data(uuid, device_infos[i:])
        else:
            log("MQTT > No Connection. Reconnecting...")
            wifiManager.connect()
            send_data(uuid, device_infos[i:])
        utils.free()
