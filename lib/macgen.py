#!/usr/bin/python
import random
import dbconnect

class Macgen(object):
    """
    MAC generator - Generates a new mac
    check the database table if that mac
    exists. If mac is already taken, generate
    a new mac
    """
    def __init__(self):
        self.mycomp = [0x84, 0x56, 0x9f]
    def generate(self):
        mac = [self.mycomp[0],self.mycomp[1],self.mycomp[2],
                random.randint(0x90, 0xff),
                random.randint(0x00, 0xff),
                random.randint(0x00, 0xfe)]
        return ':'.join(map(lambda octet:"%02x" %octet, mac))
    def is_new_mac(self):
        mac = self.generate()
        if dbconnect.get_usedmac(mac):
            return mac
        else:
            return self.is_new_mac()
if __name__ == '__main__':
    """ Create a MAC """
    inst = Macgen()
    mac = inst.is_new_mac()
