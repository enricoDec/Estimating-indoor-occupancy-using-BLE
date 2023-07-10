# BLE Scanner Deployment

## 1. Install esptool (needed to flash the board with microPython)   
Run this command:
``` bash
pip install esptool
```
Refer to the [official documentation](https://docs.espressif.com/projects/esptool/en/latest/esp32/) for more information.

## 2. Flash the board with microPython
1. Find out the port of the board:  
Depending on the OS, the port can be different. For example, on Linux it can be ```/dev/ttyUSB0``` or ```/dev/ttyACM0```. On Mac it can be ```/dev/tty.SLAB_USBtoUART```. On Windows it can be ```COM1```. To find out the port, you can use the following command:

``` bash
ls /dev/tty* 
ls /dev/cu*
```  

2. Download the latest microPython firmware from [here](https://micropython.org/download/). If using the ESP32 [here](https://micropython.org/download/esp32/).

3. Flash the board with the following commands (replace the port with the one you found out in step 1 and the board):

``` bash
esptool.py --chip esp32 --port [PORT] erase_flash
esptool.py --chip esp32 --port [PORT] --baud 460800 write_flash -z 0x1000 [FIRMWARE.bin]
```

or try this if the above does not work:

``` bash
esptool.py --port /dev/tty.usbserial-0001 --baud 460800 write_flash --flash_size=detect 0 [FIRMWARE.bin]
```

Refer to the [official documentation](https://docs.micropython.org/en/latest/esp8266/tutorial/intro.html#deploying-the-firmware) for more information.

## 3. Configure the project
1. Make sure to change the WIFI and MQTT constants references. Either use your own data (SSID, WIFI Key, MQTT Broker Address) directly in the variables or enter the corresponding values in constants.py (recommended) and insert them into the `config.py`.
2. Check the `config.py` file and configure the scanner (Default Config works as well)
3. Restart or Soft-Reboot the ESP32 (Ctrl+D)

## 4. Upload the project to the board
### Setup the project using Visual Studio Code
1. Install the Pymakr extension for Visual Studio Code. [Link](https://marketplace.visualstudio.com/items?itemName=pycom.Pymakr)
2. Open the workspace in Visual Studio Code.
3. Setup your board as device in Pymakr (it might help to stop the script if you get the warning board is busy).
4. Upload the project to the board using the upload button in Pymakr.
5. Open the serial monitor in Pymakr to see the output of the board.
6. Done!
### Setup the project using Thonny
TODO: Add instructions

## 5. (Optional) Get code completion for the project  
The 'lib' folder is already added to the project. This folder contains the libraries needed for the project (the ones that are specific to the esp32). If you want to add more libraries, add them to the 'lib' folder. To do so, you can use the following command:   
(Note) for this to work, the board needs to be connected to the internet.
1. Connect to the board using the serial monitor in Pymakr.
```bash
import mip
mip.install("myLib", mpy=False)
```
1. Copy the sources from the esp to your local machine using PyMakr or another tool (for example esptool).

## 5. (Optional) Get code completion for the project by stubbing
1. run `import sys; print( "version:", sys.version, "port:", sys.platform)` to get the port and micropython version
2. `python3 -m venv .venv` `source .venv/bin/activate` 
3. Get the stub with the same version and port [here](https://github.com/Josverl/micropython-stubs/tree/main/stubs) or generate one [here](https://github.com/Josverl/micropython-stubber#readme) if it doesn't exist.
4. Now run `pip install -U  micropython-<port>-stubs` in the virtual environment. For example: `pip install -U micropython-esp32-stubs`

## 5. (Optional) Get code completion for the project by stubbing yourself (Good luck)
0. [Using](https://github.com/Josverl/micropython-stubber#readme) (the install guide on Github does not work)...
1. `python3 -m venv .venv` `source .venv/bin/activate` 
2. `pip install micropython-stubber`
3. `mkdir all-stubs && mkdir stubs`
4. `touch pyproject.toml (no clue why or what this does)`
5. `stubber clone`
6. `stubber switch v1.18`   
7. `stubber get-docstubs`
8. `stubber get-frozen`  
9. `stubber get-core`
10. `stubber update-fallback`
11. Include extraPaths in .vscode/settings.json for the stubs to be found by the IDE. For example: `"python.autoComplete.extraPaths": ["./stubs"]`