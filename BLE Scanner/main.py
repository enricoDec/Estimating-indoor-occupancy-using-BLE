from util import mqttClient
from bleScanner import bleScanner
from util import utils
from util.utils import log
import uasyncio as asyncio
import config


async def scan_on_trigger():
    log("MQTT > Waiting for scan trigger...")
    while True:
        await mqttClient.check_for_message()
        await asyncio.sleep_ms(100) # add check for update here


async def scan_on_loop():
    while True:
        scan_result = asyncio.run(bleScanner.do_scan_and_connect(
            utils.generate_uuid(),
            config.ACTIVE_SCAN,
            config.SCAN_DURATION,
            config.SCAN_CONNECTION_TIMEOUT,
            config.FILTER_RSSI
        ))
        utils.free()
        if (config.MQTT):
            mqttClient.send_data(scan_result)
        utils.free()
        await asyncio.sleep(config.TIME_BETWEEN_SCANS)


if (config.TIME_BETWEEN_SCANS != -1):
    asyncio.run(scan_on_loop())
else:
    try:
        asyncio.run(scan_on_trigger())
    except Exception as e:
        log("Loop ended with exception: " + str(e))
