from util import wifiManager
from util import utils
from util import mqttClient
import config

utils.df()
if (config.NET):
    wifiManager.connect()
try:
    if (config.MQTT_START):
        mqttClient.MQTTConnect()
except OSError:
    mqttClient.errorFallback()
