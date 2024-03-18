from bleScanner import bleScanner
from util import mqttClient
from util import utils
from util.utils import log
import uasyncio as asyncio
from primitives import Queue
import config


async def scan_on_timer(update_config_queue: Queue):
    while True:
        try:
            scanUUID = utils.generate_uuid()
            device_infos = await bleScanner.do_scan(
                config.get(config.ACTIVE_SCAN),
                config.get(config.SCAN_DURATION_MS),
                config.get(config.SCAN_CONNECTION_TIMEOUT_MS),
                config.get(config.FILTER_RSSI)
            )
            mqttClient.send_data(scanUUID, device_infos)
            await config.handle_config_update(update_config_queue)
            sleep_time = config.get(config.TIME_BETWEEN_SCANS_MS)
            log("BLE-Scanner: Waiting " +
                str(sleep_time) + "ms for next scan...")
            await asyncio.sleep_ms(sleep_time)
        except (Exception, OSError) as e:
            log("Error in scan_on_timer Tasks: " + str(e), log_type=3)


async def scan_on_trigger(trigger_queue: Queue, update_config_queue: Queue):
    log("MQTT > Waiting for scan trigger...")
    while True:
        try:
            scanUUID = utils.generate_uuid()
            log("MQTT > Scan(s) queued " + str(trigger_queue.qsize()))
            await trigger_queue.get()
            log("MQTT > Scan Triggered!")
            device_infos = await bleScanner.do_scan(
                config.get(config.ACTIVE_SCAN),
                config.get(config.SCAN_DURATION_MS),
                config.get(config.SCAN_CONNECTION_TIMEOUT_MS),
                config.get(config.FILTER_RSSI)
            )
            mqttClient.send_data(scanUUID, device_infos)
            # TODO: this could potentially never be reached if no trigger is received
            await config.handle_config_update(update_config_queue)
        except (Exception, OSError) as e:
            log("Error in scan_on_trigger Task: " + str(e), log_type=3)


def set_global_exception():
    def handle_exception(loop, context):
        import sys
        exception = context.get('exception')
        log("Exception in loop: " + str(loop) + " " + str(exception), log_type=3)
        if exception:
            sys.print_exception(exception)
            # TODO: When deploying, reboot on exception
            # utils.reboot()
    loop = asyncio.get_event_loop()
    loop.set_exception_handler(handle_exception)


async def main():
    log("Free Mem: " + utils.df())
    log("Time: " + utils.get_timestamp())
    set_global_exception()  # Debug aid
    tasks = []
    update_config_queue = None
    if (config.get(config.ALLOW_CONFIG_UPDATE)):
        update_config_queue = await mqttClient.subscribe_topic(mqttClient.UPDATE_TOPIC)
    # Start the task depending on the configuration
    if (config.get(config.TIME_BETWEEN_SCANS_MS) != -1):
        tasks.append(asyncio.create_task(scan_on_timer(update_config_queue)))
        if (update_config_queue != None):
            tasks.append(asyncio.create_task(mqttClient.check_messages()))
    else:
        trigger_queue = await mqttClient.subscribe_topic(
            mqttClient.TRIGGER_TOPIC)
        tasks.append(asyncio.create_task(scan_on_trigger(
            trigger_queue, update_config_queue)))
        tasks.append(asyncio.create_task(mqttClient.check_messages()))
    try:
        res = await asyncio.gather(*tasks, return_exceptions=True)
        log("Main Loop exited with error: " + str(res))
    except Exception as e:
        log("Error in main loop: " + str(e), log_type=3)


try:
    asyncio.run(main())
finally:
    asyncio.new_event_loop()  # Clear retained state
