import requests
import json
# import sys
import argparse
import os
import time
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
SERVER = os.getenv("SERVER") if os.getenv("SERVER") else "https://admin.socialgrow.live"

#
#   fucntion for apply a proxy
#
# is_module = False
# if "instapy" in sys.modules:
#    is_module = True

allocate_proxy_url = SERVER + "/admin/proxy/allocate/{group}/{tag}/{exclude}"
mark_fail_url = SERVER + "/admin/proxy/{string}/fails"


def allocate_proxy(group="default", tag="default", exclude=None):
    if not group:
        group = "default"
    if not tag:
        tag = "default"
    if not exclude:
        exclude = "null"

    url = allocate_proxy_url.format(group=group, tag=tag, exclude=exclude)
    try:
        # print(url)
        proxy = requests.get(url=url).json()
    except Exception:
        return ""
    if "string" in proxy:
        return proxy
    else:
        return ""


def mark_fail(proxy, client_id="proxypool.py"):
    url = mark_fail_url.replace("{string}", proxy)
    headers = {'content-type': 'application/json'}
    client = {
        "id": client_id,
        "time": int(time.time())
    }
    res = requests.post(url=url, data=json.dumps(client), headers=headers).json()
    return res


#
#
#   if not imported as a module
#   print some result to command line
#


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("current_proxy", nargs='?', type=str)
    parser.add_argument("-d", "--details", action="store_true")
    parser.add_argument("-f", "--fail", action="store_true")
    parser.add_argument("-c", "--client", type=str)
    args = parser.parse_args()
    proxy = args.current_proxy
    client = args.client
    details = args.details
    if not args.fail:
        allocated = allocate_proxy(proxy)
        if details:
            print(allocated)
        else:
            print({
                "id": allocated["_id"],
                "string": allocated["string"],
                "clients": len(allocated["clients"]),
                "fails": len(allocated["fails"]),
                "history": len(allocated["history"]),
                "allocateCount": allocated["allocateCount"]
            })
    else:
        if not proxy:
            print("specify a proxy to mark fail")
        else:
            res = {}
            if client:
                res = mark_fail(proxy, client)
            else:
                res = mark_fail(proxy)
            print(res)


if __name__ == "__main__":
    main()
