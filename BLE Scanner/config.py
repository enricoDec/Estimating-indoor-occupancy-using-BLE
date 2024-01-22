# ----APPLICATION FLAGS----#
# True = Connect to WiFi on Startup
NET = True
# True = Connect to MQTT Broker on Startup
MQTT_START = True
# True = Transfers Data via MQTT after Scan
SEND_MQTT = True

# ----WIFI CONNECTION CONFIG----#
SSID = "MY_SSID" # TODO: Change to your WiFi SSID
NETWORK_KEY = "MY_KEY" # TODO: Change to your WiFi Key

# ----MQTT CLIENT CONFIG----#
MQTT_BROKER_ADDRESS = "BROKER_IP" ## TODO: Change to your MQTT Broker IP
# This topic pattern is suggested, like this you can subscribe to all rooms with "roomUtilization/scans/#"
# or to a specific room with "roomUtilization/scans/myRoom". The topic for triggering a scan is "roomUtilization/doScan"
# doScan not allowed as room name (reserved for scan trigger)
MQTT_ROOM_NAME = "myRoom"
MQTT_BASE_TOPIC = "roomUtilization/"

# ----SCANNER CONFIG----#

# Time in sec between each scan (Default 30000ms = 30s). Set TIME_BETWEEN_SCANS_MS to -1 if scan should be triggered via MQTT
TIME_BETWEEN_SCANS_MS = 30000

# The actual duration of the scan in ms (Default 8000ms).
SCAN_DURATION_MS = 8000

# Timeout in ms to connect to a device (for each connectable device)
SCAN_CONNECTION_TIMEOUT_MS = 5000

# True = Active Scan | False = Passive Scan (Only listens for advertising packets sent by BLE devices, uses less power)
ACTIVE_SCAN = True

# Only Include Devices with a higher RSSI (0 for no filter)
FILTER_RSSI = -100

# True = Prints Scanning Process, Results and other events
LOGGING = True
