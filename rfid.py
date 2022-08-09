import serial

DEBUG = False

class Serial:
    def __init__(self):
        self.port_USB = "/dev/ttyUSB"
        self.ser = None
        self.baudrate = 9600

    def initialize(self):
        global DEBUG
        if DEBUG:
            return True
        for i in range(0, 10):
            try:
                self.ser = serial.Serial(self.port_USB + str(i), self.baudrate)
                return True
            except serial.serialutil.SerialException:
                pass
        if self.ser is None:
            return False

    def read_serie(self):
        global DEBUG
        if DEBUG:
            return "4:28:28:AA:7A:57:80"
        try:
            line = self.ser.readline().strip().decode('utf-8')
            self.ser.close()
        except serial.serialutil.SerialException:
            self.ser.close()
            self.initialize()
            line = self.ser.readline().strip().decode('utf-8')
            self.ser.close()
        return line
