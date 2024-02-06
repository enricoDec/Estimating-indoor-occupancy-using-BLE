from util import utils
from util.utils import log
from binascii import hexlify
from aioble import GattError
from aioble.device import Device
from aioble.device import DeviceConnection
from aioble.client import ClientCharacteristic
from aioble.central import ScanResult
from bleScanner.deviceInfo import DeviceInfo
from asyncio import Lock
import aioble
import ujson
import sys
import uasyncio as asyncio
import bluetooth

sys.path.append("")
aioble.core.log_level = -1

_deviceInfoServiceUUID = bluetooth.UUID(0x180A)
_modelNumberStringCharUUID = bluetooth.UUID(0x2A24)
_manufacturerStringCharUUID = bluetooth.UUID(0x2A29)
_completeLocalNameDataType = 0x09
_shortenedLocalNameDataType = 0x08
_appearanceDataType = 0x19
_manufacturer_specific_data = 0xFF


async def do_scan(uuid, active=True, scan_duration_ms=5000, connection_timeout_ms=3000, filter_rssi=-90) -> list:
    log("BLE-Scanner: Starting Scan...")
    # Scan for devices and analyze adv data
    scan_results: list[ScanResult] = await scan_and_collect_scan_results(active, scan_duration_ms, filter_rssi)
    log("BLE-Scanner: Found {} devices.".format(len(scan_results)))
    utils.free()
    device_infos: list[DeviceInfo] = []
    for scan_result in scan_results:
        device: Device = scan_result.device
        (descriptor, manufacturerCode) = analyze_adv_data(scan_result.adv_data, device.addr_hex())
        device_infos.append(DeviceInfo(device.addr_hex(), scan_result.rssi, scan_result.connectable, descriptor, manufacturerCode))
    if (len(device_infos) > 0):
        log("Got following device info from adv data:")
        _print_devices(device_infos, True)
    else:
        log("No device info found in adv data.", log_type=0)
    # Filter out devices that are not connectable and not in the device_infos list (they have a descriptor already)
    scan_results = [scan_result for scan_result in scan_results if scan_result.connectable
                    and any(scan_result.device.addr_hex() == device.addr for device in device_infos)]
    # Connect to devices and get more info
    for i in range(len(scan_results)):
        scanResult: ScanResult = scan_results[i]
        log("BLE-Scanner: Connecting to {} ({}/{})".format(
            scanResult.device.addr_hex(), i + 1, len(scan_results)), log_type=0)
        newDeviceInfo: DeviceInfo = await connect_and_analyze(scanResult, connection_timeout_ms)
        device_infos.append(newDeviceInfo)
        # TODO: Check if this is necessary, seems more stable with it
        utils.free()
        asyncio.sleep_ms(100)
    _print_devices(device_infos)
    scan_results.clear()
    utils.free()
    if (device_infos == None or len(device_infos) == 0):
        return None
    scan_result = {
        "timestamp": utils.get_timestamp(),
        "scanresult": ujson.dumps([ob.__dict__ for ob in device_infos]),
        "uuid": ujson.dumps(str(uuid) + "-" + str(utils.get_room())),
        "room": utils.get_room()
    }
    device_infos.clear()
    utils.free()
    log("BLE-Scanner: Scan finished.")
    return scan_result


async def scan_and_collect_scan_results(active=True, scan_duration_ms=5000, filter_rssi=-90, interval_us=30000, window_us=30000) -> list[ScanResult]:
    # TODO: Check memory after each result and stop if free mem < 80% or so
    scan_results: list[ScanResult] = []
    scan_results_lock = Lock()
    async with aioble.scan(duration_ms=scan_duration_ms, interval_us=interval_us, window_us=window_us, active=active) as scanner:
        async for result in scanner:
            if (_filter_by_rssi(result.rssi, filter_rssi)):
                log("BLE-Scanner: Ignored device with RSSI >" +
                    str(filter_rssi).strip())
                continue
            await _update_scan_results(scan_results_lock, scan_results, result)
    return scan_results


async def _update_scan_results(lock: Lock, scan_results: list[ScanResult], new_scan_result: ScanResult):
    await lock.acquire()
    for old_scan_result in scan_results:
        # Device eqs if old.addr_type == new.addr_type and old.addr == new.addr
        if (old_scan_result.device == new_scan_result.device):
            scan_results.remove(old_scan_result)
            break
    scan_results.append(new_scan_result)
    lock.release()


def analyze_adv_data(adv_data, addr_hex=None) -> tuple[str, int]:
    complete_local_name = None
    shortened_local_name = None
    isPhone = False

    descriptor: str = None
    manufacturerCode: int = None
    i = 0
    log("Adv data of: " + str(addr_hex), log_type=0)
    while i < len(adv_data):
        length = adv_data[i]
        if length == 0:
            break
        i += 1
        data_type = adv_data[i]
        i += 1
        log("Type: " + str(data_type), newLine=False, log_type=0)
        log(" Payload: " + str(hexlify(adv_data[i:i+length-1])), log_type=0)
        if data_type == _completeLocalNameDataType:
            complete_local_name = adv_data[i:i+length-1].decode('utf-8')
        elif data_type == _shortenedLocalNameDataType:
            shortened_local_name = adv_data[i:i+length-1].decode('utf-8')
        elif data_type == _appearanceDataType:
            value = int.from_bytes(adv_data[i:i+length-1], "little")
            if value >= 0x0040 and value <= 0x004F:
                log("Found appearance data: " + str(value), log_type=0)
                isPhone = True
        elif data_type == _manufacturer_specific_data:
            # TODO: kinda unsafe adv_data[i:i+2]
            manufacturerCode = int.from_bytes(adv_data[i:i+2], "little")
        i += length - 1
    log("\n", log_type=0)
    # Set descriptor using hirarchy
    if isPhone:
        descriptor = "Phone"
    elif complete_local_name != None:
        descriptor = complete_local_name
    elif shortened_local_name != None:
        descriptor = shortened_local_name
    return descriptor, manufacturerCode


async def connect_and_analyze(scanResult: ScanResult, connection_timeout_ms=5000) -> DeviceInfo:
    # TODO: maybe change to global timeout, would also make sense to test the timeout more
    device: Device = scanResult.device
    deviceInfo: DeviceInfo = DeviceInfo(
        device.addr_hex(), scanResult.rssi, scanResult.connectable, connectionAttempts=1)
    manufacturer = None
    modelNumber = None
    connection = None
    try:
        connection: DeviceConnection = await device.connect(timeout_ms=connection_timeout_ms)
        deviceInfo.connSuccessful = True
        log("BLE-Scanner: Connected to " + device.addr_hex(), log_type=0)
        async with connection:
            deviceInfoService = await connection.service(_deviceInfoServiceUUID, timeout_ms=connection_timeout_ms)
            if deviceInfoService is None:
                await connection.disconnect()
            else:
                log("BLE-Scanner: Analyzing services", log_type=0)
                # Read the model number string characteristic
                modelChar = await deviceInfoService.characteristic(_modelNumberStringCharUUID)
                modelNumber = await _read_characteristic_as_utf8(modelChar, connection_timeout_ms)
                # Read the manufacturer string characteristic
                manufacturerChar = await deviceInfoService.characteristic(_manufacturerStringCharUUID)
                manufacturer = await _read_characteristic_as_utf8(manufacturerChar, connection_timeout_ms)
                # Disconnect from the device
                await connection.disconnect()
    except (OSError) as e:
        log("BLE-Scanner: Exception while getting info for device: " +
            str(device.addr_hex()) + "\nError: " + str(e), log_type=2)
        if (connection is not None):
            await connection.disconnect()  # does not seem to disconnect properly
    except asyncio.TimeoutError:
        # TODO: Retry after timeout?
        log("BLE-Scanner: Timeout while getting info for device: " +
            str(device.addr_hex()), log_type=2)
    if (manufacturer != None or modelNumber != None):
        deviceInfo.descriptor = manufacturer + " " + modelNumber
    return deviceInfo


async def _read_characteristic_as_utf8(characteristic: ClientCharacteristic, timeout_ms=2000) -> str:
    """Reads a characteristic and returns the data as string"""
    if (characteristic is None):
        log("BLE-Scanner: Characteristic {} not found".format(
            str(characteristic)), log_type=0)
        return None
    try:
        data = await characteristic.read(timeout_ms)
        return data.decode('utf-8')
    except GattError as e:
        log("BLE-Scanner: GattError during read: " + str(e))
        return None


def _print_devices(device_infos: list[DeviceInfo], only_with_descriptor=False):
    """Prints a list of devices"""
    if (device_infos == None or len(device_infos) == 0):
        return
    log("---------------Device List---------------")
    log("{:<17} {:<5} {:<26} {:<5} {:<5} {:<5}".format(
        "ADDR", "RSSI", "Descriptor", "Cntbl", "Succ", "Manufacturer Code"))
    for device_info in device_infos:
        if (only_with_descriptor and device_info.descriptor == None):
            continue
        log(device_info.__str__())
    log("\n")


def _filter_by_rssi(rssi, max_rssi):
    """Filter devices with RSSI > max_rssi"""
    if (max_rssi == 0):
        return False
    else:
        return max_rssi > rssi
