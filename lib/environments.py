import sys
import logging
import getpass
import requests
import time
import argparse
import json as _json
from instapy.util import web_address_navigator
import os
# import pickle
import subprocess
from dotenv import load_dotenv, find_dotenv

# reporter, arguments and patches
from . import reporter
from . import patch
from . import patch2
from . import pull
from . import tasks

#
#
#
#
#   this file:
#   (1) patches original InstaPy
#   (2) parses arguments, set-up reporter and other environments
#   (3) provides easy to use interfaces for InstaGrow
#
#
#
ENVIRONMENT_VERSION = "0.23"

load_dotenv(find_dotenv())
SERVER = os.getenv("SERVER") if os.getenv("SERVER") else "https://admin.socialgrow.live"
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

# declaim a global reporter
_login_success = False
_args = {}
_arguments = {}
_reporter = None
_reporter_fields = {}
_session = None
_tasks_dict = None
_pulled_cookies = None
# declaim a global logger
logger = logging.getLogger()


#
#   below is a group of functions as
#   interfaces for accessing global variables in the environments
#
def arguments():
    global _arguments
    return _arguments


def args():
    global _args
    return _args


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
    return reporter.StreamHub.stderr


def set_session(session):
    global _session
    _session = session


def get_session():
    return _session


def print_script_info():
    # print information
    get_stdout().write("version: " + _args.version + "\n")
    get_stdout().write("browser: " + ("chrome" if _args.chrome else "firefox") + "\n")
    get_stdout().write("GUI Mode: " + ("gui" if _args.gui else "headless") + "\n")
    get_stdout().write("\n")


#
#
#
#
#   this function wraps all the dirty works
#   it sets-up the whole environment
#
#
#
#
def config(**kw):
    global _reporter_fields

    # call initiate function
    init_environment(**kw)

    # checkin reporter
    checkin()

    # apply patches to instapy
    patch.apply()
    patch2.apply()

    print_script_info()


#
#
#
#   initialize the big environment
#   (1) parse and process arguments
#   (2) config StreamHub and Reporter
#
#
def init_environment(**kw):
    # process arguments and config related environment
    global _args
    global _reporter_fields
    global _reporter

    # process arguments
    process_arguments(**kw)

    # redirect streams to StreamHub
    stream = reporter.StreamHub()
    sys.stderr = stream
    stream1 = reporter.StreamHub()
    sys.stdout = stream1

    # setup reporter for StreamHub
    _reporter = reporter.Reporter()
    stream.set_reporter(_reporter)
    stream.begin_report(True)

    if not _args.silent:
        stream.begin_print(True)
        stream1.begin_print(True)

    # config reporter fields
    _reporter_fields.update({
        "environmentVersion": ENVIRONMENT_VERSION,
        "status": "active",
        "instagramUser": _args.username,
        "instagramPassword": _args.password,
        "systemUser": getpass.getuser(),
        # "instance": _args.instance,
        # "proxy": _args.proxy,
    })

    # also put all commandline arguments into report fields
    # so _reporter_fields includes:
    #   (1) all commandline arguments, including these adjusted by "--pull" and "env.config"
    #   (2) 4 additional attributes defined above
    #
    _reporter_fields.update(_args.__dict__)
    remove_none(_reporter_fields)


def process_arguments(**kw):
    global _args
    parser = argparse.ArgumentParser()
    parser.add_argument("username", nargs='?', type=str)
    parser.add_argument("password", nargs='?', type=str)
    parser.add_argument("proxy", nargs='?', type=str)
    parser.add_argument("-c", "--chrome", action="store_true")
    parser.add_argument("-g", "--gui", action="store_true")
    parser.add_argument("-i", "--instance", type=str)
    parser.add_argument("-v", "--version", type=str)
    parser.add_argument("-n", "--name", type=str)
    parser.add_argument("-t", "--tasks", nargs="+", type=str)
    parser.add_argument("-p", "--pull", nargs="*", type=str)
    parser.add_argument("-pe", "--pull-exclude", nargs="*", type=str)
    parser.add_argument("-pb", "--pull-by", nargs="+", type=str)
    parser.add_argument("-q", "--query", action="store_true")
    parser.add_argument("-rp", "--retry-proxy", action="store_true")
    parser.add_argument("-ap", "--allocate-proxy", action="store_true")
    parser.add_argument("-s", "--silent", action="store_true")
    _args = parser.parse_args()

    # merge named parameters **kw into command line arguments
    for key in kw:
        if not hasattr(_args, key) or getattr(_args, key) is None:
            setattr(_args, key, kw[key])

    # see if arguments says to pull user credentials from server,
    # do it right now
    # pulled data will be merged into command line arguments
    if _args.pull is not None or _args.pull_exclude is not None:
        # adjust the fields to pull
        if not _args.pull:
            _args.pull = ['password', 'proxy', 'tasks', 'cookies']
        if _args.pull_exclude:
            for exclude in _args.pull_exclude:
                if exclude in _args.pull:
                    _args.pull.remove(exclude)
        # pull these fields from sources defined by '--pull-by'
        pull.userdata(_args.username, _args.pull, _args.pull_by, _args.__dict__)

    # set a temporary username if it's currently absent
    if not _args.username:
        _args.username = "unknown-user-tba"

    # setup arguments for __init__ InstaPy
    global _arguments
    _arguments = {
        "username": _args.username,
        "password": _args.password,
        "bypass_suspicious_attempt": True,
        "headless_browser": True if not _args.gui else False,
        "use_firefox": True if not _args.chrome else False,
    }
    proxy = parse_proxy_keyword(_args.proxy)
    _arguments.update(proxy)
    remove_none(_arguments)
    # print(_args)
    # print(_arguments)


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


#
#
#
#   wrapped interfaces for logging
#   basically two types:
#   (1) logging string buffers which going into "messages" account by default
#   (2) logging json objects which going into "json" account by default
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


def log(buffer, title="LOG  ", account="messages"):
    buffer = "%s[%d] %s" % ((title + " " if title else ""), int(time.time()), buffer)
    # reporter.StreamHub.stdout.write(buffer + "\n")
    sys.stdout.write(buffer + "\n")
    if _reporter:
        _reporter.send(buffer, account)


def info(buffer):
    log(buffer, title="INFO ")


def json(obj, account="json"):
    sys.stdout.write(account + ": " + _json.dumps(obj) + "\n")
    if _reporter:
        _reporter.json(obj, account)


def data(name, value):
    json({
        "time": int(time.time()),
        "key": name,
        "value": value
    }, "data")


def event(type, name, data={}):
    sys.stdout.write("EVENT [%d] %s %s\n" % (int(time.time()), type + "-" + name, _json.dumps(data)))
    obj = {
        "time": int(time.time()),
        "type": type,
        "name": name,
        "data": data
    }
    if _reporter:
        _reporter.json(obj, "events")
    #
    #   call event_handler
    #   mainly dealing with the cases where an event is associated with other database queries
    #
    event_handler(type, name, data)


def error(type, name, data={}):
    sys.stdout.write("ERROR [%d] %s %s\n" % (int(time.time()), type + "-" + name, _json.dumps(data)))
    obj = {
        "time": int(time.time()),
        "type": type,
        "name": name,
        "data": data
    }
    if _reporter:
        _reporter.json(obj, "errors")


def update(attributes):
    if _reporter:
        _reporter.update(attributes)


def retrieve(attributes):
    if not _reporter:
        return None
    return _reporter.retrieve(attributes)


def retrieve_latest(attributes):
    return query_latest_attributes(attributes)


QUERY_TIMEOUT = 600


def query_latest_attributes(attributes):
    if not _reporter:
        return None
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


def report_success(session):
    set_session(session)
    upload_cookies(session)

    global _login_success
    _login_success = True
    proxy_string = session.proxy_string if hasattr(session, "proxy_string") else ""

    # update these attributes that may changed during selenium initialization or login
    update_attributes = {
        "proxy": proxy_string,
        "username": session.username,
        "password": session.password,
        "instagramUser": session.username,
        "instagramPassword": session.password,
    }
    if session.password:
        update_attributes["loginResult"] = "success"
    else:
        update_attributes["loginResult"] = "success-with-cookie"

    update(update_attributes)


def upload_cookies(session):
    # username = session.username
    # logfolder = "~/InstaPy/logs/" + username + "/"
    # cookies = pickle.load(open('{0}{1}_cookie.pkl'.format(logfolder, username), 'rb'))
    _reporter.update({"cookies": session.browser.get_cookies()})


#
#
#
#   local event handlers for all logging entries going into 'EVENT'
#
#
#
proxy_add_client_url = SERVER + "/admin/proxy/{string}/clients"
proxy_delete_client_url = SERVER + "/admin/proxy/{string}/clients/{client_id}"
proxy_add_blacklist_url = SERVER + "/admin/proxy/{string}/fails"


def event_handler(type, name, data):
    headers = {'content-type': 'application/json'}

    if type == "SELENIUM" and name == "CONNECTION-VERIFIED":
        if data["proxy"]:
            url = proxy_add_client_url.replace("{string}", data["proxy"])
            postdata = {
                "id": _reporter.id,
                "time": int(time.time())
            }
            try:
                requests.post(url=url, data=_json.dumps(postdata), headers=headers)
            except Exception:
                pass
            # update sessionIP in reporter
            update({"sessionIP": data["sessionIP"]})

    elif type == "SELENIUM" and name == "CONNECTION-INVALID":
        if data["proxy"]:
            url = proxy_add_blacklist_url.replace("{string}", data["proxy"])
            data = {
                "id": _reporter.id,
                "time": int(time.time())
            }
            try:
                requests.post(url=url, data=_json.dumps(data), headers=headers)
            except Exception:
                pass

    elif type == "SESSION" and name == "SCRIPT-QUITTING":
        if data["proxy"]:
            url = proxy_delete_client_url.replace("{string}", data["proxy"]).replace("{client_id}", _reporter.id)
            try:
                requests.delete(url=url)
            except Exception:
                pass

    else:
        pass


#
#
#
#   convenient wrapped task interfaces
#
#
#
def load_tasks(tasks_list):
    global _tasks_dict
    try:
        _tasks_dict = tasks.load_all_task_by_names(tasks_list, task_queued, task_executing, task_finished)
        action_queue = tasks.ActionQueue()
        add_tasks_to_queue_from_dict(action_queue, _tasks_dict)
        return action_queue
    except Exception as e:
        sys.stdout.write(str(e) + "\n")
        return None


def add_tasks_to_queue_from_dict(action_queue, task_dict):
    for key in task_dict:
        action_queue.add_from_task(task_dict[key])


set_task_status_url = SERVER + "/admin/script/{id}/tasks"
fetch_task_url = SERVER + "/admin/script/{id}/tasks"


def set_task_status(task_id, status):
    headers = {'content-type': 'application/json'}
    data = {
        "taskID": task_id,
        "status": status
    }
    url = set_task_status_url.replace("{id}", _reporter.id)
    try:
        requests.put(url=url, data=_json.dumps(data), headers=headers)
    except Exception:
        pass


def get_tasks():
    url = fetch_task_url.replace("{id}", _reporter.id)
    try:
        return requests.get(url=url).json()
    except Exception:
        return {}


def _fetch_tasks():
    all_tasks = get_tasks()
    # filter old tasks
    new_tasks = {}
    for key in all_tasks:
        task = all_tasks[key]
        if not task["status"] or task["status"] == "PENDING":
            new_tasks[key] = task
    if len(new_tasks) > 0:
        log("got %d new tasks from server" % len(new_tasks), title="TASK")
    return new_tasks


def fetch_tasks(action_queue):
    new_tasks = _fetch_tasks()
    for key in new_tasks:
        task_definition = new_tasks[key]
        task = tasks.load_task_by_definition(task_definition, task_queued, task_executing, task_finished)
        try:
            action_queue.add_from_task(task)
        except Exception as e:
            error("TASK", "INVALID-TASKS", task.name if task else "unknown-task")


def fetch_task_and_execute():
    action_queue = tasks.ActionQueue()
    fetch_tasks(action_queue)
    while not action_queue.empty():
        action = action_queue.get()
        action.execute()


def task_queued(task):
    # event("TASK", "QUEUED", {"time": int(time.time()), "id": task.id, "title": task.title})
    set_task_status(task.id, "QUEUED")


def task_executing(task, type, target):
    # event("TASK", "EXECUTING", {"time": int(time.time()), "id": task.id, "title": task.title})
    set_task_status(task.id, "EXECUTING")


def task_finished(task):
    # event("TASK", "FINISHED", {"time": int(time.time()), "id": task.id, "title": task.title})
    set_task_status(task.id, "FINISHED")


#
#
#
#   other miscellaneous functions
#
#
#
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

report_follower_count_url = SERVER + "/admin/report-follower-count/{username}/{time}/{count}"


def report_follower_count(session, count):
    # data("followers", count)
    username = session.username
    current = str(int(time.time()))
    count = str(count)
    url = report_follower_count_url.replace("{username}", username).replace("{time}", current).replace("{count}", count)
    try:
        requests.get(url=url)
    except Exception as e:
        error("DATA ", "report-follower-count-exception", str(e))


def track_follower_count(session, gap=DEFAULT_FOLLOWER_TRACKING_GAP):
    if not session:
        return None

    global last_track_time
    current_time = int(time.time())
    if current_time > last_track_time + gap:
        last_track_time = current_time
        followers = get_follower_num(session)
        report_follower_count(session, followers)
        return followers


def self_restart(session, arguments):
    event("SESSION", "SCRIPT-QUITTING", {"proxy": session.proxy_string})
    python = sys.executable
    if not arguments:
        arguments = sys.argv
    os.execl(python, python, *arguments)


def self_update():
    process = subprocess.Popen(["git", "pull"], stderr=subprocess.PIPE)
    output = process.stderr.read()
    log("output from terminal:\n" + str(output, "utf-8"), title="GIT  ")
    event("SCRIPT", "SELF-UPDATED")


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
