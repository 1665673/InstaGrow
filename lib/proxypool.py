import requests
import json
import sys
import argparse
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
SERVER = os.getenv("SERVER")

#
#   fucntion for apply a proxy
#
apply_proxy_url = SERVER + "/admin/proxy/apply"


def allocate_proxy(current_proxy=None):
    url = apply_proxy_url + "/" + current_proxy if current_proxy else apply_proxy_url
    proxy = requests.get(url=url).json()
    if "string" in proxy:
        return proxy["string"]
    else:
        return None


#
#
#   if not imported as a module
#   print some result to command line
#
is_module = False
if "instapy" in sys.modules:
    is_module = True

if not is_module:
    parser = argparse.ArgumentParser()
    parser.add_argument("current_proxy", nargs='?', type=str)
    args = parser.parse_args()
    print(allocate_proxy(args.current_proxy))
