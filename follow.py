from instapy import InstaPy
from instapy import smart_run

import time
import reporter

SLEEP_BETWEEN_EACH_FOLLOW = 25
SLEEP_AFTER_ALL_FOLLOW = 240
SLEEP_BETWEEN_EACH_UNFOLLOW = 20

users_celebrity = ['justinbieber', 'taylorswift', 'selenagomez', 'kimkardashian', 'arianagrande', 'instagram',
                   'beyonce', 'kyliejennr', 'katyperry', 'therock']
users = users_celebrity


def main():
    reporter.set_version("follow-ff-2.0")

    session = InstaPy(
        headless_browser=True,
        bypass_suspicious_attempt=True,
        use_firefox=True,
        **reporter.Arguments().all()
    )

    reporter.log("[check-in]")

    with smart_run(session):
        while True:
            for user in users:
                session.follow_by_list([user],
                                       times=9223372036854775807,
                                       sleep_delay=1,
                                       interact=False)
                time.sleep(SLEEP_BETWEEN_EACH_FOLLOW)

            reporter.log("[sleep {0} seconds before unfollowing]".format(SLEEP_AFTER_ALL_FOLLOW))
            time.sleep(SLEEP_AFTER_ALL_FOLLOW)

            for user in users:
                session.unfollow_users(customList=(True, [user], "all"),
                                       style="RANDOM",
                                       unfollow_after=1,
                                       sleep_delay=1)
                time.sleep(SLEEP_BETWEEN_EACH_UNFOLLOW)


# call main function
main()
