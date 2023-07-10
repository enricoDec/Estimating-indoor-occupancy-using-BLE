# NodeRed Deployment

## 1. Install NodeRed

```bash
sudo apt-get install nodered
```

### Required Modules
- node-red-contrib-data-table-viewer
- node-red-contrib-influxdb

Can be installed from `Manage Palette` -> `Install`

## 2. Import the Flow
- Import the `nodeRed.json` file

## 3. Configure

1. Run the Init Node to create the required files.
2. Configure the `Trigger Scan` Node MQTT Server.
3. Configure the `roomUtilization/scans/+` Node MQTT Server.
4. Configure the `Send to DB` Node.