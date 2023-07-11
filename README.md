# BLE (Bluetooth Low Energy) Room occupancy detection
Here a general overview of the project is given. A deployment guide can be found [here](#deployment).

This project is based on the work of Justin Steven Herbrich, his project can be found [here](https://github.com/jutnhbr/dln-ble-scanner-for-room-utilization). Herbrich's developed an approach to take advange of the fact that most people carry at least one BLE capable device with them. The idea is to use BLE to detect nearby devices and try to determine how many people are found in a room. This project is an attempt to improve Herbrich's approach and make it more scalable and accurate. Herbrich's approach to determine the number of people in a room is based on the assumption, that a BLE Device that allows a connection and has a public address is a consumer device and as such counts as a person.
Altough his testing showed promising results, there are some flaws in his approach. Most devices nowdays use random MAC addresses to protect the privacy of the user, this includes most Apple devices (iPhones, MacBooks and iPads). All these devices offer a connection over BLE and could be related to a person in the room but they are not counted as a person, because they use a random MAC address. This project tries to solve this problem by using the device name instead of the MAC address to identify a person. The device name is not protected by privacy and can be used to identify a device. This project also tries to make the BLE Scanner more scalable by adding support for multiple BLE Scanners. The BLE Scanners can be distributed across multiple rooms and the data is then sent to a central database. This allows us to scale the system to multiple rooms and buildings.

## Takkling the problems of Herbrich's approach
### Assign a person to a BLE Device
Currently a person is identified as a BLE Device with the following conditions:
- The peripheral is in range of the scanner
- The peripheral allows a connection
- The RSSI is above the configured threshold (default: -100)
- The peripheral has a pubblic address (not random). A pubblic address is a MAC address that is unique and can be used to identify a device. Random addresses are used to protect the privacy of the user. The problem with random addresses is that they change every 15 minutes. This means that if a device is in range of the scanner for more than 15 minutes, it will be counted as a new device. To solve this, you can either increase the scan interval or use a different method to identify a device.
#### My approach
#### 1. Analyze the advertising data 
Analyze the advertising data of the peripheral to be able to classify the device. Following [Common Data Types](https://www.bluetooth.com/specifications/assigned-numbers/) specifyed by the Bluetooth SIG are analyzed:
   - Shortened Local Name (0x08)
   - Complete Local Name (0x09)
   - Appearance (0x19)

The advertised name of the peripheral is later on used to determine if the device is a smartphone, altough most smartphones based on my testing do not advertise their name in the advertising data, but rather as a characteristic of the GAP Service (under the device info service). The appearance type is used to determine if the device is a smartphone. The appearance type is a 2 byte value that specifies the category of the device. The Value 0x0040 to 0x007F specifies a Phone.

#### 2. Connect to the device and read the Device info service
If not valuable information could be obtained by analyzing the advertising data, my approach tries to connect to the device and read the Device info service of the GAP Service to obtain the device name and manufacturer. The Device info service (UUID 0x180A) contains the following relevant characteristics:
- Manufacturer Name String (UUID 0x2A29)
- Model Number String (UUID 0x2A24)

For example an iPhone 13 has the following values:
- Manufacturer Name String: Apple Inc.
- Model Number String: iPhone13,4

This data can later be used to identify a BLE Device as a smartphone. Different approaches can be used to achieve this comparing the string with a list of known smartphone names being the easiest one.

### Multiple BLE Scanners
With the current setup only one BLE Scanner per Room can be used at a time. Duplicates are only filtered on the Scanner and not on the database. This means that if you have multiple scanners running at the same time, you will get duplicates in the database. Moreover no information about room in which the device was found is stored. 

#### My approach
To solve this problem, I added support for multiple BLE Scanners. The Flow is as follows:
1. The BLE Scanner is triggered by a MQTT message which contains a payload with the scan id. The scan id is used to identify the scan and group the results and a room id. The room id is used to identify the room in which the scanner is located. 
```json
{'uuid': 'f56eb9f0-aaf9-436d-b0fb-df65ecb06c7e', 
'room': 'myRoom'}
```
Each scanner needs to have a unique room id and sends a result only if the room id matches the room id of the scan or the room id is `all`. The central pushlishes the trigger to the topic `roomUtilization/doScan` while the BLE Scanner subscribes to the topic `roomUtilization/doScan`.

2. The BLE Scanner published the scan results to the topic `roomUtilization/scans/myRoom` where myRoom is the room id of the scanner. The central subscribes to `roomUtilization/scans/+`.
```json
{
  'scanresult': 
  '[
    {"addr": "45:88:7b:10:68:b6", "descriptor": "Apple Inc. iPad13,4"},
    {"addr": "d7:9f:fb:78:8d:c3", "descriptor": "Philips 929002376101"},
    {"addr": "5e:cc:6c:70:b1:f4", "descriptor": "Apple Inc. MacBookAir8,2"},
    {"addr": "6f:11:b2:e8:46:58", "descriptor": "Apple Inc. MacBookPro16,3"},
    {"addr": "58:4d:66:56:32:a7", "descriptor": "Apple Inc. Mac14,9"},
    {"addr": "4a:27:71:c6:64:29", "descriptor": "Apple Inc. iPhone13,2"}
  ]', 
  'uuid': '"f56eb9f0-aaf9-436d-b0fb-df65ecb06c7e-myRoom"', 
  'room': 'myRoom', 
  'timestamp': '9/7/2023 16:04'
}
```
Potentially more scanners could send it's own results with other scanresults (which are leter filtered by addr and uuid) in order to distinguish between different rooms and scans.
3. The central waits for all result scans (with a fixed timeout) and merges the scans as mentioned before. For each uuid (room and scan trigger id) the central analyzed the scans and stores the results in an influxdb database. 

### Bug in the current implementation while collecting the scan results 
Currently the first result of the scan is stored, while all subsequent results are filtered. Aioble returns the same device multiple times, if new information is available (for example new rrsi or advData information). This means that we are not storing the most recent information. To solve this, we need to store all the results and then filter them. This is quite a flaw in the current implementation, as the device might be not connectable in the first scan, but connectable in the second scan and so it potentially does not count a connectable device as a person.

## Research and Ideas

### Advertising Data for Apple Devices
Extract from this Paper: [Handoff All Your Privacy – A Review of Apple’s
Bluetooth Low Energy Continuity Protocol](https://arxiv.org/pdf/1904.10600.pdf).


"Specifically, we investigate the following flags:
– Simultaneous LE and BR/EDR to Same Device Ca-
pable Host (H)
– Simultaneous LE and BR/EDR to Same Device Ca-
pable Controller (C)
– Peripheral device is LE only (LE)
Mobile devices were observed with flags H, C, and LE
set to 1,1,0, whereas MacBooks were set to 0,0,1. Air-
Pods lacked any flags and were thereby easily identifi-
able as the only device type with no flag attributes." 
[[article](https://arxiv.org/pdf/1904.10600.pdf), P.7].


Disproved this seems to not be the case anymore, as all Apple devices seem to the the same flag `11010` (0x1A) set. Further testing should be done to confirm this.

Another really interesting [article](https://hexway.io/wp-content/uploads/2020/01/apple_bleee.pdf) about the BLE Advertising Data of Apple Devices (manufacturer specific data). 

### Ideas/Imporvements

- Analyze more services and characteristics that can relate with smartphones: 
  - Phone Alert Status 
- Analyze advertising data more in depth 
  - Class of Device (0x0D) with the Minor Device Class with bits 2-3 set to 1 (Smartphone) and bits 4-7 set to 0 (Uncategorized).
- Make assumption about moving or standing devices based on the RSSI. For example, if the RSSI is constantly changing, the device is moving. If the RSSI is constant, the device is standing still. This could be used to filter out devices that are standing still for a long time (e.g. a printer or a TV)
- Hash the address of the peripherals (more privacy? (not persisted anyway at the moment))
- Automate the deployment process (Docker?)

# Deployment
The deployment is rather time consuming and requires a lot of manual steps. I will try to describe the steps as good as possible.

## Prerequisites
- Host computer that will run: `node-red`, `influxdb` and `MQTT Broker`.
- One or more ESP32 (any microcontroller with BLE support should work, but may require to reinstall aioble).

## Setup the Host Computer
1. Install MQTT Broker (e.g. [Mosquitto](https://mosquitto.org/)).
   1. Be sure to remeber the IP address of the MQTT Broker, User and password.
   2. The mosquitto.conf file could look like this:
   ``` bash
   # listen tcp
   listener 1883
   # listen websockets
   listener 9001
   listener 8001
   protocol websockets
   socket_domain ipv4
   # allow no auth
   allow_anonymous true
   ```
2. Install [InfluxDB](https://docs.influxdata.com/influxdb/v2.7/get-started/).
  - Make a bucket named `PEOPLE_COUNTER`
3. Setup NodeRed [guide](./Interface/README.md).
## Setup ESP32
1. Setup the BLE Scanner [guide](./BLE%20Scanner/README.md).