#/usr/bin/python
import nose
from nose import *
from nose.tools import *
import unittest
from logger import *
import os
import time

class TestHelloModule(object):

    #def __init__(self):
        #self.t=10
        #self.log = Logger('12345', 'hello_test')
        #self.rep = reports.get_report((None, 'lla', "text/html",))
    #def setup(self):
        #self.log.initialize()
        #self.log.add_title("TITLE: Hello Test")
        #self.log.add_heading("HEADING: Hello Test")
        #self.usr = os.getlogin()
        #self.log.add_title("Functional")
        #self.log.info("User name: %s" %(self.usr))
        #self.log.info("Test Start Time: " )
        #self.log.info("Hello SETUP")
        #self.t = 10
    #def teardown(self):
        #self.log.info("Hello TEARDOWN")
        #self.t = None
        #del self.log
    #@with_setup(setup, teardown)
    def setUp(self):
        self.log = Logger('12345', 'hello_test')
        self.t = 10
        #self.logger = logcfg.logger

    def tearDown(self):
        self.t = None

    def hello_test(self):
        self.log()
        self.log.add_heading('Heading: Hello Test')
        self.log.passed("Hello TESTi PASSED")
        self.log.failed("Hello FAILED")
        self.log.info("Hello INFO")
        self.log.incomplete("Hello INCOMPLETE")
        self.log.diagnostic("Hello DIAGNOSTIC")
        assert_equal(self.t ,10)
        time.sleep(1)
    """
    def hru_test(self):
        self.log()
        #self.log = Logger('12345', 'fildata1')
        self.log.add_heading('Heading: How Are you? Test')
        self.log.passed(colored.green("How Are you PASSED"))
        self.log.failed("How Are you FAILED")
        self.log.info("How Are you INFO")
        self.log.incomplete("How Are you INCOMPLETE")
        self.log.diagnostic("How Are you DIAGNOSTIC")
        assert_equal(self.t ,10)
    """
