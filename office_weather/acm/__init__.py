# -*- coding: utf-8 -*-


class AirControlMini(object):
    """AirControlMini (acm) class

    Args:

    """

    def __init__(self, device="/dev/hidraw0"):

        self.device = device

        self.key = [0xc4, 0xc6, 0xc0, 0x92, 0x40, 0x23, 0xdc, 0x96]
        self.fp = open(self.device, "a+b",  0)
        HIDIOCSFEATURE_9 = 0xC0094806
        self.set_report = "\x00" + "".join(chr(e) for e in self.key)
        fcntl.ioctl(self.fp, HIDIOCSFEATURE_9, self.set_report)

    def get_values(self):
        """generator"""

        while True:
            dct = {}
            lst = list()
            decrypted = self.decrypt(self.key, self.read_data())
            if decrypted[4] != 0x0d or (sum(decrypted[:3]) & 0xff) != decrypted[3]:
                print(self.hd(data), " => ", self.hd(decrypted),  "Checksum error")
            else:
                op = decrypted[0]
                val = decrypted[1] << 8 | decrypted[2]
                values[op] = val

                if (0x50 in values) and (0x42 in values):
                    co2 = values[0x50]
                    tmp = (values[0x42]/16.0-273.15)

                    dct['co2'] = co2
                    dct['tmp'] = tmp

                    lst.append(co2)
                    lst.append(tmp)

                    #yield dct
                    yield lst

    def read_data(self):
        return list(ord(e) for e in self.fp.read(8))

    def decrypt(self, key, data):
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

    def hd(self, d):
        return " ".join("%02X" % e for e in d)

