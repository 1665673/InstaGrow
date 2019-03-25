import sys
import logging
import getpass
import requests
import time
import json as _json

# reporter, arguments and patches
import reporter
import patch

# apply login patches for instapy
patch.apply()


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
        # from command line
        self.username = None
        self.password = None
        self.proxy_string = None
        self.instance = None
        # parsed arguments
        self.proxy_address = None
        self.proxy_port = None
        self.proxy_username = None
        self.proxy_password = None
        # for initializing instapy
        self.proxy_arguments = {}
        self.all_arguments = {}
        # begin parsing
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
            if self.proxy_string not in ["SKIP", "QUERY"]:
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
        if argc > 4:
            self.instance = sys.argv[4]
        self.all_arguments = {
            "username": self.username,
            "password": self.password, }
        self.all_arguments.update(self.proxy_arguments)
        Arguments.remove_none(self.all_arguments)

    def all(self):
        return self.all_arguments

    def proxy(self):
        return self.proxy_arguments


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
# CHECKIN_URL = "https://admin.socialgrow.live/admin/check-in"
CHECKIN_URL = "http://localhost:9000/admin/check-in"
DEFAULT_REPORT_FIELDS = {
    "instagramUser": "N/A",
    "systemUser": "N/A",
    "version": "N/A",
    "instance": "N/A",
    "proxy": "N/A"
}

# set a global reporter
_arguments = None
_reporter = None
_reporter_fields = DEFAULT_REPORT_FIELDS.copy()
# set a global logger
logger = logging.getLogger()


def proxy():
    global _arguments
    return _arguments.proxy()


def arguments():
    global _arguments
    return _arguments.all()


def config(**kw):
    global _reporter_fields
    _reporter_fields.update(kw)
    checkin()


def set_version(version):
    global _reporter_fields
    _reporter_fields.update({"version": version})


def set_instance(instance):
    global _reporter_fields
    _reporter_fields.update({"instance": instance})


def set_instagram_user(username):
    global _reporter_fields
    _reporter_fields.update({"instagramUser": username})


def checkin():
    global _reporter
    global _reporter_fields
    _reporter.checkin(CHECKIN_URL, _reporter_fields)


def begin_report(yes_or_no):
    if sys.stderr.begin_report:
        sys.stderr.begin_report(yes_or_no)


def get_stderr():
    return reporter.StreamHub.stderr


def get_stdout():
    return reporter.StreamHub.stdout


# build up communication with instapy. Hack print() and logger
# (1) redirect stdout/stderr to customised string streams
# (2) for each instapy IO operation, report it's buffer to node.js server
#
def init_environment():
    # process arguments
    global _arguments
    _arguments = Arguments()
    _reporter_fields.update({
        "instance": _arguments.instance,
        "instagramUser": _arguments.username,
        "proxy": _arguments.proxy_string,
        "systemUser": getpass.getuser()
    })

    # redirect streams
    stream = reporter.StreamHub()
    sys.stderr = stream
    # sys.stdout = stream

    # setup reporter
    global _reporter
    _reporter = reporter.Reporter()
    stream.set_reporter(_reporter)
    stream.begin_report(True)
    stream.begin_print(True)


# call initiate function
init_environment()

#
#
#
#   standard interface for reporter
#
#
#
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


def log(buffer, title="LOG", entry="messages"):
    buffer = "%s[%d] %s" % ((title + " " if title else ""), int(time.time()), buffer)
    reporter.StreamHub.stdout.write(buffer + "\n")
    global _reporter
    _reporter.send(buffer, entry)


def json(obj, entry="json"):
    reporter.StreamHub.stdout.write(entry + ": " + _json.dumps(obj) + "\n")
    global _reporter
    _reporter.push([obj], entry)


def data(name, value):
    json({
        "time": int(time.time()),
        "key": name,
        "value": value
    }, "data")


def event(type, name, data={}):
    reporter.StreamHub.stdout.write("EVENT [%d] %s %s\n" % (int(time.time()), type + "-" + name, _json.dumps(data)))
    obj = {
        "time": int(time.time()),
        "type": type,
        "name": name,
        "data": data
    }
    global _reporter
    _reporter.push([obj], "events")


def error(type, name, data={}):
    reporter.StreamHub.stdout.write("ERROR [%d] %s %s\n" % (int(time.time()), type + "-" + name, _json.dumps(data)))
    obj = {
        "time": int(time.time()),
        "type": type,
        "name": name,
        "data": data
    }
    global _reporter
    _reporter.push([obj], "errors")
