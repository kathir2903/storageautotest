#!/usr/bin/python
#Editor vim: ts=4:sw=4

#title      : logger.py
#description: Logging results in console and HTML
#author     : "kathir.gitit@gmail.com"
#usage      : python logger.py
#py version : 2.7


import os
import logging
import time
from Html import *
#from clint.textui import colored
import logcfg
from define import *
"""
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s \
        - %(levelname)s - %(message)s')
print formatter
ch.setFormatter(formatter)

logger.addHandler(ch)

logger.debug('debug msg')
logger.info('info msg')
logger.warn('warn msg')
logger.error('error msg')
logger.critical('critical msg')
"""
#CLR = '\033[95m'
BLUE = '\033[94m'
PASS = '\033[92m'
YLO = '\033[93m'
FAIL = '\033[91m'
WHITE = '\033[0m'
BOLD = '\033[1m'
UL = '\033[4m'

class Logger(object):
    """
    Logging the test results in Console
    and in Html log file.
    Html file log will be linked the UUT SN and test time
    in the database can be viewed in browser
    """

    def __init__(self, *args):
        """ Initialize """
        self.path = path
        self.args = args
        self.logger = logcfg.logger
        self.fn = None     
    def __call__(self):
        """ Caller for custom behaviour when
        logger instantiated """
        self.dirname = time.strftime('%Y-%m-%d')
        self.res = os.path.dirname(self.path)
        try:
            if not os.path.exists(self.res+self.dirname):
                os.mkdir(self.res+"/"+self.dirname)
        except OSError as (errno, strerror):
            print errno, strerror
        #self.sndir = self.args[0] +"-"+ time.strftime('%Y%m%d-%H%M%S')
        self.sndir = self.args[0] +"-"+ time.strftime('%Y%m%d')
        try:
            if not os.path.exists(self.res+self.dirname+self.sndir):
                self.sn_path = self.logpath()
        except OSError as (errno, strerror):
            print errno, strerror

        os.chdir(self.res+"/"+self.dirname+"/"+self.sndir)
        #fd = open('test_records.html', 'w')
        self.fn = self.args[1] + "-" + time.strftime('%Y%m%d-%H%M%S')
        print "-------------------------"
        print self.fn
        print "-------------------------"
        self.fd = reports.get_report((None, self.fn, "text/html",))
        #self.log_to_console()

    def logpath(self):
        """ log path """
        return os.mkdir(self.res+"/"+self.dirname+"/"+self.sndir)

    def fname(self):
        """ return file name """
        return self.fn

    def getpath(self):
        """ return current working directory """
        return os.getcwd()
        
    def info(self, msg):
        """ info msg """
        self.fd.info(msg)
        msg = "[%s] INFO :" % (time.strftime('%c'))+ msg
        self.logger.info(msg)

    def passed(self, msg):
        """ pass msg """
        #self.logger = lh
        self.fd.passed(msg)
        msg = PASS + "[%s] PASSED :" % (time.strftime('%c'))+ msg + WHITE
        self.logger.info(msg)

    def failed(self, msg):
        """ fail msg """
        #self.logger = lh
        self.fd.failed(msg)
        msg = FAIL + "[%s] FAILED :" % (time.strftime('%c'))+ msg + WHITE
        self.logger.error(msg)

    def incomplete(self, msg):
        """ incomplete msg """
        #self.logger = lh
        self.fd.incomplete(msg)
        msg = YLO + "[%s] INCOMPLETE :" % (time.strftime('%c'))+ msg + WHITE
        self.logger.error(msg)

    def diagnostic(self, msg):
        """ diags msg """
        #self.logger = lh
        self.fd.diagnostic(msg)
        msg = BLUE + "[%s] DIAGNOSTIC :" % (time.strftime('%c'))+ msg + WHITE
        self.logger.error(msg)

    def add_title(self, msg):
        """ add title to the test """
        #self.logger = lh
        self.fd.add_title(msg)
        msg = BOLD + '\033[7m' + msg + WHITE
        self.logger.info(msg)

    def add_heading(self, tname, **msg):
        """ add heading to the test """
        self.fd.add_heading(tname)
        start_time = time.strftime('%c')
        login = os.getlogin()
        swver = os.system("grep 'VERSION' ../etc/VERSION | cut -d '=' -f 2")
        for name in msg:
            self.fd.info("%s: %s" %(name, msg[name]))
        self.fd.info("Test_Operator: %s" %login)
        self.fd.info("Test_Software_Release: %s" %swver)
        self.fd.info("Test_Start_Time: %s" %start_time)
        #msg = BOLD + UL + msg + WHITE
        #self.logger.info(msg)

if __name__ == "__main__":
        """ self test """
        init = Logger("1234567")
        init()
