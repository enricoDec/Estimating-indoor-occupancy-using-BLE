# ----APPLICATION FLAGS----#
# True = Connect to WiFi on Startup
NET = True
# True = Connect to MQTT Broker on Startup
MQTT_START = True
# True = Transfers Scands Data via MQTT after Scan
SEND_MQTT = True
# Allow to update the configuration via MQTT
ALLOW_CONFIG_UPDATE = True
# True = Prints Scanning Process, Results and other events
LOGGING = True
# Log Level (0 = Debug (Includes info and more), 1 = Info, 2 = Warning, 3 = Error)
LOG_LEVEL = 0

# ----WIFI CONNECTION CONFIG----#
# TODO: Change to your WiFi SSID
SSID = "MY_SSID"
# TODO: Change to your WiFi Key
NETWORK_KEY = "MY_KEY"

# ----MQTT CLIENT CONFIG----#
# TODO: Change to your MQTT Broker IP
MQTT_BROKER_ADDRESS = "localhost"
# TODO: Change to your MQTT User set to None if no user is needed
MQTT_USER = "mqtt"
# TODO: Change to your MQTT Password set to None if no password is needed
MQTT_PASSWORD = "password"
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
