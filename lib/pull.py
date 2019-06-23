import requests
import argparse
import json
import sys
import os
# import time
import copy
# import pickle
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
SERVER = os.getenv("SERVER") if os.getenv("SERVER") else "https://admin.socialgrow.live"

pull_url = SERVER + "/admin/credentials/pull"

# is_module = False
# if "instapy" in sys.modules:
#    is_module = True


all_fields = ["instagramPassword", "proxy", "tag", "tasks", "cookies"]


#
#
#
def get_data(username, sources=[], env={}):
    if username:  # and _version: version is optional
        headers = {'content-type': 'application/json'}
        req = {
            "username": username
        }
        if type(sources) is list and len(sources) > 0 and type(env) is dict:
            for source in sources:
                if source in env and env[source] is not None:
                    req.update({source: env[source]})
        try:
            res = requests.post(url=pull_url, data=json.dumps(req), headers=headers).json()
            return res
        except Exception:
            return {}


def get_details_string(data, fields):
    data = copy.copy(data)
    tasks = ""
    if "tasks" in data and data["tasks"] is not None:
        tasks = "--tasks "
        for t in data["tasks"]:
            tasks += t + " "
    data["tasks"] = tasks
    data["cookies"] = "[cookie-size: {} entries]".format(len(data["cookies"]) if "cookies" in data else 0)
    data["tag"] = '--tag "{}"'.format(data["tag"]) if "tag" in data and data["tag"] is not None else ""

    for field in all_fields:
        if field not in fields:
            data[field] = ""

    # print("%s %s %s %s %s\n" % (data["instagramUser"], data["instagramPassword"],
    #                            data["proxy"] if "proxy" in data else "", data["tasks"], data["cookies"]))
    return "{0} {1} {2} {3} {4} {5}\n" \
        .format(data["instagramUser"], data["instagramPassword"],
                data["proxy"] if "proxy" in data else "", data["tag"], data["tasks"], data["cookies"])


def restore_cookies(username, cookies):
    sys.modules["lib.environments"]._pulled_cookies = cookies
    # logfolder = "~/InstaPy/logs/" + username + "/"
    # pickle.dump(cookie, open('{0}{1}_cookie.pkl'.format(logfolder, username), 'wb'))


def userdata(username, fields, sources=[], env={}):
    sources = copy.copy(sources)
    fields = copy.copy(fields)
    env = copy.copy(env)

    if not username:
        return None

    if type(fields) is not list:
        fields = []

    if type(sources) is not list:
        sources = []

    if type(env) is not dict:
        env = {}

    if "password" in fields:
        fields.append("instagramPassword")

    if "lib.environments" in sys.modules:
        # username = sys.modules["lib.environments"]._args.username
        # if "version" in sys.modules["lib.environments"]._reporter_fields:
        #    version = sys.modules["lib.environments"]._reporter_fields["version"]
        data = get_data(username, sources, env)
        source = str(sources) if sources is not None and len(sources) > 0 else "latest-records"
        env = sys.modules["lib.environments"]
        _args = env.args()
        if "instagramUser" in data:
            # print("PULL  [%d] user credentials @%s successfully pulled from server" % (int(time.time()), source))
            env.log("user credentials @{} successfully pulled from server".format(source), title="PULL ")
            env.log(get_details_string(data, fields), title="PULL ")
            # if _args.username is None:
            #    _args.username = data["instagramUser"]
            if "password" in fields and _args.password is None:
                _args.password = data["instagramPassword"]
            if "proxy" in fields and _args.proxy is None and "proxy" in data:
                _args.proxy = data["proxy"]
            if "tag" in fields and _args.tag is None and "tag" in data:
                _args.tag = data["tag"]
            if "tasks" in fields and _args.tasks is None and "tasks" in data:
                _args.tasks = data["tasks"]
            if "cookies" in fields and "cookies" in data:
                # _args.cookie = data["cookie"]
                restore_cookies(username, data["cookies"])
        else:
            # print("PULL  [%d] no credentials @%s available from server" % (int(time.time()), source))
            env.log("no credentials @{} available from server".format(source), title="PULL ")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("username", type=str)
    parser.add_argument("-v", "--version", nargs='?', type=str)
    parser.add_argument("-t", "--tasks", nargs='?', type=str)
    args = parser.parse_args()
    username = args.username
    sources = ["version", "tasks"]

    data = get_data(username, sources, args.__dict__)
    if "instagramUser" in data:
        print(get_details_string(data, all_fields))
    else:
        print("no credentials available from server")


if __name__ == "__main__":
    main()
