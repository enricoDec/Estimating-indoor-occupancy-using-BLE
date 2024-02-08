class DeviceInfo:
    def __init__(self, addr: str, rssi, connectable=False, descriptor=None, manufacturerCode: int = None, connectionAttempts: int = 0, connectionSuccessful=False):
        self.addr = addr
        self.rssi = rssi
        self.connectable = connectable
        self.descriptor = descriptor
        self.manufacturerCode = manufacturerCode
        self.connAttempts = connectionAttempts
        self.connSuccessful = connectionSuccessful

    def __str__(self):
        isConnectable = "Y" if self.connectable else "N"
        descr = "N/A" if self.descriptor is None else self.descriptor
        isSuccessful = "Y" if self.connSuccessful else "N"
        manuCode = "N/A" if self.manufacturerCode is None else str(self.manufacturerCode)
        return "{:<17} {:<5} {:<26} {:<5} {:<5} {:<5} {:<5}".format(self.addr, str(self.rssi), descr, isConnectable, isSuccessful, manuCode, self.connAttempts)

    def __eq__(self, other):
        return self.addr == other.addr
