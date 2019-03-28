import requests
import argparse
import json
import sys
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
SERVER = os.getenv("SERVER")

pull_url = SERVER + "/admin/credentials/pull"

is_module = False
if "instapy" in sys.modules:
    is_module = True

#
#   input & output
#
username = None
data = {}
#
#
#

if not is_module:
    parser = argparse.ArgumentParser()
    parser.add_argument("username", type=str)
    args = parser.parse_args()
    username = args.username
else:
    if "environments" in sys.modules:
        username = sys.modules["environments"]._args.username

if username:
    headers = {'content-type': 'application/json'}
    req = {
        "username": username
    }
    data = requests.post(url=pull_url, data=json.dumps(req), headers=headers).json()

if not is_module:
    if "instagramUser" in data:
        print("%s %s %s" % (data["instagramUser"], data["instagramPassword"],
                            data["proxy"] if "proxy" in data else ""))
    else:
        print("no credentials available from server")
else:
    if "environments" in sys.modules:
        if "instagramUser" in data:
            print("[PULL] user credentials pulled from server")
            sys.modules["environments"]._args.username = data["instagramUser"]
            sys.modules["environments"]._args.password = data["instagramPassword"]
            sys.modules["environments"]._args.proxy = (data["proxy"] if "proxy" in data else None)
        else:
            print("[PULL] no credentials available from server")
