from util import wifiManager
import config
import gc
import os
import ntptime
import time
import machine
import uasyncio as asyncio


ntptime.host = config.get(config.NTP_HOST)
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
    if config.get(config.LOGGING) and log_type >= config.get(config.LOG_LEVEL):
        print(str(text).strip(), end='\n' if newLine else '')


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


def get_timestamp_formatted():
    global synced
    if (synced == False):
        if (wifiManager.isConnected()):
            ntptime.settime()
            synced = True
    date_and_time = current_date() + " " + current_time()
    return date_and_time

def get_timestamp_epoch():
    global synced
    if (synced == False):
        if (wifiManager.isConnected()):
            ntptime.settime()
            synced = True
    return time.time()


def generate_uuid():
    return os.urandom(16).hex()


def get_room():
    room_name = config.get(config.MQTT_ROOM_NAME)
    if (room_name == "doScan"):
        raise ValueError("Room name 'doScan' is not allowed")
    return config.get(config.MQTT_ROOM_NAME)

def reboot():
    log("Rebooting...\n", 2)
    asyncio.new_event_loop()  # Clear retained state
    machine.reset()