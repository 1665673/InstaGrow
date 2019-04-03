import requests
import argparse
import json
import sys
import os
import time
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
SERVER = os.getenv("SERVER") if os.getenv("SERVER") else "https://admin.socialgrow.live"

pull_url = SERVER + "/admin/credentials/pull"

is_module = False
if "instapy" in sys.modules:
    is_module = True

#
#   input & output
#
username = None
sources = None
data = None


#
#
#


def get_data(_username, _sources=[], _env={}):
    if _username:  # and _version: version is optional
        headers = {'content-type': 'application/json'}
        req = {
            "username": _username
        }
        if _sources is not None and len(_sources) > 0 and type(_env) is dict:
            for source in _sources:
                if source in _env and _env[source] is not None:
                    req.update({source: _env[source]})
        try:
            res = requests.post(url=pull_url, data=json.dumps(req), headers=headers).json()
            return res
        except Exception:
            return {}


if not is_module:
    parser = argparse.ArgumentParser()
    parser.add_argument("username", type=str)
    parser.add_argument("-v", "--version", nargs='?', type=str)
    parser.add_argument("-t", "--tasks", nargs='?', type=str)
    args = parser.parse_args()
    username = args.username
    sources = ["version", "tasks"]

    data = get_data(username, sources, args.__dict__)
    if "instagramUser" in data:
        print("%s %s %s" % (data["instagramUser"], data["instagramPassword"],
                            data["proxy"] if "proxy" in data else ""))
    else:
        print("no credentials available from server")


def userdata(_username, _sources=[], _env={}):
    global username
    global sources
    global data
    username = _username
    sources = _sources

    if not username:
        return None

    if "lib.environments" in sys.modules:
        # username = sys.modules["lib.environments"]._args.username
        # if "version" in sys.modules["lib.environments"]._reporter_fields:
        #    version = sys.modules["lib.environments"]._reporter_fields["version"]
        data = get_data(username, sources, _env)
        source = str(_sources) if _sources is not None and len(_sources) > 0 else "latest-records"
        if "instagramUser" in data:
            print("PULL  [%d] user credentials @%s successfully pulled from server" % (int(time.time()), source))
            sys.modules["lib.environments"]._args.username = data["instagramUser"]
            sys.modules["lib.environments"]._args.password = data["instagramPassword"]
            sys.modules["lib.environments"]._args.proxy = (data["proxy"] if "proxy" in data else None)
        else:
            print("PULL  [%d] no credentials @%s available from server" % (int(time.time()), source))
