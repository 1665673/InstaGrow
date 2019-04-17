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
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

DEFAULT_SERVER_NAME = "not-named-server"
DEFAULT_REPORT_INTERVAL = 5
DEFAULT_PORT_NUMBER = 8000
MAIN_SERVER_ADDRESS = os.getenv("SERVER") if os.getenv("SERVER") else "https://admin.socialgrow.live"
CHECK_IN_URL = MAIN_SERVER_ADDRESS + "/admin/droplet/check-in"
REPORT_STATUS_URL = MAIN_SERVER_ADDRESS + "/admin/droplet/report-status"
_scripts = {}


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
        content = self.handle_http(200, "text/html")
        self.wfile.write(content)

    def handle_http(self, status, content_type):
        self.send_response(status)
        self.send_header("Content-type", content_type)
        self.end_headers()

        parts = re.search("/([^/]+)/([^/]+)(/([^/]+))?", self.path)
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
                    return bytes("ok", "UTF-8")
                except Exception as e:
                    return bytes(str(e), "UTF-8")
            return bytes("not-enough-url-arguments", "UTF-8")

        return bytes("invalid-url", "UTF-8")


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
def login_script(instance):
    if not instance:
        raise Exception("no-instance")
    if instance in _scripts:
        raise Exception("instance-already-exists")
    argv = ["login.py", "-q", "-ap", "-s", "-i", instance, "-g"]
    run_script(instance, "__LOGIN__", argv)


# arguments is a list consumed by subprocess.Popen
def start_script(instance, arguments):
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
    if "-g" not in arguments and "--gui" not in arguments:
        arguments += ["-g"]
    run_script(instance, username, arguments)


def stop_script(instance):
    if not instance or instance not in _scripts:
        raise Exception("no-instance or invalid instance")
    process = _scripts[instance]["process"]
    # process.kill()
    # process.terminate()
    # os.kill(process.pid, signal.SIGINT)
    process.send_signal(signal.SIGINT)
    return _scripts.pop(instance, None)
    # argv = ["login.py", "-s", "-q", "-ap", "-i", instance]
    # return run_script(argv, instance)


def restart_script(instance):
    process_info = stop_script(instance)
    print(process_info)
    start_script(instance, process_info["arguments"])
    # argv = ["login.py", "-s", "-q", "-ap", "-i", instance]
    # return run_script(argv, instance)


def run_script(instance, username, argv):
    global _scripts
    # n = os.fork()
    # if n > 0:
    #     print("Parent process and id is : ", os.getpid())
    # else:
    #     python = sys.executable
    #     os.execl(python, python, *argv)
    print("!!!!!about to run this script:\n", instance, username, str(["python3"] + argv))

    try:
        process = subprocess.Popen(["python3"] + argv,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   stdin=subprocess.PIPE)
        _scripts[instance] = {
            "username": username,
            "arguments": argv,
            "process": process
        }
    except Exception as e:
        print(str(e))
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
def checkin_droplet(name, port):
    pid = os.getpid()
    data = {
        "name": name,
        "pid": pid,
        "port": port
    }
    try:
        headers = {'content-type': 'application/json'}
        res = requests.post(url=CHECK_IN_URL, data=json.dumps(data), headers=headers).json()
        return res["_id"]
    except Exception as e:
        print("error in checkin_droplet(): " + str(e))
        exit(0)


def report_to_main_server(droplet_id):
    # keep timer alive
    threading.Timer(DEFAULT_REPORT_INTERVAL, report_to_main_server, [droplet_id]).start()

    data = {
        "_id": droplet_id,
        "status": get_droplet_status_summary(),
        "scripts": get_droplet_scripts_summary()
    }
    headers = {'content-type': 'application/json'}
    try:
        requests.post(url=REPORT_STATUS_URL, data=json.dumps(data), headers=headers)
    except Exception as e:
        print("report_to_main_server(): " + str(e))


def get_droplet_status_summary():
    # get script status (summary string), memory, cpu usage
    process = subprocess.Popen("exec " + "top | head -10", shell=True, stdout=subprocess.PIPE)
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
        memory_used = memory.group(1)
        memory_free = memory.group(2)
    except:
        pass
    try:
        swap = re.search(r"Swap[^\d.]+([\d.]+)[^\d.]+([\d.]+)", summary)
        swap_used = swap.group(1)
        swap_free = swap.group(2)
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
            "username": _scripts[instance]["username"]
        })
    return scripts


def main():
    #
    #   parse arguments
    #
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--name", type=str)
    parser.add_argument("-p", "--port", type=int)
    parser.add_argument("-ri", "--report-interval", type=int)
    args = parser.parse_args()
    if not args.name:
        args.name = DEFAULT_SERVER_NAME
    if not args.port:
        args.port = DEFAULT_PORT_NUMBER
    if not args.report_interval:
        args.report_interval = DEFAULT_REPORT_INTERVAL
    #
    #   checkin server
    #
    droplet_id = checkin_droplet(args.name, args.port)

    #
    #   start report timer
    #
    report_to_main_server(droplet_id)

    #
    #   start server
    #
    httpd = None
    try:
        httpd = HTTPServer(("localhost", args.port), Server)
        print(time.asctime(), 'Server UP - %s:%s' % ("localhost", args.port))
        httpd.serve_forever()
    except Exception as e:
        print(str(e))
        exit(0)
    httpd.server_close()
    print(time.asctime(), 'Server DOWN - %s:%s' % ("localhost", args.port))


if __name__ == '__main__':
    main()
