from instapy import InstaPy
from instapy import smart_run
import time
import lib.environments as env

env.config(version="follow-ff-2.1")

SLEEP_BETWEEN_EACH_FOLLOW = 25
SLEEP_AFTER_ALL_FOLLOW = 240
SLEEP_BETWEEN_EACH_UNFOLLOW = 20
TRACK_FOLLOWER_COUNT_GAP = 3600

users_celebrity = ['justinbieber', 'taylorswift', 'selenagomez', 'kimkardashian', 'arianagrande', 'instagram',
                   'beyonce', 'kyliejennr', 'katyperry', 'therock']
users = users_celebrity

session = InstaPy(**env.arguments())

with smart_run(session):
    env.report_success(session)
    while True:
        for user in users:
            try:
                session.follow_by_list([user],
                                       times=9223372036854775807,
                                       sleep_delay=1,
                                       interact=False)
                time.sleep(SLEEP_BETWEEN_EACH_FOLLOW)
            except Exception as e:
                env.error("follow_by_list", "exception", str(e))

        env.log("[sleep {0} seconds before unfollowing]".format(SLEEP_AFTER_ALL_FOLLOW))
        time.sleep(SLEEP_AFTER_ALL_FOLLOW)

        for user in users:
            try:
                session.unfollow_users(customList=(True, [user], "all"),
                                       style="RANDOM",
                                       unfollow_after=1,
                                       sleep_delay=1)
                time.sleep(SLEEP_BETWEEN_EACH_UNFOLLOW)
            except Exception as e:
                env.error("unfollow_users", "exception", str(e))

        env.track_follower_count(session, TRACK_FOLLOWER_COUNT_GAP)
