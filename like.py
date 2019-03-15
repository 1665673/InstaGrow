from instapy import InstaPy
from instapy.util import smart_run

import time
import reporter

SLEEP_BETWEEN_EACH_LIKE = 20

reporter.set_version("like-ff-2.0")  # set a version tag

session = InstaPy(username=insta_username,
                  password=insta_password,
                  headless_browser=True,
                  use_firefox=True,
                  proxy_address="zproxy.lum-superproxy.io",
                  proxy_port=22225,
                  proxy_username="lum-customer-hl_648f8412-zone-static-ip-185.217.61.22",
                  proxy_password="9y4lv38oag4e")

with smart_run(session):
    while True:
        time.sleep(SLEEP_BETWEEN_EACH_LIKE)
        session.like_by_tags(['love'], amount=1, interact=False)

        time.sleep(SLEEP_BETWEEN_EACH_LIKE)
        session.like_by_tags(['instagood'], amount=1, interact=False)

        time.sleep(SLEEP_BETWEEN_EACH_LIKE)
        session.like_by_tags(['photooftheday'], amount=1, interact=False)

        time.sleep(SLEEP_BETWEEN_EACH_LIKE)
        session.like_by_tags(['fashion'], amount=1, interact=False)
