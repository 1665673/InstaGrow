import logging
import requests
import sys
import io
import getpass

# MACROS
REPORT_SERVER = "https://admin.socialgrow.live"
CHECK_IN_URL = REPORT_SERVER + "/admin/check-in"
REPORT_STATUS_URL = REPORT_SERVER + "/admin/report-status"
DEFAULT_REPORT_FIELDS = {
    "instagramUser": "N/A",
    "systemUser": "N/A",
    "version": "N/A",
    "task": "N/A",
    "proxy": "N/A"
}

# backup stdout and stderr
stdout = sys.stdout
stderr = sys.stderr
# set a global reporter
reporter = None
# set a global logger
logger = logging.getLogger()


# build up communication with instapy. Hack print() and logger
# (1) redirect stdout/stderr to customised string streams
# (2) for each instapy IO operation, report it's buffer to node.js server
#
class MyIO(io.StringIO):
    def __init__(self):
        super(MyIO, self).__init__()
        self.report = False
        self.reporter = None

    def begin_report(self, yes_or_no):
        self.report = yes_or_no

    def set_reporter(self, rep):
        self.reporter = rep

    def write(self, buffer):
        super(MyIO, self).write(buffer)
        stdout.write(buffer)
        if self.report and self.reporter is not None:
            self.reporter.send(buffer)


class Reporter:
    def __init__(self, fields):
        self.fields = fields.copy()

    def set_fields(self, fields):
        self.fields = fields.copy()

    def get_fields(self):
        return self.fields.copy()

    def update_fields(self, fields):
        self.fields.update(fields)

    def send(self, buffer):
        buffer = buffer.rstrip()
        if buffer == "":
            return

        data = self.fields.copy()
        data.update({"message": buffer})

        try:
            requests.post(url=REPORT_STATUS_URL, data=data)
        except ConnectionError:
            pass


def init_reporter():
    # redirect streams
    stream = MyIO()
    sys.stderr = stream
    sys.stdout = MyIO()  # another stream for stdout, do not enable report on this stream
    # sys.stdout = io.StringIO()  # or discard everything in stdout by directing to a never-use stream

    # check in this process to server
    # cli_args = parse_cli_args()
    # instagram_user = cli_args.username
    system_user = getpass.getuser()

    # setup reporter
    global reporter
    fields = DEFAULT_REPORT_FIELDS.copy()
    fields.update({
        # "instagramUser": instagram_user,
        "systemUser": system_user
    })
    reporter = Reporter(fields)

    # begin report stderr
    begin_report_stderr()


def set_report_url(url):
    global REPORT_STATUS_URL
    REPORT_STATUS_URL = url


def set_instagram_user(instagram_user="unknown"):
    global reporter
    if reporter is not None:
        reporter.update_fields({
            "instagramUser": instagram_user
        })


def set_version(version="N/A"):
    global reporter
    if reporter is not None:
        reporter.update_fields({
            "version": version
        })


def set_task(task="N/A"):
    global reporter
    if reporter is not None:
        reporter.update_fields({
            "task": task
        })


def set_proxy(proxy="N/A"):
    global reporter
    if reporter is not None:
        reporter.update_fields({
            "proxy": proxy
        })


def update_report_fields(fields):
    global reporter
    if reporter is not None:
        reporter.update_fields(fields)


def begin_report_stderr(begin=True):
    # link reporter to stderr stream and begin report
    sys.stderr.set_reporter(reporter)
    sys.stderr.begin_report(begin)


def begin_report_stdout(begin=True):
    # link reporter to stderr stdout and begin report
    sys.stdout.set_reporter(reporter)
    sys.stdout.begin_report(begin)


def get_stderr():
    return stderr


def get_stdout():
    return stdout


def log(*var, **kw):
    logger.warning(*var, **kw)


def event(*var, **kw):
    logger.warning("EVENT", *var, **kw)


def error(*var, **kw):
    logger.warning("ERROR", *var, **kw)


# call initiate function
init_reporter()


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
            "password": self.password,        }
        self.all_arguments.update(self.proxy_arguments)
        Arguments.remove_none(self.all_arguments)
        self.update_reporter()

    def update_reporter(self):
        if self.username:
            set_instagram_user(self.username)
        if self.proxy_string:
            set_proxy(self.proxy_string)

    def all(self):
        return self.all_arguments

    def proxy(self):
        return self.proxy_arguments
