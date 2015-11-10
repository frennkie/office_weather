# -*- coding: utf-8 -*-

import fcntl
import time
import random
import os


class AirControlMini(object):
    """AirControlMini (acm) class"""

    def __init__(self, device=None):
        """

        Args:
            device (str): device path, defaults to "/dev/co2mini0"

        """

        if device:
            self.device = device
        else:
            self.device = "/dev/co2mini0"

        if not os.path.exists(self.device):
            raise("Could not find device: " + str(self.device) +
                  "\nMake sure it is connected (and check udev rules).")

        self.key = [0xc4, 0xc6, 0xc0, 0x92, 0x40, 0x23, 0xdc, 0x96]
        self.set_report = "\x00" + "".join(chr(e) for e in self.key)

    def connect(self):
        """actually open connection to the sensor"""

        try:
            self.fp = open(self.device, "a+b",  0)
            HIDIOCSFEATURE_9 = 0xC0094806
            fcntl.ioctl(self.fp, HIDIOCSFEATURE_9, self.set_report)
            return True
        except Exception as err:
            raise(err)

    @classmethod
    def auto_detect_sensor(cls):
        """automatically detect the device path of the sensor"""
        """possibly raises an exception if unable to detect a sensor"""
        # TODO (frennkie): implement this
        return "/dev/hidraw0"

    @staticmethod
    def get_fake_values():
        """generator that fakes values to simulate the real get_values method"""
        while True:
            co2 = int(random.randint(300, 2000))
            tmp = float(random.randint(1000, 3000))/100
            time.sleep(0.5)
            yield co2, tmp

    def get_values(self):
        """generator

        Yields:
            tuple (co2, tmp): The next tuple of valid sensor values

        """

        values = {}

        while True:
            lst = list()

            data = list(ord(e) for e in self.fp.read(8))
            print("DEBUG: " + str(data))

            decrypted = self._decrypt(self.key, data)
            if decrypted[4] != 0x0d or (sum(decrypted[:3]) & 0xff) != decrypted[3]:
                print(self._hd(data), " => ", self._hd(decrypted), "Checksum error")
            else:
                op = decrypted[0]
                val = decrypted[1] << 8 | decrypted[2]
                values[op] = val

                if (0x50 in values) and (0x42 in values):
                    co2 = values[0x50]
                    tmp = (values[0x42]/16.0-273.15)

                    print("CO2: %4i TMP: %3.1f" % (co2, tmp))

                    yield co2, tmp

    @staticmethod
    def _decrypt(key, data):
        cstate = [0x48,  0x74,  0x65,  0x6D,  0x70,  0x39,  0x39,  0x65]
        shuffle = [2, 4, 0, 7, 1, 6, 5, 3]

        phase1 = [0] * 8
        for i, o in enumerate(shuffle):
            phase1[o] = data[i]

        phase2 = [0] * 8
        for i in range(8):
            phase2[i] = phase1[i] ^ key[i]

        phase3 = [0] * 8
        for i in range(8):
            phase3[i] = ( (phase2[i] >> 3) | (phase2[ (i-1+8)%8 ] << 5) ) & 0xff

        ctmp = [0] * 8
        for i in range(8):
            ctmp[i] = ( (cstate[i] >> 4) | (cstate[i]<<4) ) & 0xff

        out = [0] * 8
        for i in range(8):
            out[i] = (0x100 + phase3[i] - ctmp[i]) & 0xff

        return out

    @staticmethod
    def _hd(d):
        return " ".join("%02X" % e for e in d)

