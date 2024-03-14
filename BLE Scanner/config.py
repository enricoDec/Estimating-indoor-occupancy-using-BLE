import ujson as json
from micropython import const
from primitives import Queue
from util import utils

NET = const("NET")
MQTT = const("MQTT")
SEND_MQTT = const("SEND_MQTT")
ALLOW_CONFIG_UPDATE = const("ALLOW_CONFIG_UPDATE")
LOGGING = const("LOGGING")
LOG_LEVEL = const("LOG_LEVEL")
NTP_HOST = const("NTP_HOST")
SSID = const("SSID")
NETWORK_KEY = const("NETWORK_KEY")
MQTT_BROKER_ADDRESS = const("MQTT_BROKER_ADDRESS")
MQTT_USER = const("MQTT_USER")
MQTT_PASSWORD = const("MQTT_PASSWORD")
MQTT_ROOM_NAME = const("MQTT_ROOM_NAME")
MQTT_BASE_TOPIC = const("MQTT_BASE_TOPIC")
TIME_BETWEEN_SCANS_MS = const("TIME_BETWEEN_SCANS_MS")
SCAN_DURATION_MS = const("SCAN_DURATION_MS")
SCAN_CONNECTION_TIMEOUT_MS = const("SCAN_CONNECTION_TIMEOUT_MS")
ACTIVE_SCAN = const("ACTIVE_SCAN")
FILTER_RSSI = const("FILTER_RSSI")

config = {
    # True = Connect to WiFi on Startup
    NET: True,
    # True = Use MQTT. If set to False ALLOW_CONFIG_UPDATE and SEND_MQTT will be set to False
    MQTT: True,
    # True = Transfers Scands Data via MQTT after Scan
    SEND_MQTT: True,
    # Allow to update the configuration via MQTT
    ALLOW_CONFIG_UPDATE: True,
    # True = Prints Scanning Process, Results and other events
    LOGGING: True,
    # Log Level (0 = Debug (Includes info and more), 1 = Info, 2 = Warning, 3 = Error)
    LOG_LEVEL: 1,
    # NTP Server to use for time synchronization
    NTP_HOST: "pool.ntp.org",
    # WiFi SSID
    SSID: "FunnyWifiName",
    # WiFi Password
    NETWORK_KEY: "DefaultRouterPasswordThatYouShouldChange",
    # MQTT Broker Address
    MQTT_BROKER_ADDRESS: "localhost",
    # MQTT User set to None if no user is needed (anonymous access)
    MQTT_USER: "User",
    # MQTT Password set to None if no password is needed
    MQTT_PASSWORD: "Password",
    # This topic pattern is suggested, like this you can subscribe to all rooms with "roomUtilization/scans/#"
    # or to a specific room with "roomUtilization/scans/myRoom". The topic for triggering a scan is "roomUtilization/doScan"
    # doScan not allowed as room name (reserved for scan trigger)
    MQTT_ROOM_NAME: "myRoom",
    MQTT_BASE_TOPIC: "roomUtilization/",
    # Time in sec between each scan (Default 30000ms = 30s). Set TIME_BETWEEN_SCANS_MS to -1 if scan should be triggered via MQTT
    TIME_BETWEEN_SCANS_MS: 30000,
    # The actual duration of the scan in ms (would suggest at least 5000ms).
    SCAN_DURATION_MS: 10000,
    # Timeout in ms to connect to a device (for each connectable device)
    SCAN_CONNECTION_TIMEOUT_MS: 5000,
    # True = Active Scan | False = Passive Scan (Only listens for advertising packets sent by BLE devices, uses less power)
    ACTIVE_SCAN: True,
    # Only Include Devices with a higher RSSI (0 for no filter)
    FILTER_RSSI: -100
}

config_file = "config.json"


def get(flag):
    global config
    try:
        flag = config[flag]
        return flag
    except Exception:
        utils.log("Config > Config flag not found: " +
                  str(flag) + "\n Config is malformed!", 3)
        return None


def load(config_file=config_file):
    # load config the given config file
    global config
    try:
        with open(config_file, "r") as json_file:
            newConfig = _validate_and_update_config(json.load(json_file))
            if (newConfig == None):
                utils.log("Config > Critical error, config invalid!", 3)
                return
            config = newConfig
    except Exception:
        utils.log("Config > Critical error, no config file found!", 3)


def save(config_file=config_file):
    global config
    with open(config_file, "w") as json_file:
        json.dump(config, json_file)


def update_config(newConfig):
    global config
    newConfig = _validate_and_update_config(newConfig)
    if (newConfig == None):
        utils.log("MQTT > Invalid config. Ignoring...", 3)
        return
    if (config != newConfig):
        config = newConfig
        save()
        utils.log("Configuration updated: \n" + str(newConfig))
        utils.reboot()
    else:
        utils.log("MQTT > Current configuration is already up to date.")


async def handle_config_update(update_config_queue: Queue):
    if (update_config_queue != None and not update_config_queue.empty()):
        lastConfig = None
        # we want the latest config, so we discard the older ones
        while (not update_config_queue.empty()):
            # no race condition, as only one task gets the message
            lastConfig = await update_config_queue.get()
        utils.log("MQTT > Updating config...")
        update_config(lastConfig)


def _validate_and_update_config(config_to_validate):
    # check if config has all keys and values are of the right type
    global config
    for key in config:
        # carry over keys and values not present in the new config
        if key not in config_to_validate:
            config_to_validate[key] = config[key]
        # check if the type is the same, if not discard the new config (malformed config file)
        elif (config_to_validate[key] != None and type(config_to_validate[key]) != type(config[key])):
            utils.log("Config > Malformed config file, " + str(key) +
                      " has the wrong type!", 3)
            return None
    for key in config_to_validate:
        # if new config has keys not present in the current config, discard the new config (malformed config file)
        if key not in config:
            utils.log("Config > Malformed config file, " + str(key) +
                      " is not a valid config flag!", 3)
            return None
    adjust_config(config_to_validate)
    return config_to_validate


def adjust_config(config):
    # If NET is disabled, MQTT should be disabled as well
    if (config[NET] == False):
        config[MQTT] = False
    # If MQTT is disabled, ALLOW_CONFIG_UPDATE and SEND_MQTT should be disabled as well
    if (config[MQTT] == False):
        utils.log(
            "Config > NET and or MQTT is disabled. Disabling ALLOW_CONFIG_UPDATE and SEND_MQTT", 2)
        config[ALLOW_CONFIG_UPDATE] = False
        config[SEND_MQTT] = False
