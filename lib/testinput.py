#!/usr/bin/python

import argparse
import re

class userMenu(object):

    def get_ch_sn(self, ch_sn, match=True):
        #Kathir: SN Format must go to generic module or to database
        #ch_sn = (raw_input(YLO + 'Enter the CHASSIS SN(0123456789): '+WH)).strip()
        #ch_sn = (raw_input(YLO + 'Enter the CHASSIS SN(0123456789): '+WH)).strip()
        ch_sn_format1 = re.compile(r'[A-Z]{1}\d{14}$')
        #ch_sn_format1 = re.compile(r'[0-9]{10}$')
        match1 = re.match(ch_sn_format1, ch_sn)
        if match1:
            print "Chassis SN entered is Valid %s" %ch_sn
            self.valid_ch_sn = ch_sn
        else:
            #print "Invalid SN Format. Retry..."
            #return self.get_ch_sn(False)
            raise argparse.ArgumentTypeError("Chassis SN format must be S12345678901234")
        return self.valid_ch_sn

    def get_node_sn(self, node_sn, match=True):
        #sn = (raw_input(YLO + 'Enter the (NODE)UUT VENDOR SN(Startswith Z): ' +WH)).strip()
        sn_format2 = re.compile(r'[A-Z]{2}\d{3}[A-Z]{1}\d{6}$')

        match2 = re.match(sn_format2, node_sn)
        if not match2: #REMOVE NOT
            print "Node SN entered is Valid %s" %(node_sn)
            self.valid_node_sn = node_sn
        else:
            raise argparse.ArgumentTypeError("Vendor Node SN format must be ZA123B123456")
            #return self.get_node_sn(False)
        return self.valid_node_sn

    def get_comments(self, inp=",.", match=True):
        form = re.compile(r'.+?$')
        match1 = re.match(form, inp)
        if match1:
            self.comments = inp
        else:
            print "Please enter your comments and end it with ."
            raise argparse.ArgumentTypeError("Comment format must be <Any words with space>")
            #return self.get_comments(False)
        return self.comments

class testInput(userMenu):

    def user_input(self, test):
        parser = argparse.ArgumentParser(prog = test, usage='nosetests %(prog)s --ch_sn <CHASSIS SN> --node_sn <NODE SN> --comment <Any characters must end with .>')
        parser.add_argument('-ch_sn', type=self.get_ch_sn, required=True)
        parser.add_argument('-node_sn', type=self.get_node_sn, required=True)
        parser.add_argument('-comment', type=self.get_comments, required=False)

        args = parser.parse_args()
        return args

if __name__ == "__main__":
    """ self test """
    inst = testInput()
    inst.user_input('CheckSensors_Test.py')
    
