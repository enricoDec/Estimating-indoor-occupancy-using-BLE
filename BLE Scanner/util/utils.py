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


def free(full=False, logging=False):
    gc.collect()
    F = gc.mem_free()
    A = gc.mem_alloc()
    T = F+A
    P = '{0:.2f}%'.format(F/T*100)
    if (logging):
        log('Memory - Total:{0} Free:{1} ({2})'.format(T, F, P))
    if not full:
        return P
    else:
        return ('Total:{0} Free:{1} ({2})'.format(T, F, P))


def log(text: str, newLine=True):
    if config.LOGGING:
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