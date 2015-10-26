#!/usr/bin/python
"""
get environ settings
"""
import os
pn = os.environ['PN']
prod = os.environ['PROD']
mail_list = os.environ['MAILLIST']
utils_path = os.environ['UTILS']
path = '/var/www/html/testrecords/' + prod.lower() + '/'
print path
out = os.popen("/sbin/ifconfig eth0 | grep 'inet addr:' | cut -d: -f2 | awk '{ print $1}'")
ip = out.readline().strip()
url = "http://"+ip
out.close()
