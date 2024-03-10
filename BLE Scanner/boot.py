import util.wifiManager as wifiManager
import util.utils as utils
import config
import mip

utils.df()
config.load()
if (config.get(config.NET)):
    wifiManager.connect()
    if (wifiManager.isConnected()):
        try:
            import aioble
        except ImportError:
            mip.install("aioble")
        try:
            import primitives
        except ImportError:
            mip.install("github:peterhinch/micropython-async/v3/primitives")
try:
    if (config.MQTT):
        from util import mqttClient
        mqttClient.MQTTConnect()
except OSError:
    mqttClient.errorFallback()
