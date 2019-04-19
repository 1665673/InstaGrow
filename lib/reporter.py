import requests
import sys
import io
import time
import json


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

    def flush(self):
        if self.save:
            super(StreamHub, self).flush()
        if self.print and StreamHub.stdout:
            StreamHub.stdout.flush()
        if self.log and StreamHub.stderr:
            StreamHub.stderr.flush()
        if self.report and self.reporter:
            self.reporter.flush()


class Reporter:
    def __init__(self):
        self.id = None
        self.attributes = {}
        self.checkin_url = None
        self.access_url = None
        self.payload = {"accounts": {}, "attributes": {}, "retrieve": []}
        self.headers = {'content-type': 'application/json'}

    def __merge(self, array, account):
        if account not in self.payload["accounts"]:
            self.payload["accounts"][account] = array
        else:
            self.payload["accounts"][account] += array
        self.payload["time"] = int(time.time())

    def __post(self):
        if not self.id or not self.access_url or len(self.payload.keys()) == 0:
            return
        self.payload["id"] = self.id
        data = self.payload
        try:
            requests.post(url=self.access_url, data=json.dumps(data), headers=self.headers)
        except Exception as e:
            pass
        finally:
            self.payload = {"accounts": {}, "attributes": {}, "retrieve": []}

    def checkin(self, url, attributes):
        self.attributes = attributes
        self.checkin_url = url
        data = attributes
        try:
            res = requests.post(url=url, data=json.dumps(data), headers=self.headers).json()
            self.id = res["id"]
            self.access_url = res["accessUrl"]
        except Exception as e:
            pass

    def update(self, attributes):
        if not self.id or not self.access_url or len(attributes.keys()) == 0:
            return
        data = {"id": self.id, "attributes": attributes}
        try:
            requests.post(url=self.access_url, data=json.dumps(data), headers=self.headers)
        except Exception as e:
            pass

    def retrieve(self, attributes):
        if not self.id or not self.access_url or len(attributes) == 0:
            return
        data = {"id": self.id, "retrieve": attributes}
        try:
            return requests.post(url=self.access_url, data=json.dumps(data), headers=self.headers).json()
        except Exception as e:
            pass
        return {}

    def send(self, buffer, account="messages"):
        buffer = buffer.rstrip()
        if buffer == "":
            return
        self.push([buffer], account)

    def json(self, json, account="json"):
        self.push([json], account)

    def push(self, array, account):
        self.__merge(array, account)
        self.__post()

    def flush(self):
        pass
