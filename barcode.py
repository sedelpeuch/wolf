import logging
import time

import pyautogui
import serial

running_virtual_keyboard = True


def read_virtual_barcode():
    """
    Initialise le lecteur de code barre et un clavier virtuel pour écrire à chaque lecteur de code barre et appuyer
    sur la touche entrée tant que le flag running_virtual_keyboard est à True. Désactive le lecteur de code barre une
    fois le flag running_virtual_keyboard à False.

    :return: None
    """
    barcode_reader = BarcodeReader()
    while running_virtual_keyboard:
        try:
            barcode = barcode_reader.ser.readline().decode("utf-8").strip("\r\n")
            barcode_len = len(barcode)
            if barcode_len > 0:
                for char in barcode:
                    with pyautogui.hold('shift'):
                        pyautogui.press(char, interval=0.01)
                pyautogui.press("enter")
        except serial.SerialException as error:
            barcode_reader.close()
            barcode_reader.open()
    barcode_reader.close()


class BarcodeReader:
    """
    Classe permettant d'initialiser le lecteur de code barre et de le fermer. Cette classe permet aussi de renvoyer
    en uart (sur le port /dev/rfcomm0, voir tutoriel d'installation) le code barre lu.
    """

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
        """
        Initialise le port série du lecteur de code barre.

        :return: True si le port série a été ouvert, False sinon.
        """
        try:
            if not self.ser.is_open:
                self.ser.open()
        except serial.SerialException as error:
            return False
        return self.ser.is_open

    def close(self):
        """
        Ferme le port série du lecteur de code barre si celui-ci est ouvert.

        :return: None
        """
        if self.ser.is_open:
            self.ser.close()

    def read(self):
        """
        Lit la dernière ligne du port série du lecteur de code barre, ouvre le port série si celui-ci n'est pas ouvert

        :return: La dernière ligne lue du port série du lecteur de code barre si celui-ci est ouvert, None sinon.
        """
        try:
            barcode = self.ser.readline().decode("utf-8").strip("\r\n")
            barcode_len = len(barcode)
            if barcode_len > 0:
                return barcode
        except serial.SerialException as error:
            self.close()
            self.open()

    def read_barcode(self):
        """
        Lit le prochain code barre lu sur le port série du lecteur de code barre, ouvre le port série si celui-ci
        n'est pas ouvert (appel blocquant). Dépend de read().

        :return: Le prochain code barre lu sur le port série du lecteur de code barre
        """
        time.sleep(0.2)
        barcode = None
        while barcode is None:
            barcode = self.read()
        return barcode


if __name__ == "__main__":
    br = BarcodeReader()
    br.open()
    running_virtual_keyboard = True
    read_virtual_barcode()
    br.close()
    del br
    exit(0)
