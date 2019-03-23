import logging
import requests
import json as _json
import sys
import io
import getpass
import time


#
#
#       class StreamHub (MyIO)
#       class Reporter
#
#
class StreamHub(io.StringIO):
    # backup stdout and stderr
    stdout = sys.stdout
    stderr = sys.stderr

    def __init__(self):
        super(StreamHub, self).__init__()
        self.save = False
        self.print = False
        self.log = False
        self.report = False
        self.reporter = None

    def begin_save(self, yes_or_no):
        self.save = yes_or_no

    def begin_print(self, yes_or_no):
        self.print = yes_or_no

    def begin_log(self, yes_or_no):
        self.log = yes_or_no

    def begin_report(self, yes_or_no):
        self.report = yes_or_no

    def set_reporter(self, rep):
        self.reporter = rep

    def write(self, buffer):
        if self.save:
            super(StreamHub, self).write(buffer)
        if self.print and StreamHub.stdout:
            StreamHub.stdout.write(buffer)
        if self.log and StreamHub.stderr:
            StreamHub.stderr.write(buffer)
        if self.report and self.reporter:
            self.reporter.send(buffer)


class Reporter:
    def __init__(self):
        self.id = None
        self.fields = {}
        self.checkin_url = None
        self.report_url = None
        self.payload = {"entries": {}}

    def __merge(self, array, entry):
        if entry not in self.payload["entries"]:
            self.payload["entries"][entry] = array
        else:
            self.payload["entries"][entry] += array
        self.payload["time"] = int(time.time())

    def __post(self):
        if not self.id or not self.report_url or len(self.payload.keys()) == 0:
            return
        headers = {'content-type': 'application/json'}
        self.payload["id"] = self.id

        try:
            requests.post(url=self.report_url, data=_json.dumps(self.payload), headers=headers)
        except Exception as e:
            pass
        finally:
            self.payload = {"entries": {}}

    def checkin(self, url, fields):
        self.fields = fields
        self.checkin_url = url
        try:
            res = requests.post(url=url, data=fields).json()
            self.id = res["id"]
            self.report_url = res["reportUrl"]
        except Exception as e:
            pass

    def send(self, buffer, entry="messages"):
        buffer = buffer.rstrip()
        if buffer == "":
            return
        self.push([buffer], entry)

    def push(self, array, entry):
        self.__merge(array, entry)
        self.__post()


#
#
#
#
#   easy to use interfaces
#   for project instapy
#
#
#
#


# MACROS
CHECKIN_URL = "https://admin.socialgrow.live/admin/check-in"
# CHECKIN_URL = "http://localhost:9000/admin/check-in"
DEFAULT_REPORT_FIELDS = {
    "instagramUser": "N/A",
    "systemUser": "N/A",
    "version": "N/A",
    "task": "N/A",
    "proxy": "N/A"
}

# set a global reporter
arguments = None
reporter = None
reporter_fields = DEFAULT_REPORT_FIELDS.copy()
# set a global logger
logger = logging.getLogger()


def set_version(version):
    reporter_fields.update({"version": version})


def set_task(task):
    reporter_fields.update({"task": task})


def checkin():
    global reporter
    global reporter_fields
    reporter.checkin(CHECKIN_URL, reporter_fields)


def get_stderr():
    return StreamHub.stderr


def get_stdout():
    return StreamHub.stdout


"""""""""""""""""""""""""""""""""""""""
def log(msg, *var, **kw):
    title = ""
    if "title" in kw:
        title = kw["title"] + " "
        del kw["title"]
    logger.warning("%s[%d] %s" % (title, int(time.time()), msg), *var, **kw)


def info(*var, **kw):
    log(*var, **kw, title="INFO")
"""""""""""""""""""""""""""""""""""""""


def log(buffer, title="INFO", entry="messages"):
    buffer = "%s[%d] %s" % ((title + " " if title else ""), int(time.time()), buffer)
    StreamHub.stdout.write(buffer + "\n")
    reporter.send(buffer, entry)


def event(buffer):
    log(buffer, "EVENT", "events")


def error(buffer):
    log(buffer, "ERROR", "errors")


def json(obj, entry="json"):
    StreamHub.stdout.write(_json.dumps(obj) + "\n")
    reporter.push([obj], entry)


def data(name, value):
    json({
        "name": name,
        "time": int(time.time()),
        "value": value
    }, "data")


#
#
#
#
#
#
################################
#   an useful tool for processing arguments
#
class Arguments:
    def __init__(self):
        self.username = None
        self.password = None
        self.proxy_string = None
        self.proxy_address = None
        self.proxy_port = None
        self.proxy_username = None
        self.proxy_password = None
        self.proxy_arguments = {}
        self.all_arguments = {}
        self.read_arguments()

    @staticmethod
    def remove_none(arguments):
        delete = [key for key in arguments if arguments[key] is None]
        for key in delete:
            del arguments[key]

    def read_arguments(self):
        argc = len(sys.argv)
        if argc > 1:
            self.username = sys.argv[1]
        if argc > 2:
            self.password = sys.argv[2]
        if argc > 3:
            self.proxy_string = sys.argv[3]
            self.proxy_address, self.proxy_port, self.proxy_username, self.proxy_password, *_ \
                = self.proxy_string.split(':') + [None] * 4
            self.proxy_port = int(self.proxy_port)
            self.proxy_arguments = {
                "proxy_address": self.proxy_address,
                "proxy_port": self.proxy_port,
                "proxy_username": self.proxy_username,
                "proxy_password": self.proxy_password
            }
            Arguments.remove_none(self.proxy_arguments)
        self.all_arguments = {
            "username": self.username,
            "password": self.password, }
        self.all_arguments.update(self.proxy_arguments)
        Arguments.remove_none(self.all_arguments)

    def all(self):
        return self.all_arguments

    def proxy(self):
        return self.proxy_arguments


# build up communication with instapy. Hack print() and logger
# (1) redirect stdout/stderr to customised string streams
# (2) for each instapy IO operation, report it's buffer to node.js server
#
def init_reporter():
    # process arguments
    global arguments
    arguments = Arguments()
    reporter_fields.update({
        "instagramUser": arguments.username,
        "proxy": arguments.proxy_string,
        "systemUser": getpass.getuser()
    })

    # redirect streams
    stream = StreamHub()
    sys.stderr = stream
    # sys.stdout = stream

    # setup reporter
    global reporter
    reporter = Reporter()
    stream.set_reporter(reporter)
    stream.begin_report(True)
    stream.begin_print(True)


# call initiate function
init_reporter()
