from util import mqttClient
from bleScanner import bleScanner
from util import utils
from util.utils import log
import uasyncio as asyncio
import config


def set_global_exception():
    def handle_exception(loop, context):
        import sys
        sys.print_exception(context["exception"])
        sys.exit()
    loop = asyncio.get_event_loop()
    loop.set_exception_handler(handle_exception)


async def scan_on_trigger():
    log("MQTT > Waiting for scan trigger...")
    while True:
        scan_result = await mqttClient.check_for_message()
        utils.free()
        if (config.SEND_MQTT):
            mqttClient.send_data(scan_result)
        await asyncio.sleep_ms(100)


async def scan_on_loop():
    while True:
        scan_result = await bleScanner.do_scan(
            utils.generate_uuid(),
            config.ACTIVE_SCAN,
            config.SCAN_DURATION_MS,
            config.SCAN_CONNECTION_TIMEOUT_MS,
            config.FILTER_RSSI
        )
        utils.free()
        if (config.SEND_MQTT):
            mqttClient.send_data(scan_result)
        log("BLE-Scanner: Waiting for next scan...")
        await asyncio.sleep_ms(config.TIME_BETWEEN_SCANS_MS)


async def main():
    set_global_exception()  # Debug aid
    task = None
    if (config.TIME_BETWEEN_SCANS_MS != -1):
        task = asyncio.create_task(scan_on_loop())
    else:
        task = asyncio.create_task(scan_on_trigger())
    await task
    log("Main Loop exited.")


try:
    asyncio.run(main())
finally:
    asyncio.new_event_loop()  # Clear retained state
