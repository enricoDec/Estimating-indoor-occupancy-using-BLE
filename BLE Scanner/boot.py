from util import wifiManager
from util import utils
from util import mqttClient
import time
import machine
import config

current_try = 0
max_retries = 5


def errorFallback():
    if (current_try < max_retries):
        print('Failed to connect to MQTT. Reconnecting...',
              current_try, "/", max_retries, ")")
        time.sleep(5)
        mqttClient.MQTTConnect()
    else:
        print("Max Retries reached. Resetting Device.")
        machine.reset()


utils.df()
if (config.NET):
    wifiManager.connect()
try:
    if (config.MQTT_START):
        mqttClient.MQTTConnect()
except OSError as e:
    errorFallback()
