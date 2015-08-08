#!/usr/bin/python
"""
Various test reports and formatters are defined here. These are used for unit
test and test framework reporting.

Generally, you don't use this package in the normal way. Instead, you call the
'get_report' function in this module with a particular pattern of paramters and
it will return a report object according to that. Any necessary report objects
and modules are specified there, and imported as necessary.

e.g.:

     get_report( ("StandardReport", "reportfile", "text/plain") )

Note that the argument is a single tuple. A list of these may be supplied for a
"stacked" report. 

The first argument is a report object name (plus module, if necessary). Any
remaining argumments in the tuple are passed to the specified reports
constructor.

"""

#__all__ = ['Html', 'ANSI', 'Email', 'Eventlog']

import sys, os
import UserFile
import time

NO_MESSAGE = "no message"

# map mime type to formatter class name and file extension
_FORMATTERS = {
	None: ("StandardFormatter", "txt"), # default
	"text/plain": ("StandardFormatter", "txt"), # plain text
	"text/ascii": ("StandardFormatter", "asc"), # plain text
	"text/html": ("Html.HTMLFormatter", "html"), # HTML 
	"text/ansi": ("ANSI.ANSIFormatter", "ansi"), # text with ANSI-term color escapes
}


class NullFormatter(object):
	def title(self, title):
		return ""
	def heading(self, text, level=1):
		return ""
	def paragraph(self, text, level=1):
		return ""
	def message(self, msgtype, msg, level=1):
		return ""
	def passed(self, msg=NO_MESSAGE, level=1):
		return self.message("PASSED", msg, level)
	def failed(self, msg=NO_MESSAGE, level=1):
		return self.message("FAILED", msg, level)
	def completed(self, msg=NO_MESSAGE, level=1):
		return self.message("COMPLETED", msg, level)
	def error(self, msg=NO_MESSAGE, level=1):
		return self.message("ERROR", msg, level)
        def incomplete(self, msg=NO_MESSAGE, level=1):
		return self.message("INCOMPLETE", msg, level)
	def abort(self, msg=NO_MESSAGE, level=1):
		return self.message("ABORT", msg, level)
	def info(self, msg, level=1):
        #msg_type = "INFO [%s]" % (time.strftime('%H:%M:%S'))
                msg_type = "INFO [%s]" % (time.strftime('%c'))
		return self.message(msg_type, msg, level)
	def diagnostic(self, msg, level=1):
		return self.message("DIAGNOSTIC", msg, level)
	def text(self, text):
		return ""
	def url(self, text, url):
		return ""
	def page(self):
		return ""
	def endpage(self):
		return ""
	def section(self):
		return ""
	def endsection(self):
		return ""
	def initialize(self, *args):
		return ""
	def finalize(self):
		return ""

class NullReport(object):
	"""NullReport defines the interface for report objects. It is the base
	class for all Report objects."""
	# overrideable methods
	def write(self, text):
		raise NotImplementedError, "override me!"
	def writeline(self, text=""):
		raise NotImplementedError, "override me!"
	def writelines(self, lines):
		raise NotImplementedError, "override me!"
	def initialize(self, *args): pass
	def logfile(self, filename): pass
	def finalize(self): pass
	def add_title(self, title): pass
	def add_heading(self, text, level=1): pass
	def add_message(self, msgtype, msg, level=1): pass
	def add_summary(self, text): pass
	def add_text(self, text): pass
	def add_url(self, text, url): pass
	def passed(self, msg=NO_MESSAGE): pass
	def failed(self, msg=NO_MESSAGE): pass
	def incomplete(self, msg=NO_MESSAGE): pass
	def abort(self, msg=NO_MESSAGE): pass
	def info(self, msg): pass
	def diagnostic(self, msg): pass
	def newpage(self): pass
	def newsection(self): pass


class StandardReport(UserFile.FileWrapper, NullReport):
	"""StandardReport writes to a file or file-like object, such as stdout. If
the filename specified is "-" then use stdout.	"""
	def __init__(self, name=None, formatter=None):
		self._do_close = 0
		self._formatter, self.fileext = get_formatter(formatter)
		if type(name) is str:
			if name == "-":
				fo = sys.stdout
			else:
				name = "%s.%s" % (name, self.fileext)
				fo = file(os.path.expanduser(os.path.expandvars(name)), "w")
				self._do_close = 1
		elif name is None:
			fo = sys.stdout
		else:
			fo = name # better be a file object
		UserFile.FileWrapper.__init__(self, fo)
	
	filename = property(lambda s: s._fo.name)
	filenames = property(lambda s: [s._fo.name])

	def initialize(self):
		self.write(self._formatter.initialize())

	def finalize(self):
		self.write(self._formatter.finalize())
		self.flush()
		if self._do_close:
			self.close()

	def add_title(self, title):
		self.write(self._formatter.title(title))

	def add_heading(self, text, level=1):
		self.write(self._formatter.heading(text, level))

	def add_message(self, msgtype, msg, level=1):
                msgtype = "%s" % (msgtype) 
		self.write(self._formatter.message(msgtype, msg, level))

	def passed(self, msg=NO_MESSAGE, level=1):
		self.write(self._formatter.passed(msg, level))

	def failed(self, msg=NO_MESSAGE, level=1):
		self.write(self._formatter.failed(msg, level))
	
        def error(self, msg=NO_MESSAGE, level=1):
		self.write(self._formatter.error(msg, level))
		
	def completed(self, msg=NO_MESSAGE, level=1):
		self.write(self._formatter.completed(msg, level))

	def incomplete(self, msg=NO_MESSAGE, level=1):
		self.write(self._formatter.incomplete(msg, level))

	def abort(self, msg=NO_MESSAGE, level=1):
		self.write(self._formatter.abort(msg, level))

	def info(self, msg, level=1):
		self.write(self._formatter.info(msg, level))

	def diagnostic(self, msg, level=1):
		self.write(self._formatter.diagnostic(msg, level))

	def add_text(self, text):
		self.write(self._formatter.text(text))

	def add_url(self, text, url):
		self.write(self._formatter.url(text, url))

	def add_summary(self, text):
		self.write(self._formatter.summary(text))

	def newpage(self):
		self.write(self._formatter.page())

	def newsection(self):
		self.write(self._formatter.section())


class StandardFormatter(NullFormatter):
	"""The Standard formatter just emits plain ASCII text."""
	MIMETYPE = "text/plain"
	def title(self, title):
		s = ["="*len(title)]
		s.append("%s" % title)
		s.append("="*len(title))
		s.append("\n")
		return "\n".join(s)

	def heading(self, text, level=1):
		s = ["\n"]
		s.append("%s%s" % ("  "*(level-1), text))
		s.append("%s%s" % ("  "*(level-1), "-"*len(text)))
		s.append("\n")
		return "\n".join(s)

	def message(self, msgtype, msg, level=1):
                return "%s%s [%s] %s\n" % ("  "*(level-1), msgtype, time.strftime('%H:%M:%S'), msg)

	def text(self, text):
		return text

	def url(self, text, url):
		return "%s: <%s>\n" % (text, url)

	def summary(self, text):
		return text

	def page(self):
		return "\n\n\n"

	def section(self):
		return "\n"

	def paragraph(self, text, level=1):
		return text+"\n"


class FailureReport(StandardReport):
	"FailureReport() A Report type that only prints failures and diagnostics."
	def __init__(self, name=None, formatter=None):
		StandardReport.__init__(self, name, formatter)
		self.state = 0

	def add_message(self, msgtype, msg, level=1):
		if msgtype == "FAILED":
			self.state = -1
			self.write(self._formatter.message(msgtype, msg, level))
		else:
			if self.state == -1 and msgtype == "DIAGNOSTIC":
				self.write(self._formatter.message(msgtype, msg, level))
			else:
				self.state = 0

class TerseReport(StandardReport):
	"TerseReport() A Report type that only prints results."
	def __init__(self, name=None, formatter=None):
		StandardReport.__init__(self, name, formatter)

	def add_message(self, msgtype, msg):
		if msgtype  in ("PASSED", "FAILED"):
			self.write(self._formatter.message(msgtype, msg, level))

	#def add_title(self, title): pass
	def add_heading(self, text, level=1): pass
	def add_summary(self, text): pass
	def add_text(self, text): pass
	def add_url(self, text, url): pass


class StackedReport(object):
	"""StackedReport allows stacking of reports, which creates multiple
	reports simultaneously.  It adds a new method, add_report() that is
	used to add on a new report object. """ 
	def __init__(self, rpt=None):
		self._reports = []
		if rpt:
			self.add_report(rpt)

	def add_report(self, rpt_or_name, *args):
		"""adds a new report to the stack."""
		if type(rpt_or_name) is str:
			rpt = get_report(rpt_or_name, *params )
			self._reports.append(rpt)
		elif isinstance(rpt_or_name, NullReport):
			self._reports.append(rpt_or_name)
		else:
			raise ValueError, "StackedReport: report must be name of report or report object."

	def _get_names(self):
		rv = []
		for rpt in self._reports:
			fn = rpt.filename
			if fn:
				rv.append(fn)
		return rv
	filenames = property(_get_names)

	def add_title(self, title):
		map(lambda rpt: rpt.add_title(title), self._reports)

	def write(self, text):
		map(lambda rpt: rpt.write(text), self._reports)

	def writeline(self, text):
		map(lambda rpt: rpt.writeline(text), self._reports)

	def writelines(self, text):
		map(lambda rpt: rpt.writelines(text), self._reports)

	def add_heading(self, text, level=1):
		map(lambda rpt: rpt.add_heading(text, level), self._reports)

	def add_message(self, msgtype, msg, level=1):
 		map(lambda rpt: rpt.add_message(msgtype, msg, level), self._reports)

	def passed(self, msg=NO_MESSAGE):
		map(lambda rpt: rpt.passed(msg), self._reports)

	def failed(self, msg=NO_MESSAGE):
		map(lambda rpt: rpt.failed(msg), self._reports)

        def error(self, msg=NO_MESSAGE):
		map(lambda rpt: rpt.error(msg), self._reports)

	def incomplete(self, msg=NO_MESSAGE):
		map(lambda rpt: rpt.incomplete(msg), self._reports)

	def abort(self, msg=NO_MESSAGE):
		map(lambda rpt: rpt.abort(msg), self._reports)

	def info(self, msg):
		map(lambda rpt: rpt.info(msg), self._reports)

	def diagnostic(self, msg):
		map(lambda rpt: rpt.diagnostic(msg), self._reports)

	def add_text(self, text):
		map(lambda rpt: rpt.add_text(text), self._reports)

	def add_url(self, text, url):
		map(lambda rpt: rpt.add_url(text, url), self._reports)

	def add_summary(self, text):
		map(lambda rpt: rpt.add_summary(text), self._reports)

	def newpage(self):
		map(lambda rpt: rpt.newpage(), self._reports)

	def logfile(self, fn):
		map(lambda rpt: rpt.logfile(fn), self._reports)

	def initialize(self):
		map(lambda rpt: rpt.initialize(), self._reports)

	def finalize(self):
		map(lambda rpt: rpt.finalize(), self._reports)


def _get_object(name):
	try:
		robj = getattr(sys.modules[__name__], name)
		return robj
	except AttributeError:
		i = name.find(".")
		if i >= 0:
			#repmod = __import__("%s.%s" % (__name__, name[:i]), globals(), locals(), ["*"])
			repmod = __import__('Html', globals(),locals(), ["*"])
			robj = getattr(repmod, name[i+1:])
			return robj
		else:
			raise ValueError, "%s is not a valid name" % (name,)

def get_report(args):
	"""
	If args is a list, it should contain argument-tuples that specify a series
	of reports. A StackedReport object will be generated in that case.
	Otherwise, args should be a tuple, with first arg the name of a report or
	None (for StandardReport), and remaining args get passed to report
	initializer.  
	if type(args) is list:
		rpt = StackedReport()
		for subargs in args:
			n = get_report(subargs)
			rpt.add_report(n)
		return rpt
	"""
	name = args[0]
	if name is None:
		return apply(StandardReport, args[1:])
	robj = _get_object(name)
	return apply(robj, args[1:])

def get_formatter(name, *args):
	objname, ext = _FORMATTERS.get(name, (name, "txt"))
	fobj = _get_object(objname)
	form = apply(fobj, args)
	return form, ext


if __name__ == "__main__":
	rpt = get_report( ("StandardReport", "-", "text/plain") )
	rpt.initialize()
	rpt.add_title("The Title")
	rpt.add_heading("Some heading")
	rpt.info("some info")
	rpt.passed("A message for a passed condition.")
	rpt.failed("A message for a failed condition.")
	rpt.error("A message for a error condition.")
	rpt.finalize()

