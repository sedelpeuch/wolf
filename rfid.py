import time

import serial


class Serial:
    def __init__(self):
        self.port_USB = "/dev/ttyUSB"
        self.ser = None
        self.baudrate = 9600

    def initialize(self):
        for i in range(0, 10):
            try:
                self.ser = serial.Serial(self.port_USB + str(i), self.baudrate)
                return True
            except serial.serialutil.SerialException:
                pass
        if self.ser is None:
            return False

    def read_serie(self):
        try:
            line = self.ser.readline().strip().decode('utf-8')
            self.ser.close()
        except serial.serialutil.SerialException:
            self.ser.close()
            self.initialize()
            line = self.ser.readline().strip().decode('utf-8')
            self.ser.close()
        return line

    def activation(self):
        try:
            self.ser.write(b'1')
            time.sleep(0.5)
        except serial.serialutil.SerialException:
            self.ser.close()
            self.initialize()
            self.ser.write(b'1')
            time.sleep(0.5)


    def desactivation(self):
        try:
            self.ser.write(b'0')
        except serial.serialutil.SerialException:
            self.ser.close()
            self.initialize()
            self.ser.write(b'0')
            time.sleep(0.5)

