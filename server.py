import time
from http.server import HTTPServer
from http.server import BaseHTTPRequestHandler
import re
import os
import sys


class Server(BaseHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super(BaseHTTPRequestHandler, self).__init__(*a, **kw)
        self.instances = {}

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

        parts = re.search("/([^/]+)/([^/]+)", self.path)
        if parts:
            parts = parts.groups()
            if len(parts) == 2:
                action = parts[0]
                param = parts[1]

                if action == "login":
                    self.login_script(param)
                elif action == "start":
                    self.start_script(param)
                elif action == "stop":
                    self.stop_script(param)
                elif action == "restart":
                    self.restart_script(param)
                else:
                    pass

                return bytes("ok", "UTF-8")

        return bytes("error", "UTF-8")

    def login_script(self, param):
        instance = param
        run_login_script(instance)

    def start_script(self, param):
        print(sys.argv)
        print(*sys.argv)

    def stop_script(self, param):
        print("instance stopped:", param)

    def restart_script(self, param):
        print("instance restarted:", param)


def run_login_script(instance):
    if not instance:
        return
    argv = ["login.py", "-q", "-ap", "-i", instance]
    run_script(argv)


def run_script(argv):
    n = os.fork()
    if n > 0:
        print("Parent process and id is : ", os.getpid())
    else:
        python = sys.executable
        os.execl(python, python, *argv)


HOST_NAME = 'localhost'
PORT_NUMBER = 8000




def checkin_server():
    os.getpid()


if __name__ == '__main__':
    httpd = HTTPServer((HOST_NAME, PORT_NUMBER), Server)
    print(time.asctime(), 'Server UP - %s:%s' % (HOST_NAME, PORT_NUMBER))

    checkin_server()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print(time.asctime(), 'Server DOWN - %s:%s' % (HOST_NAME, PORT_NUMBER))