from instapy import InstaPy
from instapy.util import smart_run

import time
import reporter

SLEEP_BETWEEN_EACH_LIKE = 20


def main():
    reporter.set_version("like-ff-2.0")  # set a version tag

    session = InstaPy(
        headless_browser=True,
        bypass_suspicious_attempt=True,
        use_firefox=True,
        **reporter.Arguments().all()  # dump all arguments from command line
    )

    reporter.log("[check-in]")  # reporter.log() prints in both terminal and server

    with smart_run(session):
        while True:
            session.like_by_tags(['love'], amount=1, interact=False)
            time.sleep(SLEEP_BETWEEN_EACH_LIKE)

            session.like_by_tags(['instagood'], amount=1, interact=False)
            time.sleep(SLEEP_BETWEEN_EACH_LIKE)

            session.like_by_tags(['photooftheday'], amount=1, interact=False)
            time.sleep(SLEEP_BETWEEN_EACH_LIKE)

            session.like_by_tags(['fashion'], amount=1, interact=False)
            time.sleep(SLEEP_BETWEEN_EACH_LIKE)


main()
