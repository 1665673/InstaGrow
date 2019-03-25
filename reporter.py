import requests
import json
import sys
import io
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
            requests.post(url=self.report_url, data=json.dumps(self.payload), headers=headers)
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
