#!/usr/bin/python

"""
Report object that creats XHTML format reports. 

"""

import sys
import reports

def escape(s):
	s = s.replace("&", "&amp;") # Must be first
	s = s.replace("<", "&lt;")
	s = s.replace(">", "&gt;")
	s = s.replace('"', "&quot;")
	return s

class HTMLFormatter(reports.NullFormatter):
	MIMETYPE = "text/html"
	_MSGTYPESUB = {
		"PASSED":'<font color="green">PASSED</font>',
		"FAILED":'<font color="red">FAILED</font>',
		"ERROR":'<font color="red">ERROR</font>',
		"COMPLETED":'<font color="green">COMPLETED</font>',
		"INCOMPLETE":'<font color="yellow">INCOMPLETE</font>',
		"ABORTED":'<font color="yellow">ABORTED</font>',
		"INFO":"INFO",
		"DIAGNOSTIC":'<font color="brown">DIAGNOSTIC</font>',
	}

	def title(self, title):
		s = ["<br><h1>"]
		s.append(escape(title))
		s.append("</h1>\n")
		return "".join(s)

	def heading(self, text, level=1):
		s = []
		s.append("\n<h%s>" % (level,))
		s.append(escape(text))
		s.append("</h%s>\n" % (level,))
		return "".join(s)

	def paragraph(self, text):
		return "<p>%s</p>\n" % (escape(text),)

	def message(self, msgtype, msg, level=1):
		msg = str(msg)
		msgtype = self._MSGTYPESUB.get(msgtype, msgtype)
		if msg.find("\n") > 0:
			return "%s: <pre>%s</pre><br>\n" % (msgtype, escape(msg))
		else:
			return '<font face="courier" size="-1">%s: %s</font><br>\n' % (msgtype, escape(msg))

	def text(self, text):
		return "<pre>\n%s\n</pre>\n" % (text,)

	def url(self, text, url):
		return '<a href="%s">%s</a>\n' % (url, text)

	def summary(self, text):
		sum = "<pre>\n%s\n</pre>\n" % (text,)
		return sum.replace("PASSED", self._MSGTYPESUB["PASSED"])
	def section(self):
		return "<hr>\n"

	def page(self):
		return "<br><hr><br>\n"

	def initialize(self):
		return """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Final//EN">
<html>
  <head>
	<title>Test Results</title>
  </head>
<body>
"""
	def finalize(self):
		return "\n</body>\n</html>\n"




if __name__ == "__main__":
	#report = reports.get_report((None, "-", "text/html",))
	report = reports.get_report((None, 'lla', "text/html",))
	report.initialize()
	report.info("Some self test info.")
	report.passed("Hello World")
	report.incomplete("Hello World")
	report.diagnostic("Hello World")
	report.passed("Hello World")
	report.passed("Hello World")
	report.finalize()

