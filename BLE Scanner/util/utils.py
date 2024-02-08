from util import wifiManager
import config
import gc
import os
import ntptime
import time


ntptime.host = "1.europe.pool.ntp.org"
synced = False


def df():
    s = os.statvfs('//')
    return ('{0} MB'.format((s[0]*s[3])/1048576))


def free(full=False):
    gc.collect()
    F = gc.mem_free()
    A = gc.mem_alloc()
    T = F+A
    P = '{0:.2f}%'.format(F/T*100)
    log('Memory - Total:{0} Free:{1} ({2})'.format(T, F, P), log_type=0)
    if not full:
        return P
    else:
        return ('Total:{0} Free:{1} ({2})'.format(T, F, P))


def log(text: str, newLine=True, log_type=1):
    # 0: Debug, 1: Info, 2: Warning, 3: Error
    if config.LOGGING and log_type >= config.LOG_LEVEL:
        print(text, end='\n' if newLine else '')


def current_date():
    now = time.localtime()
    date = "{}/{}/{}".format(now[2], now[1], now[0])
    return date


def current_time():
    now = time.localtime()
    minutes = 0
    if now[4] < 10:
        minutes = "{}{}".format(0, now[4])
    else:
        minutes = now[4]
    c_time = "{}:{}".format(now[3], minutes)
    return c_time


def get_timestamp():
    global synced
    if (synced == False):
        if (wifiManager.isConnected()):
            ntptime.settime()
            synced = True
    date_and_time = current_date() + " " + current_time()
    return date_and_time


def generate_uuid():
    return os.urandom(16).hex()


def get_room():
    room_name = config.MQTT_ROOM_NAME
    if (room_name == "doScan"):
        raise ValueError("Room name 'doScan' is not allowed")
    return config.MQTT_ROOM_NAME


def update_config(newConfig):
    # General Settings
    if "LOGGING" in newConfig:
        config.LOGGING = newConfig["LOGGING"]
    if "LOG_LEVEL" in newConfig:
        config.LOG_LEVEL = newConfig["LOG_LEVEL"]

    # MQTT client Settings
    if "MQTT_CLIENT_CONFIG" in newConfig:
        mqtt_config = newConfig["MQTT_CLIENT_CONFIG"]
        if "MQTT_BROKER_ADDRESS" in mqtt_config:
            config.MQTT_BROKER_ADDRESS = mqtt_config["MQTT_BROKER_ADDRESS"]
        if "MQTT_USER" in mqtt_config:
            config.MQTT_USER = mqtt_config["MQTT_USER"]
        if "MQTT_PASSWORD" in mqtt_config:
            config.MQTT_PASSWORD = mqtt_config["MQTT_PASSWORD"]
        if "MQTT_ROOM_NAME" in mqtt_config:
            config.MQTT_ROOM_NAME = mqtt_config["MQTT_ROOM_NAME"]
        if "MQTT_BASE_TOPIC" in mqtt_config:
            config.MQTT_BASE_TOPIC = mqtt_config["MQTT_BASE_TOPIC"]

    # Scanner config Settings
    if "SCANNER_CONFIG" in newConfig:
        scanner_config = newConfig["SCANNER_CONFIG"]
        if "TIME_BETWEEN_SCANS_MS" in scanner_config:
            config.TIME_BETWEEN_SCANS_MS = scanner_config["TIME_BETWEEN_SCANS_MS"]
        if "SCAN_DURATION_MS" in scanner_config:
            config.SCAN_DURATION_MS = scanner_config["SCAN_DURATION_MS"]
        if "SCAN_CONNECTION_TIMEOUT_MS" in scanner_config:
            config.SCAN_CONNECTION_TIMEOUT_MS = scanner_config["SCAN_CONNECTION_TIMEOUT_MS"]
        if "ACTIVE_SCAN" in scanner_config:
            config.ACTIVE_SCAN = scanner_config["ACTIVE_SCAN"]
        if "FILTER_RSSI" in scanner_config:
            config.FILTER_RSSI = scanner_config["FILTER_RSSI"]
