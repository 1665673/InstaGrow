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
version = None
data = {}


#
#
#


def get_data(_username, _version=None):
    if _username:  # and _version: version is optional
        headers = {'content-type': 'application/json'}
        req = {
            "username": _username,
            "version": _version
        }
        res = requests.post(url=pull_url, data=json.dumps(req), headers=headers).json()
        return res
    return {}


if not is_module:
    parser = argparse.ArgumentParser()
    parser.add_argument("username", type=str)
    parser.add_argument("version", nargs='?', type=str)
    args = parser.parse_args()
    username = args.username
    version = args.version

    data = get_data(username, version)
    if "instagramUser" in data:
        print("%s %s %s" % (data["instagramUser"], data["instagramPassword"],
                            data["proxy"] if "proxy" in data else ""))
    else:
        print("no credentials available from server")


def userdata(_username, _version):
    global username
    global version
    global data
    username = _username
    version = _version

    if "lib.environments" in sys.modules:
        # username = sys.modules["lib.environments"]._args.username
        # if "version" in sys.modules["lib.environments"]._reporter_fields:
        #    version = sys.modules["lib.environments"]._reporter_fields["version"]
        data = get_data(username, version)
        version_str = version if version else "all-versions"
        if "instagramUser" in data:
            print("PULL  [%d] user credentials @ version [%s] pulled from server" % (int(time.time()), version_str))
            sys.modules["lib.environments"]._args.username = data["instagramUser"]
            sys.modules["lib.environments"]._args.password = data["instagramPassword"]
            sys.modules["lib.environments"]._args.proxy = (data["proxy"] if "proxy" in data else None)
        else:
            print("PULL  [%d] no credentials @ version [%s] available from server" % (int(time.time()), version_str))
