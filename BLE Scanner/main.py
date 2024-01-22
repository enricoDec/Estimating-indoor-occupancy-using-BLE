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
        await asyncio.sleep_ms(100)


async def scan_on_loop():
    while True:
        scan_result = asyncio.run(bleScanner.do_scan_and_connect(
            utils.generate_uuid(),
            config.ACTIVE_SCAN,
            config.SCAN_DURATION_MS,
            config.SCAN_CONNECTION_TIMEOUT_MS,
            config.FILTER_RSSI
        ))
        utils.free()
        mqttClient.send_data(scan_result)
        utils.free()
        await asyncio.sleep_ms(config.TIME_BETWEEN_SCANS_MS)


async def main():
    if (config.TIME_BETWEEN_SCANS_MS != -1):
        asyncio.create_task(scan_on_loop())
    else:
        asyncio.create_task(scan_on_trigger())
    while True:
        await asyncio.sleep_ms(100) # add check for update here
    log("Main Loop exited.")


asyncio.run(main())