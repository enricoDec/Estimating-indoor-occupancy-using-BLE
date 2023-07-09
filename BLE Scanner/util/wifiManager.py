from util.utils import log
import config
import time
import network
import machine

station = network.WLAN(network.STA_IF)

current_try = 0
max_retries = 10


def connect():
    ssid = config.SSID
    password = config.NETWORK_KEY

    if station.isconnected() == True:
        log("WiFiMananger > Already connected")
        return

    station.active(True)
    try:
        station.connect(ssid, password)
    except OSError as e:
        global current_try
        global max_retries

        if (current_try < max_retries):
            log("WiFiMananger > Failed to connect. Retrying... (" +
                      str(current_try) + "/" + str(max_retries) + ")")
            log("WiFiMananger > status:" + str(station.status()))
            time.sleep(5)
            current_try = current_try + 1
            connect()
        else:
            log("Max Retry Limit reached... Rebooting Device.")
            current_try = 0
            machine.reset()

    while station.isconnected() == False:
        pass

    log("WiFiMananger > Connection successful")


def disconnect():
    log("WiFiMananger > Disconnecting")
    station.disconnect()


def isConnected():
    return station.isconnected()
