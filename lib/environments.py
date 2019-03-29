import sys
import logging
import getpass
import requests
import time
import argparse
import json as _json
from instapy.util import web_address_navigator
import os
from dotenv import load_dotenv, find_dotenv

# reporter, arguments and patches
from . import reporter
from . import patch

#
#
#
#
#   easy to use interfaces for InstaGrow
#
#
#
#
#

load_dotenv(find_dotenv())
SERVER = os.getenv("SERVER")
CHECKIN_URL = SERVER + "/admin/check-in"
DEFAULT_FOLLOWER_TRACKING_GAP = 1800
# MACROS
# DEFAULT_REPORT_FIELDS = {
#     "instagramUser": "N/A",
#     "systemUser": "N/A",
#     "version": "N/A",
#     "instance": "N/A",
#     "proxy": "N/A"
# }

# set a global reporter
_args = {}
_arguments = {}
_reporter = reporter.Reporter()
_reporter_fields = {}
# set a global logger
logger = logging.getLogger()


def arguments():
    global _arguments
    return _arguments


def args():
    global _args
    return _args


def config(**kw):
    # apply login patches for instapy
    patch.apply()

    # call initiate function
    init_environment()

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


#
#
#
#   initialize the big environment
#   (1) parse and process arguments
#   (2) config StreamHub and Reporter
#
#
def init_environment():
    # process arguments and config related environment
    global _args
    global _reporter_fields
    process_arguments()
    _reporter_fields.update({
        "instance": _args.instance,
        "instagramUser": _args.username,
        # "proxy": _args.proxy,
        # "systemUser": getpass.getuser()
    })
    remove_none(_reporter_fields)

    # redirect streams
    stream = reporter.StreamHub()
    sys.stderr = stream
    # sys.stdout = stream

    # setup reporter
    global _reporter
    # reporter = reporter.Reporter()
    stream.set_reporter(_reporter)
    stream.begin_report(True)
    stream.begin_print(True)


def process_arguments():
    global _args
    parser = argparse.ArgumentParser()
    parser.add_argument("username", nargs='?', type=str)
    parser.add_argument("password", nargs='?', type=str)
    parser.add_argument("proxy", nargs='?', type=str)
    parser.add_argument("-i", "--instance", type=str)
    parser.add_argument("-p", "--pull", action="store_true")
    parser.add_argument("-q", "--query", action="store_true")
    parser.add_argument("-rp", "--retry-proxy", action="store_true")
    parser.add_argument("-ap", "--allocate-proxy", action="store_true")
    _args = parser.parse_args()

    if _args.pull:
        from . import pull
        pull.userdata()

    if not _args.username:
        _args.username = "unknown-user-tba"

    global _arguments
    _arguments = {
        "username": _args.username,
        "password": _args.password,
    }
    proxy = parse_proxy_keyword(_args.proxy)
    _arguments.update(proxy)
    remove_none(_arguments)
    # print(_args)
    # print(_arguments)
    #
    #
    #
    #   standard interface for reporter
    #
    #
    #


def remove_none(arguments):
    delete = [key for key in arguments if arguments[key] is None]
    for key in delete:
        del arguments[key]


def parse_proxy_keyword(proxy_string):
    proxy_list = proxy_string.split(":") if proxy_string else []
    proxy_address, proxy_port, proxy_username, proxy_password, *_ = proxy_list + [None] * 4
    proxy_port = None if not proxy_port else (int(proxy_port) if proxy_port.isdigit() else None)
    proxy = {
        "proxy_address": proxy_address,
        "proxy_port": proxy_port,
        "proxy_username": proxy_username,
        "proxy_password": proxy_password
    }
    return proxy


def parse_proxy_positional(proxy_string):
    proxy_list = proxy_string.split(":") if proxy_string else []
    proxy_address, proxy_port, proxy_username, proxy_password, *_ = proxy_list + [None] * 4
    proxy_port = None if not proxy_port else (int(proxy_port) if proxy_port.isdigit() else None)
    return [proxy_address, proxy_port, proxy_username, proxy_password]


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
    #
    #   call event_handler
    #   mainly dealing with the cases where an event is associated with other database queries
    #
    event_handler(type, name, data)


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


def update(attributes):
    _reporter.update(attributes)


def retrieve(attributes):
    return _reporter.retrieve(attributes)


def report_success(session):
    proxy_string = session.proxy_string if hasattr(session, "proxy_string") else ""
    update({
        "systemUser": getpass.getuser(),
        "proxy": proxy_string,
        "instagramPassword": session.password,
        "loginResult": "success"
    })



QUERY_TIMEOUT = 600


def query_latest_attributes(attributes):
    begin_time = int(time.time())
    if not _reporter:
        raise Exception("reporter not ready")
    names = list(attributes.keys())
    while True:
        # check for timeout
        cur_time = int(time.time())
        if cur_time > begin_time + QUERY_TIMEOUT:
            raise Exception("query timeout")
        # retrieve new data
        res = _reporter.retrieve(names)
        if res:
            # print(attributes)
            # print(res)
            for key in attributes:
                if key not in res:
                    break
                if res[key] != attributes[key]:
                    return res
        time.sleep(1)


ip_address_check_url = "https://api.ipify.org/"
instagram_test_url = "https://www.instagram.com/web/search/topsearch/?query=kimkardashian"


def test_connection(browser):
    try:
        fetch_ip = None
        fetch_instagram_data = None
        web_address_navigator(browser, ip_address_check_url)
        fetch_ip = browser.find_element_by_tag_name("pre").text
        if fetch_ip:
            web_address_navigator(browser, instagram_test_url)
            fetch_instagram_data = browser.page_source
        return {
            "ip": fetch_ip,
            "instagramResponse": fetch_instagram_data
        }
    except Exception as e:
        raise e


proxy_add_client_url = SERVER + "/admin/proxy/{string}/clients"
proxy_add_blacklist_url = SERVER + "/admin/proxy/{string}/fails"


def event_handler(type, name, data):
    headers = {'content-type': 'application/json'}
    if type == "SELENIUM" and name == "CONNECTION-VERIFIED":
        if data["proxy"]:
            url = proxy_add_client_url.replace("{string}", data["proxy"])
            data = {
                "id": _reporter.id,
                "time": int(time.time())
            }
            requests.post(url=url, data=_json.dumps(data), headers=headers)
    elif type == "SELENIUM" and name == "CONNECTION-INVALID":
        if data["proxy"]:
            url = proxy_add_blacklist_url.replace("{string}", data["proxy"])
            data = {
                "id": _reporter.id,
                "time": int(time.time())
            }
            requests.post(url=url, data=_json.dumps(data), headers=headers)
    else:
        pass


def get_follower_num(session):
    """Prints and logs the current number of followers to
    a seperate file"""
    if not session:
        return None

    user_link = "https://www.instagram.com/{}".format(session.username)

    try:
        session.browser.get(user_link)
        followed_by = session.browser.execute_script(
            "return window._sharedData.""entry_data.ProfilePage[0]."
            "graphql.user.edge_followed_by.count")
        return followed_by

    except Exception as e:  # handle the possible `entry_data` error
        error("browser", "exception", str(e))
        return None


last_track_time = 0


def track_follower_count(session, gap=DEFAULT_FOLLOWER_TRACKING_GAP):
    if not session:
        return None

    global last_track_time
    current_time = int(time.time())
    if current_time > last_track_time + gap:
        last_track_time = current_time
        followers = get_follower_num(session)
        data("followers", followers)
        return followers


#
#
#
#
#
#
#
#
#
#
#
#
#
#
################################
#   an useful tool for processing arguments
#   ***** obsoleted 2019/03/26 05:23, use argparse instead
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
        # self.read_arguments(sys.argv)

    @staticmethod
    def remove_none(arguments):
        delete = [key for key in arguments if arguments[key] is None]
        for key in delete:
            del arguments[key]

    def read_arguments(self, argv):
        argc = len(argv)
        if argc > 1:
            self.username = argv[1]
        if argc > 2:
            self.password = argv[2]
        if argc > 3:
            self.proxy_string = argv[3]
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
            self.instance = argv[4]
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
#
#
#
#
#
#
#
#
#
#
