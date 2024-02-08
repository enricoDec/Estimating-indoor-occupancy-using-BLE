from util import wifiManager
from util import utils
import config
import mip

utils.df()
if (config.NET):
    wifiManager.connect()
if (wifiManager.isConnected()):
    # check if aioble is installed
    try:
        import aioble
    except ImportError:
        mip.install("aioble")
    try:
        import primitives
    except ImportError:
        mip.install("github:peterhinch/micropython-async/v3/primitives")
try:
    if (config.MQTT_START):
        from util import mqttClient
        mqttClient.MQTTConnect()
except OSError:
    mqttClient.errorFallback()
