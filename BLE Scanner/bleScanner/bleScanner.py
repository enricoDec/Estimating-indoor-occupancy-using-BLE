from util import utils
from util.utils import log
from binascii import hexlify
from bleScanner.deviceInfo import DeviceInfo
from aioble import GattError
from aioble.device import Device
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


async def do_scan_and_connect(uuid, active=True, duration=5000, connection_timeout=3000, filter_rssi=-90) -> list:
    log("BLE-Scanner: Starting Scan...")
    (device_infos, connectable_devices) = await collect_device_info(active, duration, filter_rssi)
    utils.free()
    log("BLE-Scanner: Scan done, found " + str(len(connectable_devices)) +
        " connectable devices. Got info from adv data from: " + str(len(device_infos)) + " devices.")
    utils.free()
    if len(device_infos) > 0:
        log("Got following device info from adv data:")
        _print_devices(device_infos)
    for connectable_device in connectable_devices:
        newDeviceInfo = await connect_and_get_info(connectable_device, connection_timeout)
        if newDeviceInfo != None:
            log("BLE-Scanner: Got info from device: \n" + str(newDeviceInfo))
        if (newDeviceInfo != None):
            device_infos.append(newDeviceInfo)
        # TODO: Check if this is necessary, seems more stable with it
        asyncio.sleep_ms(100)
        utils.free()
    if device_infos is None:
        return None
    scan_result = {
        "timestamp": utils.getTimestamp(),
        "scanresult": ujson.dumps([ob.__dict__ for ob in device_infos]),
        "uuid": ujson.dumps(str(uuid) + "-" + str(utils.get_room())),
        "room": utils.get_room()
    }
    _print_devices(device_infos)
    utils.free()
    log("BLE-Scanner: Scan finished.")
    return scan_result


async def collect_device_info(active=True, duration=5000, filter_rssi=-90, interval_us=30000, window_us=30000) -> tuple[list, list]:
    # TODO: Check memory after each result and stop if free mem < 80% or so
    connectable_devices = []
    device_infos: DeviceInfo = []
    async with aioble.scan(duration, interval_us=interval_us, window_us=window_us, active=active) as scanner:
        async for result in scanner:
            deviceName = None
            if _filter_by_rssi(result, filter_rssi):
                log("BLE-Scanner: Ignored device with RSSI >" +
                    str(filter_rssi).strip())
                continue
            # Get info from adv data
            if (result.adv_data != None and _already_scanned(device_infos, result.device) == False):
                deviceName = _get_descriptor_from_advData(
                    result.adv_data, False, result.device.addr_hex())
            if (deviceName != None):
                device_infos.append(DeviceInfo(
                    addr=result.device.addr_hex(), descriptor=deviceName))
                continue
            # If no info was extracted from the adv data keep the device if connectable
            if result.connectable == False:
                continue
            _update_result(connectable_devices, result.device)
            utils.free()
    return device_infos, connectable_devices


def _already_scanned(device_infos: DeviceInfo, device: Device):
    for device_info in device_infos:
        if device_info.addr == device.addr_hex():
            return True
    return False


def _update_result(connectable_devices, newDevice):
    for device in connectable_devices:
        if device == newDevice:
            connectable_devices.remove(newDevice)
            connectable_devices.append(newDevice)
            return
    connectable_devices.append(newDevice)


def _get_descriptor_from_advData(adv_data, logging=False, addr_hex=None):
    complete_local_name = None
    shortened_local_name = None
    isPhone = False
    i = 0
    if logging:
        log("Adv data of: " + str(addr_hex))
    while i < len(adv_data):
        length = adv_data[i]
        if length == 0:
            break
        i += 1
        data_type = adv_data[i]
        i += 1
        if logging:
            log("Type: " + str(data_type), newLine=False)
            log(" Payload: " + str(hexlify(
                adv_data[i:i+length-1])))
        if data_type == _completeLocalNameDataType:
            complete_local_name = adv_data[i:i+length-1].decode('utf-8')
        elif data_type == _shortenedLocalNameDataType:
            shortened_local_name = adv_data[i:i+length-1].decode('utf-8')
        elif data_type == _appearanceDataType:
            value = int.from_bytes(adv_data[i:i+length-1], "little")
            if value >= 0x0040 and value <= 0x004F:
                log("Found appearance data: " + str(value))
                isPhone = True
        elif data_type == _manufacturer_specific_data:
            # TODO: parse and identify manufacturer specific data
            isPhone = False
        i += length - 1
    if isPhone:
        return "Phone"
    elif complete_local_name != None:
        return complete_local_name
    elif shortened_local_name != None:
        return shortened_local_name
    return None


async def connect_and_get_info(device, connection_timeout=3000) -> DeviceInfo:
    deviceInfo = None
    manufacturer = None
    modelNumber = None
    connection = None
    try:
        log("BLE-Scanner: Connecting to device: " + str(device.addr_hex()))
        connection = await device.connect()
        async with connection:
            deviceInfoService = await connection.service(_deviceInfoServiceUUID)
            if deviceInfoService is None:
                await connection.disconnect()
            else:
                # Read the model number string characteristic
                modelChar = await deviceInfoService.characteristic(_modelNumberStringCharUUID)
                modelNumber = await _read_characteristic_as_utf8(modelChar)
                # Read the manufacturer string characteristic
                manufacturerChar = await deviceInfoService.characteristic(_manufacturerStringCharUUID)
                manufacturer = await _read_characteristic_as_utf8(manufacturerChar)
                # Disconnect from the device
                await connection.disconnect()
    except (OSError) as e:
        log("BLE-Scanner: Exception while getting info for device: " +
            str(device.addr_hex()) + "\nError: " + str(e))
        if connection is not None:
            await connection.disconnect()
    except asyncio.TimeoutError as e:
        log("BLE-Scanner: Timeout while getting info for device: " +
            str(device.addr_hex()))
    if manufacturer != None or modelNumber != None:
        deviceInfo = DeviceInfo(
            addr=device.addr_hex(), descriptor=str(manufacturer) + " " + str(modelNumber))
    return deviceInfo


async def _read_characteristic_as_utf8(characteristic):
    """Reads a characteristic and returns the data as string"""
    if characteristic is None:
        log("BLE-Scanner: Characteristic not found")
        return None

    try:
        data = await characteristic.read(timeout_ms=2000)
        return data.decode('utf-8')
    except GattError as e:
        log("BLE-Scanner: GattError during read: " + str(e))
        return None


def _print_devices(device_infos):
    """Prints a list of devices"""
    if (device_infos == None or len(device_infos) == 0):
        return
    log("---------------Device List---------------")
    for device_info in device_infos:
        log(device_info.__str__())


def _filter_by_rssi(result: int, max_rssi: int):
    """Filter devices with RSSI > max_rssi"""
    if (max_rssi == 0):
        return False
    else:
        return max_rssi > result.rssi
