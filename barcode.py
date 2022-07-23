import logging
import time

import pyautogui
import serial

running_virtual_keyboard = True

def read_virtual_barcode():
    barcode_reader = BarcodeReader()
    print("Barcode reader started", running_virtual_keyboard)
    while running_virtual_keyboard:
        try:
            barcode = barcode_reader.ser.readline().decode("utf-8").strip("\r\n")
            barcode_len = len(barcode)
            if barcode_len > 0:
                for char in barcode:
                    pyautogui.press(char)
                pyautogui.press("enter")
        except serial.SerialException as error:
            logging.error("Barcode reader error: {}".format(error))
            barcode_reader.close()
            barcode_reader.open()
    barcode_reader.close()


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

    def read_barcode(self):
        time.sleep(0.2)
        barcode = None
        while barcode is None:
            barcode = self.read()
        return barcode


if __name__ == "__main__":
    br = BarcodeReader()
    br.open()
    while True:
        barcode = br.read_virtual_barcode()
    br.close()
    del br
    print("Done")
    exit(0)
