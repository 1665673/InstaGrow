import sys
import logging
import getpass
import requests
import datetime
import time
# import argparse
import json as _json
from instapy.util import web_address_navigator
import os
import psutil
import signal
import re
# import pickle
import subprocess
from dotenv import load_dotenv, find_dotenv

# reporter, arguments and patches
from . import reporter
from . import patch
from . import patch2
from . import pull
from . import tasks
from .arguments import get_argparser, amend_arguments

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
ENVIRONMENT_VERSION = "0.29"

load_dotenv(find_dotenv())
SERVER = os.getenv("SERVER") if os.getenv("SERVER") else "https://admin.socialgrow.live"
CHECKIN_URL = SERVER + "/admin/check-in"
CHECKOUT_URL = SERVER + "/admin/check-out/{}"
REPORT_BLOCK_URL = SERVER + "/admin/report-instagram-block"
GET_UPDATE_WARM_UP_URL = SERVER + "/admin/get-update-warm-up/{0}/{1}/{2}"
DEFAULT_FOLLOWER_TRACKING_GAP = 1800
QUERY_LATEST_TIMEOUT = 900
# MACROS
# DEFAULT_REPORT_FIELDS = {
#     "instagramUser": "N/A",
#     "systemUser": "N/A",
#     "version": "N/A",
#     "instance": "N/A",
#     "proxy": "N/A"
# }

# global variables
_start_time = time.time()
_stream_for_stdout = None
_stream_for_stderr = None
_reporter = None
_reporter_fields = {}
_login_success = False
_argparser = None
_args = {}
_arguments = {}
_session = None
_proxy_in_use = None
_tasks_dict = None
_pulled_cookies = None
_cookies_loaded = False
_action_statistics = {}
_warm_up = None
_tasks_loaded = []
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
    #
    # see if we do regular checkin, or merge with last record
    #
    if _args.disable_reporter:
        print("[reporter disabled]")
        return
    if _args.merge is None:
        _reporter.checkin(CHECKIN_URL, _reporter_fields)
    else:
        if _args.merge == "":
            _reporter.checkin(CHECKIN_URL, {"instagramUser": _reporter_fields["instagramUser"]})
        else:
            _reporter.checkin(CHECKIN_URL, {"instance": _args.merge})
        _reporter.update(_reporter_fields)


def checkout():
    global _reporter
    id = _reporter.id
    if id:
        try:
            url = CHECKOUT_URL.format(id)
            requests.get(url)
        except Exception as e:
            error("REPORTER", "EXCEPTION", str(e))


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
    print("version: " + _args.version)
    print("browser: " + ("chrome" if _args.chrome else "firefox"))
    print("GUI Mode: " + ("gui" if _args.gui else "headless"))
    print()


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
    global _stream_for_stdout
    global _stream_for_stderr
    global _reporter_fields
    global _reporter
    global _warm_up

    # exit handlers
    terminate_signals = [signal.SIGINT, signal.SIGTERM, signal.SIGKILL]
    for sig in terminate_signals:
        try:
            signal.signal(sig, exit_gracefully_worker)
        except:
            pass

    # redirect streams to StreamHub
    _stream_for_stdout = reporter.StreamHub()
    _stream_for_stderr = reporter.StreamHub()
    sys.stdout = _stream_for_stdout
    sys.stderr = _stream_for_stderr

    # init reporter for the stderr StreamHub
    _reporter = reporter.Reporter()
    _stream_for_stderr.set_reporter(_reporter)
    _stream_for_stderr.begin_report(True)
    _stream_for_stdout.begin_print(True)
    _stream_for_stderr.begin_print(True)

    # process arguments
    process_arguments(**kw)

    # with arguments parsed, no we can further config reporter
    _reporter_fields.update({
        "environmentVersion": ENVIRONMENT_VERSION,
        "arguments": sys.argv,
        "instagramUser": _args.username,
        "instagramPassword": _args.password,
        "systemUser": getpass.getuser(),
        "proxy": _args.proxy,
        "tasks": _args.tasks,
        "remoteTasks": _args.remote_tasks,
        "customerTasks": _args.customer_tasks,
        "tag": _args.tag,
        "owner": _args.owner,
        "version": _args.version,
        "instance": _args.instance,
        # "type": _args.type,
        "name": _args.name
        #
    })

    # print(_reporter_fields)

    # also put all commandline arguments into report fields
    # so _reporter_fields includes:
    #   (1) all commandline arguments, including these adjusted by "--pull" and "env.config"
    #   (2) 4 additional attributes defined above
    #
    # _reporter_fields.update(_args.__dict__)
    remove_none(_reporter_fields)

    # set up warm-up
    if _args.warm_up:
        _warm_up = get_warm_up_timestamp(_args.username, _args.warm_up)


def process_arguments(**kw):
    global _argparser
    global _args
    global _stream_for_stdout
    global _stream_for_stderr
    parser = get_argparser()
    _argparser = parser
    _args = parser.parse_args()

    # first thing first, if arguments says silent
    # then disable terminal streams immediately
    if _args.silent:
        _stream_for_stdout.begin_print(False)
        _stream_for_stderr.begin_print(False)

    # # see if this is a worker thread...
    # # by default, it's a daemon
    # if not _args.worker:
    #     log("script [daemon] started, pid: {}\n\n".format(os.getpid()))
    #     create_worker()
    #
    #     def _exit_handler(*av, **kw):
    #         log("script [daemon] ended, pid: {}\n\n".format(os.getpid()))
    #         exit(0)
    #
    #     signal.signal(signal.SIGINT, _exit_handler)
    #     while True:
    #         time.sleep(10)
    # else:
    #     log("script [worker] started, pid: {}\n\n".format(os.getpid()))

    # process argument allocate-proxy
    if _args.allocate_proxy is not None:
        # add two default values to make sure it has 2 sub arguments
        _args.allocate_proxy += ["all", "all"]

        # preprocess some arguments of equivalents
    if _args.username1:
        _args.username = _args.username1
    if _args.password1:
        _args.password = _args.password1
    if _args.proxy1:
        _args.proxy = _args.proxy1

    # merge named parameters **kw into command line arguments
    # if "version" not in kw:
    #     kw["version"] = "unknown-version"
    # if "type" not in kw:
    #     kw["type"] = "unknown-type"
    for key in kw:
        if not hasattr(_args, key) or getattr(_args, key) is None:
            setattr(_args, key, kw[key])

    # process short-cut for combo arguments
    if _args.pull_cookies:
        _args.pull = ["cookies"]
    if _args.gui_chrome_disable_image:
        _args.gui = True
        _args.chrome = True
        _args.disable_image = True

    # see if arguments says to pull user credentials from server,
    # do it right now
    # pulled data will be merged into command line arguments
    if _args.pull is not None or _args.pull_exclude is not None:
        # adjust the fields to pull
        if not _args.pull:
            _args.pull = ['password', 'proxy', 'tag', 'tasks', 'remote-tasks', 'customer-tasks', 'cookies']
        if _args.pull_exclude:
            for exclude in _args.pull_exclude:
                if exclude in _args.pull:
                    _args.pull.remove(exclude)
        # pull these fields from sources defined by '--pull-by'
        pull.userdata(_args.username, _args.pull, _args.pull_by, _args.__dict__)

    # set a temporary username if it's currently absent
    # if not _args.username:
    #     _args.username = "unknown-user"

    # process tasks
    if _args.tasks == None:
        _args.tasks = []
    if _args.remote_tasks == None:
        _args.remote_tasks = []
    if _args.customer_tasks == None:
        _args.customer_tasks = []

    # see if warm-up option is present
    # make sure that it always has 2 components if present
    if type(_args.warm_up) is list:
        _args.warm_up = (_args.warm_up + [None] * 2)[0:2]
        try:
            _args.warm_up[0] = float(_args.warm_up[0])
        except:
            _args.warm_up[0] = 3.0
        try:
            _args.warm_up[1] = float(_args.warm_up[1])
        except:
            _args.warm_up[1] = 2.0

    # setup arguments for __init__ InstaPy
    global _arguments
    _arguments = {
        "username": _args.username if _args.username is not None else "unknown-user",
        "password": _args.password if _args.password is not None else "",
        "bypass_suspicious_attempt": True,
        "headless_browser": True if not _args.gui else False,
        "use_firefox": True if not _args.chrome else False,
        "disable_image_load": True if _args.disable_image else False,
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
    #
    #   also report current memory usage at the same time
    #
    # rss = get_memory_usage()
    # report
    try:
        # _reporter.payload["attributes"]["rss"] = rss
        _reporter.send(buffer, account)
    except Exception as e:
        sys.stdout.write("error in reporter: " + str(e))


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
        if cur_time > begin_time + QUERY_LATEST_TIMEOUT:
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


query_latest_attributes_by_list_url = SERVER + "/admin/retrieve-status/latest-attributes"


def query_latest_attributes1(attributes):
    if not _reporter or not _reporter.id:
        return None
    # build up a query
    id = _reporter.id
    headers = {'content-type': 'application/json'}
    url = query_latest_attributes_by_list_url
    data = {
        "id": id,
        "attributes": attributes
    }

    # keep querying until we get what we care about
    while True:
        try:
            res = requests.post(url=url, data=_json.dumps(data), headers=headers).json()
            if res != {}:
                return res
        except:
            pass
        finally:
            time.sleep(1)


def report_success(session):
    # set_session(session) # moved to InstaPy.set_selenium_local_session_patch
    # upload_cookies(session)

    global _login_success
    _login_success = True
    proxy_string = session.proxy_string if hasattr(session, "proxy_string") else ""

    # update these attributes that may changed during selenium initialization or login
    update_attributes = {
        "proxy": proxy_string,
        # "username": session.username,
        # "password": session.password,
        "instagramUser": session.username,
        "instagramPassword": session.password,
        "cookies": session.browser.get_cookies()
    }

    if session.password:
        update_attributes["loginResult"] = "success"
    else:
        update_attributes["loginResult"] = "success-with-cookie"

    try:
        update(update_attributes)
    except Exception as e:
        error("report-success", "exception", str(e))

    update_script_status_to_instagram_data()
    info("[report_success] login success status synchronized with main server")


def update_script_status_to_instagram_data():
    global _session
    try:
        url = SERVER + "/admin/script/pull"
        headers = {'content-type': 'application/json'}
        data = {
            "instagramUser": _session.username,
            "instagramPassword": _session.password,
            "proxy": _session.proxy_string if hasattr(_session, "proxy_string") else "",
            "tag": _args.tag,
            "tasks": _args.tasks,
            "remoteTasks": _args.remote_tasks,
            "customerTasks": _args.customer_tasks,
            "cookies": _session.browser.get_cookies(),
            "commandLineArguments": sys.argv,
            "processedArguments": vars(_args)
        }
        requests.post(url=url, data=_json.dumps(data), headers=headers)
    except Exception as e:
        error("UPDATE-INSTAGRAM-DATA", "EXCEPTION", str(e))


def get_memory_usage():
    rss = 0
    try:
        parent = psutil.Process()
        rss = parent.memory_info().rss
        # try get memory usage of sub-processes
        children = parent.children(recursive=True)
        for child in children:
            try:
                rss1 = child.memory_info().rss
                if rss1:
                    rss += rss1
            except:
                pass
    except Exception as e:
        sys.stdout.write(str(e))
    return rss
    #
    # pid of geckodriver
    # _session.browser.service.process.pid
    #


def send_get_request_to_server(url):
    try:
        return requests.get(url).json()
    except:
        return {}


def send_post_request_to_server(url, _data):
    try:
        headers = {'content-type': 'application/json'}
        return requests.post(url=url, data=_json.dumps(_data), headers=headers).json()
    except Exception as e:
        sys.stdout.write(str(e))
        return {}


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
        # report sessionIP
        update({"sessionIP": data["sessionIP"]})
        # report proxy client, if applicable
        if data["proxy"]:
            global _proxy_in_use
            _proxy_in_use = data["proxy"]
            url = proxy_add_client_url.replace("{string}", data["proxy"])
            postdata = {
                "id": _reporter.id,
                # "instagramUser": _session.username,
                "arguments": sys.argv,
                "time": int(time.time())
            }
            try:
                requests.post(url=url, data=_json.dumps(postdata), headers=headers)
            except Exception:
                pass


    elif type == "SELENIUM" and name == "CONNECTION-INVALID":
        # report proxy fail, if applicable
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


    elif type == "SELENIUM" and name == "SESSION-QUITTING":
        # report release of proxy, if applicable
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
set_task_status_url = SERVER + "/admin/script/{id}/tasks"
fetch_task_url = SERVER + "/admin/script/{id}/tasks"
fetch_remote_tasks_url = SERVER + "/admin/tasks/fetch/general/{list}"
fetch_customer_tasks_url = SERVER + "/admin/tasks/fetch/customer/{instagram}/{list}"


def get_loaded_task_names():
    return _tasks_loaded


def init_action_queue():
    return tasks.ActionQueue()


def load_local_tasks(action_queue, tasks_list):
    global _tasks_dict
    try:
        _tasks_dict = tasks.load_all_task_by_names(tasks_list, task_queued, task_executing, task_finished, _warm_up)
        add_tasks_to_queue_from_dict(action_queue, _tasks_dict)
    except Exception as e:
        sys.stdout.write(str(e) + "\n")
    global _tasks_loaded
    _tasks_loaded += tasks_list


def load_remote_tasks(action_queue, task_list):
    if not action_queue or not task_list:
        return
    tasks_dict = fetch_remote_tasks(task_list)
    load_tasks_by_definitions(action_queue, tasks_dict)
    global _tasks_loaded
    for key in tasks_dict:
        _tasks_loaded.append(key)


def load_customer_tasks(action_queue, instagram, task_list):
    if not action_queue or not instagram or not task_list:
        return
    tasks_dict = fetch_customer_tasks(instagram, task_list)
    load_tasks_by_definitions(action_queue, tasks_dict)
    global _tasks_loaded
    for key in tasks_dict:
        _tasks_loaded.append(key)


def add_tasks_to_queue_from_dict(action_queue, task_dict):
    for key in task_dict:
        action_queue.add_from_task(task_dict[key])


def set_task_status(task_id, status):
    headers = {'content-type': 'application/json'}
    data = {
        "taskID": task_id,
        "status": status
    }

    try:
        url = set_task_status_url.replace("{id}", _reporter.id)
        requests.put(url=url, data=_json.dumps(data), headers=headers)
    except Exception:
        pass


def retrieve_tasks_from_server():
    try:
        url = fetch_task_url.replace("{id}", _reporter.id)
        return requests.get(url=url).json()
    except Exception:
        return {}


def retrieve_new_tasks_from_server():
    all_tasks = retrieve_tasks_from_server()
    # filter old tasks
    new_tasks = {}
    for key in all_tasks:
        task = all_tasks[key]
        if not task["status"] or task["status"] == "PENDING":
            new_tasks[key] = task
    if len(new_tasks) > 0:
        log("got %d new tasks from server" % len(new_tasks), title="TASK")
    return new_tasks


def load_tasks_by_definitions(action_queue, tasks_dict):
    for key in tasks_dict:
        task_definition = tasks_dict[key]
        task = tasks.load_task_by_definition(task_definition, task_queued, task_executing, task_finished, _warm_up)
        try:
            action_queue.add_from_task(task)
        except Exception as e:
            error("TASK", "INVALID-TASKS", task.name if task else "unknown-task")


def fetch_tasks(action_queue):
    new_tasks = retrieve_new_tasks_from_server()
    load_tasks_by_definitions(action_queue, new_tasks)


def fetch_remote_tasks(task_list):
    task_list = ",".join(task_list)
    url = fetch_remote_tasks_url.replace("{list}", task_list)
    tasks = {}
    try:
        if task_list:
            tasks = requests.get(url).json()
    except:
        pass
    return tasks


def fetch_customer_tasks(instagram, task_list):
    task_list = ",".join(task_list)
    url = fetch_customer_tasks_url.replace("{instagram}", instagram).replace("{list}", task_list)
    tasks = {}
    try:
        if task_list:
            tasks = requests.get(url).json()
    except:
        pass
    return tasks


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


update_statistics_url = SERVER + "/admin/update-action-statistics"


def do_statistics(action, target, success):
    if action is None or success is None:
        return
    global _action_statistics
    statistics = _action_statistics
    if action not in statistics:
        statistics[action] = {
            "success": 0,
            "fail": 0
        }

    # add this action into statistics
    success = bool(success)
    if success:
        statistics[action]["success"] += 1
    else:
        statistics[action]["fail"] += 1

    # mark this action the last executed action
    lastAction = {
        "name": action,
        "target": target,
        "success": success
    }

    # update statistics to server
    stat_data = {
        "logID": _reporter.id if _reporter else None,
        "proxyString": _proxy_in_use,
        "statistics": statistics,
        "lastAction": lastAction
    }

    if _reporter and _reporter.id:
        send_post_request_to_server(update_statistics_url, stat_data)


#
#
#
#   other miscellaneous functions
#
#
#
ip_address_check_url = "https://api.ipify.org/"
instagram_test_url = "https://www.instagram.com/web/search/topsearch/?query=kimkardashian"


# instagram_test_url = "https://www.instagram.com/accounts/login/"

# use this link to test connection. It's a BAD link. I use it intentionally because a bad link has a shorter response
# instagram_test_url = "https://www.instagram.com/accounts"


def upload_cookies(session):
    # username = session.username
    # logfolder = "~/InstaPy/logs/" + username + "/"
    # cookies = pickle.load(open('{0}{1}_cookie.pkl'.format(logfolder, username), 'rb'))
    _reporter.update({"cookies": session.browser.get_cookies()})


def load_local_cookies(username):
    return {}


def fetch_connection_ip(browser):
    try:
        # trust proxy string if a proxy is provided
        proxy_str = _session.proxy_string
        return re.search(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", proxy_str).group(0)
    except:
        # fetch current ip from third-party website
        web_address_navigator(browser, ip_address_check_url)
        return browser.find_element_by_tag_name("pre").text


def test_connection(browser):
    try:
        fetch_ip = fetch_connection_ip(browser)
        fetch_instagram_data = None

        if fetch_ip:
            web_address_navigator(browser, instagram_test_url)
            fetch_instagram_data = browser.page_source
        return {
            "ip": fetch_ip,
            "instagramResponse": fetch_instagram_data
        }
    except Exception as e:
        raise e


followers_count_url = "https://www.instagram.com/web/search/topsearch/?query={}"


def get_follower_num(session):
    """Prints and logs the current number of followers to
    a seperate file"""
    # if not session:
    #     return None
    #
    # user_link = "https://www.instagram.com/{}".format(session.username)
    #
    # try:
    #     session.browser.get(user_link)
    #     followed_by = session.browser.execute_script(
    #         "return window._sharedData.""entry_data.ProfilePage[0]."
    #         "graphql.user.edge_followed_by.count")
    #     return followed_by
    #
    # except Exception as e:  # handle the possible `entry_data` error
    #     error("browser", "exception", str(e))
    #     return None

    try:
        url = followers_count_url.format(session.username)
        data = requests.get(url=url).json()
        users = data["users"]
        for user in users:
            if user["user"]["username"] == session.username:
                # print(user["user"]["follower_count"])
                return user["user"]["follower_count"]
    except:
        return None
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


def kill_all_child_processes():
    log("closing browser...")
    # parent = psutil.Process()
    # for child in parent.children(recursive=True):  # or parent.children() for recursive=False
    #     child.kill()
    # parent.kill()
    try:
        _session.browser.quit()
    except:
        pass


# as signal handlers
def exit_gracefully_worker(sig, frame):
    event("SELENIUM", "SESSION-QUITTING", {"proxy": _proxy_in_use, "signal": sig})
    event("SCRIPT", "QUITTING", {"signal": sig})
    checkout()
    kill_all_child_processes()
    psutil.Process().kill()


# as an action in Task module
def safe_quit(session, message=""):
    #
    # clean-up handlers had been set,  @ InstaPy.end(), which was also patched,
    # so, everything's been taken care of,
    # just need to exit regularly
    #
    #
    # exit(0)
    # os.kill(os.getpid(), 3)

    # clean-up everything
    event("SELENIUM", "SESSION-QUITTING", {"proxy": session.proxy_string, "message": message})
    event("SCRIPT", "QUITTING", {"message": message})
    kill_all_child_processes()
    psutil.Process().kill()
    # exit(0)


# def _quit_clean_up():
#     # check-out proxy
#     event("SESSION", "SCRIPT-QUITTING", {"proxy": _proxy_in_use})

#
#  subprocess creator for the daemon-worker schema
#
def create_worker(argv=[]):
    if not argv:
        argv = sys.argv
    argv = argv.copy()
    if "-w" not in argv:
        argv += ["-w"]
    subprocess.Popen(['python3'] + argv)


#
#  subprocess creater for substituting-main-process schema
#
def substitute_process(argv=None):
    event("SCRIPT", "STARTING", {"arguments": argv})
    python = sys.executable
    os.execl(python, python, *argv)
    # subprocess.Popen(['nohup', 'python3'] + arguments)


def self_restart(argv=None, argv_amendments={}, argv_upsert=False):
    #
    #   clean up
    #
    event("SCRIPT", "SELF-RESTARTING", {"arguments": argv})
    event("SELENIUM", "SESSION-QUITTING", {"proxy": _proxy_in_use, "arguments": argv})
    kill_all_child_processes()
    #
    # # deamon-worker
    # create_worker(argv)
    # psutil.Process().kill()
    #

    # check arguments
    if not argv:
        argv = sys.argv
    else:
        # mandatory inherit the silent option
        if ("-s" in sys.argv or "--silent" in sys.argv) \
                and ("-s" not in argv and "--silent" not in argv):
            argv += ["-s"]

    # amend arguments
    argv = amend_arguments(argv, argv_amendments, argv_upsert)
    # substituting processes
    substitute_process(argv)


def self_update():
    process = subprocess.Popen(["git", "pull"], stderr=subprocess.PIPE)
    output = process.stderr.read()
    log("output from terminal:\n" + str(output, "utf-8"), title="GIT  ")
    event("SCRIPT", "SELF-UPDATED")


def get_warm_up_timestamp(username, warm_up):
    # full datetime format is 201907161133
    # till = warm_up
    #
    # if len(till) < len("201907161133"):
    #     days = int(till)
    #     url = GET_UPDATE_WARM_UP_URL
    #     # requests.post(url=url, data=json.dumps(data), headers=self.headers).json()
    # else:
    #     year, month, day, hour, minute = \
    #         int(till[0:4]), int(till[4:6]), int(till[6:8]), int(till[8:10]), int(till[10:12])
    #     till = datetime.datetime(year, month, day, hour, minute).timestamp()
    #
    # return int(till)
    url = GET_UPDATE_WARM_UP_URL.format(username, warm_up[0], warm_up[1])
    try:
        return requests.get(url).json()
    except:
        return None


def report_block(action, block_info={}):
    username = _session.username
    url = REPORT_BLOCK_URL
    request_data = {
        "instagram": username,
        "action": action,
        "information": block_info,
        "environment": summary_environment()
    }
    try:
        requests.post(url=url, headers={'content-type': 'application/json'}, data=_json.dumps(request_data))
    except Exception as e:
        error("REPORT-BLOCK", "EXCEPTION", str(e))


def summary_environment():
    return {
        "scriptId": _reporter.id,
        "proxy": _session.proxy_string if hasattr(_session, "proxy_string") else "",
        "runtime": time.time() - _start_time,
        "cookies": _session.browser.get_cookies()
    }


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
