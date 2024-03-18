import util.wifiManager as wifi
import util.utils as utils
import config
import mip

utils.df()
config.load()
if (config.get(config.NET)):
    wifi.connect()
    if (wifi.isConnected()):
        try:
            import aioble
        except ImportError:
            mip.install("aioble")
        try:
            import primitives
        except ImportError:
            mip.install("github:peterhinch/micropython-async/v3/primitives")
    try:
        if (config.get(config.MQTT)):
            from util import mqttClient
            mqttClient.MQTTConnect()
    except OSError:
        mqttClient.errorFallback()
