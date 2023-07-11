# NodeRed Deployment

## 1. Install NodeRed

```bash
sudo apt-get install nodered
```

## 2. Install required Modules
- node-red-contrib-data-table-viewer
- node-red-contrib-influxdb

Can be installed from `Manage Palette` -> `Install`

## 3. Import the Flow
- Import the `nodeRed.json` file

## 4. Configure

1. Run the Init Node to create the required files (it creates some required files, check Smartphone Counter directory).
2. Configure the `Trigger Scan` Node MQTT Server.
3. Configure the `roomUtilization/scans/+` Node MQTT Server.
4. Configure the `Send to DB` Node.