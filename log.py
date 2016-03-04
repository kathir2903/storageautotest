
""" Logger Module """
import os
import datetime
import sys
import traceback

ANSICOLORS = {'none': 0,
              'black': 30,
              'red': 31,
              'green': 32,
              'yellow': 33,
              'blue': 34,
              'magenta': 35,
              'cyan': 36,
              'white': 37,
              'bold': 1,
              'italic': 3,
              'underline': 4,
              'inverse': 7,
              'bgblack': 40,
              'bgred': 41,
              'bggreen': 42,
              'bgyellow': 43,
              'bgblue': 44,
              'bgpurple': 45,
              'bgcyan': 46,
              'bgwhite': 47 }

LOG_WARN   = 0
LOG_INFO   = 1
LOG_STATUS = 2
LOG_DEBUG  = 3

def colorize(text, attributes=None):
    """
    apply ansi colors in attributes list to text
    """
    if not attributes:
        return text

    return '\033[' + ';'.join([str(ANSICOLORS[a]) for a in attributes]) + \
        'm' + text + '\033[0m'

class Logger(object):
    
    def __init__(self, level=LOG_STATUS):
        self.level = level
        self.outio = sys.stdout
        self.statusio = sys.stdout
        self.interactive = hasattr(self.statusio, 'isatty') and self.statusio.isatty()
        self.colorize = self.interactive

    def set_statusfd(self, fd):
        """
        set the file descriptor 
        which will be used for all log operations
        """
        self.statusio = os.fdopen(fd, 'w')
        self.interactive = hasattr(self.statusio, 'isatty') and self.statusio.isatty()
        self.colorize = self.interactive

    def output(self, msg):
        """
        write MSG to stdout, 
        all other informational '
        messages are written to statusfd"""
        self.outio.write(msg + '\n')
        self.outio.flush()

    def title(self, msg):
        self.write(self.beautify(msg, ['bold', 'magenta'], label='TITLE'))
        
    def warn(self, msg):
        if self.level >= LOG_WARN:
            self.write(self.beautify(msg, ['bold', 'yellow'], label='WARN'))

    def failed(self, msg):
        if self.level >= LOG_WARN:
            self.write(self.beautify(msg, ['bold', 'red'], label='FAIL'))

    def info(self, msg):
        if self.level >= LOG_INFO:
            self.write(self.beautify(msg, ['cyan'], label='INFO'))

    def status(self, msg):
        if self.level >= LOG_STATUS:
            self.write(self.beautify(msg, ['blue'], label='STATUS'))

    def passed(self, msg):
        if self.level >= LOG_DEBUG:
            self.write(self.beautify(msg, ['green'], label='PASSED'))

    def traceback(self):
        """print an exception"""
        self.fail(traceback.format_exc().strip())

    def beautify(self, msg, colors, label=None):
        if label != 'TITLE':
            msg = '[%s] %s %s' % (label, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'), msg)
        else:
            msg = '====\n[%s] %s\n%s\n====' % (label, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'), msg)
        return colorize(str(msg), colors)

    def write(self, msg):
        """ 
        write log message
        to stdout or to a file descriptor 
        """
        self.statusio.write(msg + '\n')
        self.statusio.flush()
