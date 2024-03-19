import json
import sys

def rule_based_classification(descriptor, knownSmartphones):
    for knownSmartphone in knownSmartphones:
        if knownSmartphone.lower().replace(" ", "") in descriptor.lower().replace(" ", ""):
            return True
    return False

def appendUnknownDeviceIfNotAlreadyIn(unknownDevices, descriptor):
    if descriptor not in unknownDevices:
        unknownDevices.append(descriptor)

inputFile = sys.argv[1]
if not inputFile:
    print("No input file specified")
    exit(1)

with open(inputFile, "r") as file:
    json_data = json.load(file)

with open("smartphones.json", "r") as file:
    knownSmartphones = json.load(file)

with open("unknownDevices.json", "r") as file:
    unknownDevices = json.load(file)

time_counts = []

for result in json_data["descriptors"]:
    descriptor = result["descriptor"]
    time = result["time"]
    if descriptor and rule_based_classification(descriptor, knownSmartphones):
        time_counts.append({"time": time, "count": 1})
    else:
        appendUnknownDeviceIfNotAlreadyIn(unknownDevices, descriptor)

with open("unknownDevices.json", "w") as file:
    json.dump(unknownDevices, file)

# Append smartphones to the json_data
json_data["smartphones"] = time_counts

print(json.dumps(json_data))
