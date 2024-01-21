# ----APPLICATION FLAGS----#
# True = Connect to WiFi on Startup
NET = True
# True = Connect to MQTT Broker on Startup
MQTT_START = True

# ----WIFI CONNECTION CONFIG----#
SSID = "MY_WIFI_SSID"
NETWORK_KEY = "MY_WIFI_PASSWORD"

# ----MQTT CLIENT CONFIG----#
MQTT = True # True = Transfers Data via MQTT after Scan
MQTT_BROKER_ADDRESS = "MY_MQTT_BROKER_ADDRESS"
# This topic pattern is suggested, like this you can subscribe to all rooms with "roomUtilization/scans/#"
# or to a specific room with "roomUtilization/scans/myRoom". The topic for triggering a scan is "roomUtilization/doScan"
MQTT_ROOM_NAME = "myRoom" #doScan not allowed as room name (reserved for scan trigger)
MQTT_BASE_TOPIC = "roomUtilization/"

# ----SCANNER CONFIG----#

# Time in sec between each scan (Default 300s = 5min) or -1 if scan should be triggered via MQTT
TIME_BETWEEN_SCANS_S = 20

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
