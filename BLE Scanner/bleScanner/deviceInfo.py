class DeviceInfo:
    def __init__(self, addr, descriptor):
        self.addr = addr
        self.descriptor = descriptor

    def __str__(self):
        result = \
            "ADDR: " + self.addr + "\n" + \
            "Descriptor: " + self.descriptor + "\n"
        return result
