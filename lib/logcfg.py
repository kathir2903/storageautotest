#!/usr/bin/python
#Editor vim: ts=4:sw=4

#title      : logcfg.py
#description: This is just share the console handler between
#             files in the Package
#author     : "kathir.gitit@gmail.com"
#usage      : Cannot use as a stand alone
#py version : 2.7
"""
Log handler
"""

import logging

logger = logging.getLogger('logger')
#logger.setLevel(logging.DEBUG)
logger.setLevel(logging.NOTSET)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter()
ch.setFormatter(formatter)
logger.addHandler(ch)
