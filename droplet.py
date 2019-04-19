import time
from http.server import HTTPServer
from http.server import BaseHTTPRequestHandler
import json
# import re
import os
import sys
# import io
import psutil
import signal
import subprocess
# import sys
import argparse
import requests
import threading
import getpass
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

DEFAULT_SERVER_ADDRESS = "0.0.0.0"
DEFAULT_SERVER_NAME = "droplet" + "-" + str(int(time.time()))
DEFAULT_SERVER_TYPE = "regular"
DEFAULT_REPORT_INTERVAL = 30
DEFAULT_STOP_COOLDOWN = 30
DEFAULT_PORT_NUMBER = 8000
DEFAULT_RESTART_DELAY = 5
REPORT_RIGHT_AFTER_CHANGE = 5
MAIN_SERVER_ADDRESS = os.getenv("SERVER") if os.getenv("SERVER") else "https://admin.socialgrow.live"
#
#   REST data interface @ main server
#
CHECK_IN_URL = MAIN_SERVER_ADDRESS + "/admin/droplets"  # POST
CHECK_OUT_URL = MAIN_SERVER_ADDRESS + "/admin/droplets/{id}"  # DEL
REPORT_STATUS_URL = MAIN_SERVER_ADDRESS + "/admin/droplets/{id}"  # PUT
RETRIEVE_STATUS_URL = MAIN_SERVER_ADDRESS + "/admin/droplets/{id}"  # GET
#
#   global variables
#
_httpd = None
_id = None
_scripts = {}
_report_timer = None


class Server(BaseHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super(BaseHTTPRequestHandler, self).__init__(*a, **kw)

    def do_HEAD(self):
        return

    def do_GET(self):
        self.respond()

    def do_POST(self):
        return

    def respond(self):
        content = self.handle_http(200, "application/json")
        self.wfile.write(content)

    def handle_http(self, status, content_type):
        self.send_response(status)
        self.send_header("Content-type", content_type)
        # allows whatever origins
        self.send_header('Access-Control-Allow-Origin', self.headers.get('Origin'))
        self.send_header('Access-Control-Allow-Credentials', 'true')
        self.send_header('Access-Control-Allow-Methods', 'GET')
        self.end_headers()
        #
        # prepare path
        #
        # parts = re.search(r"/([^/]+)(/([^/]+))?(/([^/]+))?", self.path)
        # parts = parts.groups()
        path = self.path if self.path else ""
        parts = (path.split("/") + [""] * 5)[1:]

        #
        # prepare response
        #
        message = "invalid-url"
        data = {}
        result = {
            "result": "fail",
            "message": message,
            "data": data
        }

        #
        #   handle requests
        #
        controller = parts[0]
        action = parts[1]
        instance = parts[2]
        arguments = parts[3]
        try:
            if controller == "droplet":
                if action == "status":
                    data = droplet_status()
                elif action == "report-status":
                    droplet_report_status()
                    message = "droplet status has been reported to main server"
                elif action == "update":
                    message = droplet_update()
                elif action == "restart":
                    droplet_restart_daemon()
                    message = "droplet daemon restarts in 5 seconds..."
                elif action == "update-restart":
                    droplet_update_restart()
                    message = "droplet daemon restarts in 5 seconds..."
                elif action == "restart-system":
                    droplet_restart_system()
                    message = "operating system restarts in 5 seconds"
                else:
                    raise Exception("invalid action or arguments")
            elif controller == "script":
                if action == "login" and instance:
                    script = script_login(instance)
                    message = "login started. start time: {}".format(script["start-time"])
                elif action == "start" and instance and arguments:
                    script = script_start(instance, arguments.split('+'))
                    message = "script started. start time: {}".format(script["start-time"])
                elif action == "stop" and instance:
                    script = script_stop(instance)
                    message = "script stopped. start time: {0}, stop time: {1}" \
                        .format(script["start-time"], int(time.time()))
                elif action == "restart" and instance:
                    script = script_restart(instance)
                    message = "script restarted. start time: {}".format(script["start-time"])
                elif action == "stop-all":
                    script_stop_all()
                    message = "all scripts stopped"
                elif action == "restart-all":
                    script_restart_all()
                    message = "all scripts restarted"
                else:
                    raise Exception("invalid action or arguments")
                #
                #   report to main server soon upon script changes
                #
                threading.Timer(REPORT_RIGHT_AFTER_CHANGE, _do_report_droplet_status).start()
                #
                #
                #
            else:
                raise Exception("invalid controller")

            #
            #   it indicates a success if code arrives here
            #
            result["result"] = "success"

        except Exception as e:
            message = str(e)

        result["message"] = message
        result["data"] = data
        buffer = json.dumps(result)

        return bytes(buffer, "UTF-8")


#
#
#
#
#
#
#
#   script action handlers
#   (1) run login script
#   (2) run regular script
#   (3) stop regular script
#   (4) restart regular script
#
#
#
#
#
def printt(*av, **kw):
    print(int(time.time()), *av, **kw)


def droplet_status():
    return {
        "_id": _id,
        "status": _summary_droplet_status(),
        "scripts": _summary_all_scripts()
    }


def droplet_report_status():
    _do_report_droplet_status()


def droplet_update():
    process = subprocess.Popen(["git", "pull"],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               stdin=subprocess.PIPE)
    try:
        outs, errs = process.communicate(timeout=15)
    except:
        process.kill()
        outs, errs = process.communicate()
    return outs.decode("utf-8") + errs.decode("utf-8")


def droplet_restart_daemon():
    threading.Timer(DEFAULT_RESTART_DELAY, _do_restart_droplet_daemon).start()


def droplet_update_restart():
    droplet_update()
    droplet_restart_daemon()
    # return {
    #     "dropletUpdate": droplet_update(),
    #     "dropletRestart": droplet_restart()
    # }


def droplet_restart_system():
    #
    #   shutdown droplet
    #
    raise Exception("this feature comming soon...")


def script_login(instance):
    if not instance:
        raise Exception("no-instance")
    if instance in _scripts:
        raise Exception("instance-already-exists")
    argv = ["login.py", "-q", "-ap", "-s", "-i", instance, "-g"]
    return _run_script(argv)


# arguments is a list consumed by subprocess.Popen
def script_start(instance, arguments):
    printt("[start-script] instance:", instance)
    if not instance:
        raise Exception("no-instance")
    if instance in _scripts:
        raise Exception("instance-already-exists")
    if len(arguments) < 2:
        raise Exception("not-enough-script-arguments")
    # adjust other script arguments
    if "-rc" not in arguments and "--retry-credentials" not in arguments:
        arguments += ["-rc", "off"]
    if "-s" not in arguments and "--silent" not in arguments:
        arguments += ["-s"]
    if "-i" not in arguments and "--instance" not in arguments:
        arguments += ["-i", instance]
    if "-o" not in arguments and "--owner" not in arguments:
        arguments += ["-o", _id]
    # if "-g" not in arguments and "--gui" not in arguments:
    #     arguments += ["-g"]
    return _run_script(arguments)


def script_stop(instance):
    printt("[stop-script] instance:", instance)
    if not instance or instance not in _scripts:
        raise Exception("no-instance or invalid instance")
    start_time = _scripts[instance]["start-time"]
    if start_time + DEFAULT_STOP_COOLDOWN > int(time.time()):
        raise Exception("please don't stop an instance within {0} seconds of starting. wait for another: {1} seconds"
                        .format(DEFAULT_STOP_COOLDOWN, start_time + DEFAULT_STOP_COOLDOWN - int(time.time())))
    return _stop_script_by_instance(instance)


def script_restart(instance):
    printt("[restart-script] instance:", instance)
    script = script_stop(instance)
    return script_start(instance, script["arguments"])
    # argv = ["login.py", "-s", "-q", "-ap", "-i", instance]
    # return run_script(argv, instance)


def script_stop_all():
    scripts = _summary_all_scripts()
    _stop_scripts(scripts)


def script_restart_all():
    scripts = _summary_all_scripts()
    _stop_scripts(scripts)
    _restore_scripts(scripts)


#
#
#
#
#
#
#   low-level interfaces
#   (1) communicate with main server
#   (2) start/stop scripts
#
#
#
#
#
#
def _run_script(argv):
    global _scripts
    # n = os.fork()
    # if n > 0:
    #     printt("Parent process and id is : ", os.getpid())
    # else:
    #     python = sys.executable
    #     os.execl(python, python, *argv)
    printt("[run-script]", "about to run this script:\n", str(["python3"] + argv))

    # get instance, username and tasks from arguments
    _args = _parse_script_arguments(argv[1:])  # don't include argv[0] == "run.py" while parsing
    instance = _args.instance
    username = _args.username
    tasks = _args.tasks

    try:
        process = subprocess.Popen(["python3"] + argv,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   stdin=subprocess.PIPE)

        script = {
            "arguments": argv,
            "username": username,
            "instance": instance,
            "tasks": tasks,
            "process": process,
            "start-time": int(time.time())
        }
        _scripts[instance] = script
        return script
    except Exception as e:
        printt(str(e))
        raise
    # output = process.stdout.read()
    # log("output from terminal:\n" + str(output, "utf-8"), title="GIT  ")


def _summary_droplet_status():
    return {
        # "summary": summary,
        "cpuIdle": 100 - psutil.cpu_percent(),
        "memoryUsed": psutil.virtual_memory().used,
        # virtual_memory().free means a different thing. I use total - used
        "memoryFree": psutil.virtual_memory().total - psutil.virtual_memory().used,
        "swapUsed": psutil.swap_memory().used,
        "swapFree": psutil.swap_memory().free  # it's ok to used wap_memory().free for swap
    }


def _summary_all_scripts():
    global _scripts
    # get script abstracts
    scripts = []
    try:
        for instance in _scripts:
            process = _scripts[instance]["process"]
            scripts.append({
                "instance": instance,
                "arguments": _scripts[instance]["arguments"],
                "tasks": _scripts[instance]["tasks"],
                "username": _scripts[instance]["username"],
                "startTime": _scripts[instance]["start-time"],
                "isRunning": process.poll() is None,
                "rss": psutil.Process(process.pid).memory_info().rss
            })
    except Exception as e:
        printt("error in _summary_all_scripts()" + str(e))
    return scripts


def _do_report_droplet_status():
    data = droplet_status()
    headers = {'content-type': 'application/json'}
    try:
        url = REPORT_STATUS_URL.replace("{id}", _id)
        requests.put(url=url, data=json.dumps(data), headers=headers)
    except Exception as e:
        printt("report_to_main_server(): " + str(e))


def _do_restart_droplet_daemon():
    # checkout droplet
    checkout_droplet()
    python = sys.executable
    os.execl(python, python, *sys.argv)


# def _save_and_stop_all_scripts():
#     scripts = _summary_all_scripts()
#     _save_scripts_to_main_server(scripts)
#     _stop_scripts(scripts)


def _retrieve_and_restore_all_scripts():
    scripts = _retrieve_scripts_from_server()
    _restore_scripts(scripts)


def _save_scripts_to_main_server(scripts):
    # just do one more reporting
    # script info is included in reporting
    droplet_report_status()


def _retrieve_scripts_from_server():
    try:
        url = RETRIEVE_STATUS_URL.replace("{id}", _id)
        res = requests.get(url=url).json()
        printt(res)
        if len(res) > 0:
            droplet = res[0]
            scripts = droplet["scripts"]
            return scripts
    except Exception as e:
        printt("error in _retrieve_scripts_from_server():", str(e))
    return []


def _stop_scripts(scripts):
    sorted_scripts = sorted(scripts, key=lambda x: x["startTime"])
    for script in sorted_scripts:
        if not script["instance"] or not script["instance"] in _scripts:
            continue
        delay = script["startTime"] + DEFAULT_STOP_COOLDOWN - int(time.time())
        if delay > 0:
            printt("wait {0} before stopping instance: {1}".format(delay, script["instance"]))
            time.sleep(delay)
        _stop_script_by_instance(script["instance"])


def _stop_script_by_instance(instance):
    try:
        script = _scripts[instance]
        process = script["process"]
        # process.kill()
        # process.terminate()
        # os.kill(process.pid, signal.SIGINT)
        process.send_signal(signal.SIGINT)
        _scripts.pop(instance, None)
        # argv = ["login.py", "-s", "-q", "-ap", "-i", instance]
        # return run_script(argv, instance)
        return script
    except Exception as e:
        printt("error in _stop_script_by_instance(): " + str(e))
        return {}


def _restore_scripts(scripts):
    try:
        for script in scripts:
            if script["instance"] not in _scripts:
                argv = script["arguments"]
                _run_script(argv)
    except Exception as e:
        raise e


def _parse_script_arguments(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("username", nargs='?', type=str)
    parser.add_argument("password", nargs='?', type=str)
    parser.add_argument("proxy", nargs='?', type=str)
    parser.add_argument("-user", "--username1", type=str)
    parser.add_argument("-pass", "--password1", type=str)
    parser.add_argument("-proxy", "--proxy1", type=str)
    parser.add_argument("-c", "--chrome", action="store_true")
    parser.add_argument("-g", "--gui", action="store_true")
    parser.add_argument("-o", "--owner", type=str)
    parser.add_argument("-i", "--instance", type=str)
    parser.add_argument("-v", "--version", type=str)
    parser.add_argument("-n", "--name", type=str)
    parser.add_argument("-t", "--tasks", nargs="+", type=str)
    parser.add_argument("-p", "--pull", nargs="*", type=str)
    parser.add_argument("-pe", "--pull-exclude", nargs="*", type=str)
    parser.add_argument("-pb", "--pull-by", nargs="+", type=str)
    parser.add_argument("-q", "--query", action="store_true")
    parser.add_argument("-rp", "--retry-proxy", type=str, default="on")
    parser.add_argument("-rc", "--retry-credentials", type=str, default="on")
    parser.add_argument("-ap", "--allocate-proxy", action="store_true")
    parser.add_argument("-ra", "--retry-allocate", action="store_true")
    parser.add_argument("-m", "--merge", nargs="*", type=str)
    parser.add_argument("-s", "--silent", action="store_true")
    return parser.parse_args(argv)


#
#
#
#
#
#
#
#   initialize droplet server
#   (1) checkin and periodically report server status
#   (2) start droplet http server
#
#
#
#
#
#
#
def exit_gracefully(*av):
    printt("droplet shutting down...")
    checkout_droplet()
    global _report_timer
    global _httpd
    if _report_timer:
        _report_timer.cancel()
        printt("successfully cancelled report timer...")

    _httpd.server_close()
    printt(time.asctime(), 'Server DOWN')
    exit(0)


def checkout_droplet():
    global _id
    if _id:
        try:
            # report latest status to main server before checking-out
            _do_report_droplet_status()
            printt("successfully saved and stopped all scripts")
            # checkout this droplet
            url = CHECK_OUT_URL.replace("{id}", _id)
            result = requests.delete(url=url).json()
            result = result["result"]
            if result == "success":
                _id = None
                printt("successfully checked-out droplet")
                return
        except:
            pass
        printt("failed to check-out droplet")
    else:
        printt("droplet not checked-in. no need to check-out")


def checkin_droplet(port, name, _type):
    global _id
    if _id:
        printt("droplet already checked-in")
        return
    pid = os.getpid()
    data = {
        "systemUser": getpass.getuser(),
        "name": name,
        "type": _type,
        "port": port,
        "pid": pid
    }
    try:
        #
        # check in this droplet
        #
        headers = {'content-type': 'application/json'}
        res = requests.post(url=CHECK_IN_URL, data=json.dumps(data), headers=headers).json()
        _id = res["_id"]
        printt("successfully checked-in droplet")
        #
        #   load previous scripts
        #
        _retrieve_and_restore_all_scripts()
        printt("successfully restored all scripts")
        # return droplet id
        return _id
    except Exception as e:
        printt("error in checkin_droplet(): " + str(e))
        exit(0)


def periodically_report_to_main_server():
    global _id
    if not _id:
        return
    # keep timer alive
    global _report_timer
    _report_timer = threading.Timer(DEFAULT_REPORT_INTERVAL, periodically_report_to_main_server)
    _report_timer.start()

    # call the report interface
    _do_report_droplet_status()


def main():
    #
    #   parse arguments
    #
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--address", type=str)
    parser.add_argument("-p", "--port", type=int)
    parser.add_argument("-n", "--name", type=str)
    parser.add_argument("-t", "--type", type=str)
    parser.add_argument("-ri", "--report-interval", type=int)
    args = parser.parse_args()
    if not args.address:
        args.address = DEFAULT_SERVER_ADDRESS
    if not args.port:
        args.port = DEFAULT_PORT_NUMBER
    if not args.name:
        args.name = DEFAULT_SERVER_NAME
    if not args.type:
        args.type = DEFAULT_SERVER_TYPE
    if not args.report_interval:
        args.report_interval = DEFAULT_REPORT_INTERVAL
    #
    #   register graceful quit handler
    #
    try:
        signal.signal(signal.SIGINT, exit_gracefully)
        signal.signal(signal.SIGTERM, exit_gracefully)
        signal.signal(signal.SIGKILL, exit_gracefully)
    except Exception as e:
        printt("error-registering-exit-handlers: ", str(e))

    #
    #   checkin server
    #
    checkin_droplet(args.port, args.name, args.type)

    #
    #   start report timer
    #
    periodically_report_to_main_server()

    #
    #   start server
    #
    global _httpd
    try:
        printt('Server UP - %s:%s' % (args.address, args.port))
        _httpd = HTTPServer((args.address, args.port), Server)
        _httpd.serve_forever()

    except Exception as e:
        printt(str(e))

    #
    #   quit the program
    #
    exit_gracefully()


if __name__ == '__main__':
    main()

#
#
#
#
#
#
#   code recycle
#
#
#
#
#
#
# def get_droplet_status_summary():
#     # get script status (summary string), memory, cpu usage
#
#     #  query sys information by running command 'top'
#     #  deprecated
#
#     #  must use  top -b -n 1 | head -10 instead of top | head -10
#     #  regular top will print character position bytes in linux
#     #  that's the way the linux version top manages to print fixed position lines at top of screen
#
#     process = subprocess.Popen("exec " + "top -b -n 1 | head -10", shell=True,
#                                stdout=subprocess.PIPE,
#                                stderr=subprocess.PIPE,
#                                stdin=subprocess.PIPE)
#     summary = process.stdout.read().decode("utf-8")
#     process.wait()
#     process.kill()
#     # parse status summary
#     cpu_idle = 0
#     memory_used = 0
#     memory_free = 0
#     swap_used = 0
#     swap_free = 0
#
#     try:
#         cpu = re.search(r"Cpu[^\d.]+([\d.]+)[^\d.]+([\d.]+)[^\d.]+([\d.]+)[^\d.]+([\d.]+)", summary)
#         cpu_idle = float(cpu.group(4))
#     except:
#         pass
#     try:
#         memory = re.search(r"Mem[^\d.]+([\d.]+)[^\d.]+([\d.]+)[^\d.]+([\d.]+)", summary)
#         memory_free = float(memory.group(2))
#         memory_used = float(memory.group(3))
#     except:
#         pass
#     try:
#         swap = re.search(r"Swap[^\d.]+([\d.]+)[^\d.]+([\d.]+)[^\d.]+([\d.]+)", summary)
#         swap_free = float(swap.group(2))
#         swap_used = float(swap.group(3))
#     except:
#         pass
#     return {
#         # "summary": summary,
#         "cpuIdle": cpu_idle,
#         "memoryUsed": memory_used,
#         "memoryFree": memory_free,
#         "swapUsed": swap_used,
#         "swapFree": swap_free
#     }
