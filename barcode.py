import time

import serial
import logging

class BarcodeReader:
    """Bluetooth barcode reader"""

    def __init__(self, port="/dev/rfcomm0"):
        self.ser = serial.Serial()
        self.ser.port = port
        self.ser.baudrate = 115200
        self.ser.bytesize = serial.EIGHTBITS
        self.ser.parity = serial.PARITY_NONE
        self.ser.stopbits = serial.STOPBITS_ONE
        self.ser.timeout = 0
        self.ser.xonxoff = False
        self.ser.rtscts = False
        self.ser.dsrdtr = False
        self.ser.writeTimeout = 3

    def open(self):
        try:
            if not self.ser.is_open:
                self.ser.open()
        except serial.SerialException as error:
            logging.error("Error opening serial port: {}".format(error))
            return False
        return self.ser.is_open

    def close(self):
        if self.ser.is_open:
            self.ser.close()

    def read(self):
        try:
            barcode = self.ser.readline().decode("utf-8").strip("\r\n")
            barcode_len = len(barcode)
            if barcode_len > 0:
                return barcode
        except serial.SerialException as error:
            logging.error("Barcode reader error: {}".format(error))
            self.close()
            self.open()

    def read_multiple(self):
        try:
            barcode = self.ser.read(self.ser.inWaiting())
            barcode_len = len(barcode)
            if barcode_len > 0:
                barcode = barcode.decode("utf-8")
                return barcode
        except serial.SerialException as error:
            logging.error("Barcode reader error: {}".format(error))
            self.close()
            self.open()

    def read_barcode(self):
        time.sleep(0.2)
        barcode = None
        while barcode is None:
            barcode = self.read()
        return barcode


if __name__ == "__main__":
    br = BarcodeReader()
    br.open()
    time.sleep(10)
    barcode = br.read()
    print(barcode)
    br.close()
    del br
    print("Done")
    exit(0)