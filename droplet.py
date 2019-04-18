import time
from http.server import HTTPServer
from http.server import BaseHTTPRequestHandler
import json
import re
import os
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
DEFAULT_PORT_NUMBER = 8000
MAIN_SERVER_ADDRESS = os.getenv("SERVER") if os.getenv("SERVER") else "https://admin.socialgrow.live"
#
#   REST checkin interface
#
CHECK_IN_URL = MAIN_SERVER_ADDRESS + "/admin/droplets"  # POST
CHECK_OUT_URL = MAIN_SERVER_ADDRESS + "/admin/droplets/{id}"  # DEL
REPORT_STATUS_URL = MAIN_SERVER_ADDRESS + "/admin/droplets/{id}"  # PUT
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
        self.end_headers()

        parts = re.search("/([^/]+)/([^/]+)(/([^/]+))?", self.path)
        result = {
            "result": "no result"
        }
        if parts:
            parts = parts.groups()
            if len(parts) > 2:
                action = parts[0]
                instance = parts[1]
                arguments = None
                if len(parts) == 4:
                    arguments = parts[3]

                try:
                    if action == "login":
                        login_script(instance)
                    elif action == "start":
                        start_script(instance, arguments.split('+'))
                    elif action == "stop":
                        stop_script(instance)
                    elif action == "restart":
                        restart_script(instance)
                    else:
                        pass
                    message = "success"
                except Exception as e:
                    message = str(e)
            else:
                message = "not-enough-url-arguments"
        else:
            message = "invalid-url"

        result["result"] = message

        return bytes(json.dumps(result), "UTF-8")


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


def login_script(instance):
    if not instance:
        raise Exception("no-instance")
    if instance in _scripts:
        raise Exception("instance-already-exists")
    argv = ["login.py", "-q", "-ap", "-s", "-i", instance, "-g"]
    run_script(instance, "__LOGIN__", argv)


# arguments is a list consumed by subprocess.Popen
def start_script(instance, arguments):
    printt("[start-script] instance:", instance)
    if not instance:
        raise Exception("no-instance")
    if instance in _scripts:
        raise Exception("instance-already-exists")
    if len(arguments) < 2:
        raise Exception("not-enough-script-arguments")
    # find username
    username = None
    if "-u" in arguments or "--username" in arguments:
        for i in range(len(arguments)):
            if (arguments[i] == "-u" or arguments[i] == "--username") and i < len(arguments) - 1:
                username = arguments[i + 1]
                break
    else:
        username = arguments[1]
    if not username or username[0] == '-':
        raise Exception("no-username")
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
    run_script(instance, username, arguments)


def stop_script(instance):
    printt("[stop-script] instance:", instance)
    if not instance or instance not in _scripts:
        raise Exception("no-instance or invalid instance")
    start_time = _scripts[instance]["start-time"]
    if start_time + 30 < int(time.time()):
        raise Exception("please don't stop an instance within 30 seconds of starting. wait for another: {} seconds"
                        .format(int(time.time()) - start_time))
    process = _scripts[instance]["process"]
    # process.kill()
    # process.terminate()
    # os.kill(process.pid, signal.SIGINT)
    process.send_signal(signal.SIGINT)
    return _scripts.pop(instance, None)
    # argv = ["login.py", "-s", "-q", "-ap", "-i", instance]
    # return run_script(argv, instance)


def restart_script(instance):
    printt("[restart-script] instance:", instance)
    process_info = stop_script(instance)
    start_script(instance, process_info["arguments"])
    # argv = ["login.py", "-s", "-q", "-ap", "-i", instance]
    # return run_script(argv, instance)


def run_script(instance, username, argv):
    global _scripts
    # n = os.fork()
    # if n > 0:
    #     printt("Parent process and id is : ", os.getpid())
    # else:
    #     python = sys.executable
    #     os.execl(python, python, *argv)
    printt("[run-script]", "about to run this script:\n", instance, username, str(["python3"] + argv))

    try:
        process = subprocess.Popen(["python3"] + argv,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   stdin=subprocess.PIPE)
        _scripts[instance] = {
            "username": username,
            "arguments": argv,
            "process": process,
            "start-time": int(time.time())
        }
    except Exception as e:
        printt(str(e))
        raise
    # output = process.stdout.read()
    # log("output from terminal:\n" + str(output, "utf-8"), title="GIT  ")


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
        headers = {'content-type': 'application/json'}
        res = requests.post(url=CHECK_IN_URL, data=json.dumps(data), headers=headers).json()
        _id = res["_id"]
        printt("successfully checked-in droplet")
        return _id
    except Exception as e:
        printt("error in checkin_droplet(): " + str(e))
        exit(0)


def report_to_main_server():
    global _id
    if not _id:
        return
    # keep timer alive
    global _report_timer
    _report_timer = threading.Timer(DEFAULT_REPORT_INTERVAL, report_to_main_server)
    _report_timer.start()

    data = {
        "status": get_droplet_status_summary(),
        "scripts": get_droplet_scripts_summary()
    }
    headers = {'content-type': 'application/json'}
    try:
        url = REPORT_STATUS_URL.replace("{id}", _id)
        requests.put(url=url, data=json.dumps(data), headers=headers)
    except Exception as e:
        printt("report_to_main_server(): " + str(e))


def get_droplet_status_summary():
    # get script status (summary string), memory, cpu usage
    process = subprocess.Popen("exec " + "top -b -n 1 | head -10", shell=True, stdout=subprocess.PIPE)
    summary = process.stdout.read().decode("utf-8")
    process.kill()
    # parse status summary
    cpu_idle = None
    memory_used = None
    memory_free = None
    swap_used = None
    swap_free = None
    try:
        cpu = re.search(r"Cpu[^\d.]+([\d.]+)[^\d.]+([\d.]+)[^\d.]+([\d.]+)[^\d.]+([\d.]+)", summary)
        cpu_idle = cpu.group(4)
    except:
        pass
    try:
        memory = re.search(r"Mem[^\d.]+([\d.]+)[^\d.]+([\d.]+)", summary)
        memory_used = float(memory.group(1))
        memory_free = float(memory.group(2))
    except:
        pass
    try:
        swap = re.search(r"Swap[^\d.]+([\d.]+)[^\d.]+([\d.]+)", summary)
        swap_used = float(swap.group(1))
        swap_free = float(swap.group(2))
    except:
        pass
    return {
        # "summary": summary,
        "cpuIdle": cpu_idle,
        "memoryUsed": memory_used,
        "memoryFree": memory_free,
        "swapUsed": swap_used,
        "swapFree": swap_free
    }


def get_droplet_scripts_summary():
    global _scripts
    # get script abstracts
    scripts = []
    for instance in _scripts:
        scripts.append({
            "instance": instance,
            "arguments": _scripts[instance]["arguments"],
            "username": _scripts[instance]["username"],
            "startTime": _scripts[instance]["start-time"]
        })
    return scripts


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
    report_to_main_server()

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
