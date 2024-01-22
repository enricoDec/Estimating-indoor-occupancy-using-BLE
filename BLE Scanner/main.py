from bleScanner import bleScanner
from util import mqttClient
from util import utils
from util.utils import log
import uasyncio as asyncio
from primitives import Queue
import config


def set_global_exception():
    def handle_exception(loop, context):
        import sys
        sys.print_exception(context["exception"])
        sys.exit()
    loop = asyncio.get_event_loop()
    loop.set_exception_handler(handle_exception)

async def scan_on_timer():
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
            mqttClient.send_data_if_enabled(scan_result)
        log("BLE-Scanner: Waiting " + str(config.TIME_BETWEEN_SCANS_MS) + "ms for next scan...")
        await asyncio.sleep_ms(config.TIME_BETWEEN_SCANS_MS)

async def scan_on_trigger(queue):
    log("MQTT > Waiting for scan trigger...")
    while True:
        triggerJSon = await queue.get()
        log("MQTT > Scan Triggered!")
        scan_result = await bleScanner.do_scan(
            triggerJSon["uuid"],
            config.ACTIVE_SCAN,
            config.SCAN_DURATION_MS,
            config.SCAN_CONNECTION_TIMEOUT_MS,
            config.FILTER_RSSI
        )
        mqttClient.send_data_if_enabled(scan_result)

async def check_for_trigger(queue):
    # wait for trigger message and put it in the queue
    while True:
        triggerJSon = await mqttClient.check_for_trigger()
        if triggerJSon != None:
            utils.free()
            await queue.put(triggerJSon)
            log("MQTT > Scan(s) queued " + str(queue.qsize()))
            triggerJSon = None
        await asyncio.sleep_ms(100)

async def main():
    set_global_exception()  # Debug aid
    task = None
    if (config.TIME_BETWEEN_SCANS_MS != -1):
        task = asyncio.create_task(scan_on_timer())
    else:
        queue = Queue()
        asyncio.create_task(check_for_trigger(queue))
        task = asyncio.create_task(scan_on_trigger(queue))
    await task
    log("Main Loop exited.")


try:
    asyncio.run(main())
finally:
    asyncio.new_event_loop()  # Clear retained state
