import json
import sys


def rule_based_classification(descriptor, knownSmartphones):
    for knownSmartphone in knownSmartphones:
        if (knownSmartphone.lower().replace(" ", "") in descriptor.lower().replace(" ", "")):
            return True

def appendUnknownDeviceIfNotAlreadyIn(unknownDevices, descriptor):
    alreadyIn = False
    for unknownDevice in unknownDevices:
        if (unknownDevice == descriptor):
            alreadyIn = True
            break
    if (alreadyIn == False):
        unknownDevices.append(descriptor)


inputFile = sys.argv[1]
if (inputFile == None):
    print("No input file specified")
    exit(1)

with open(inputFile, "r") as file:
    json_data = json.load(file)

with open("smartphones.json", "r") as file:
    knownSmartphones = json.load(file)

with open("unknownDevices.json", "r") as file:
    unknownDevices = json.load(file)

counter = 0
for result in json_data["scanresult"]:
    descriptor = result["descriptor"]
    if (descriptor is not None and rule_based_classification(descriptor, knownSmartphones)):
        counter += 1
    else :
        appendUnknownDeviceIfNotAlreadyIn(unknownDevices, descriptor)

with open("unknownDevices.json", "w") as file:
    json.dump(unknownDevices, file)

# append smartphones to the json_data
json_data["smartphones"] = counter


print(json.dumps(json_data))
