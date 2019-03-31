from instapy import InstaPy
from instapy.util import smart_run
import time
import lib.environments as env

env.config(version="like-ff-2.1")

SLEEP_BETWEEN_EACH_LIKE = 60
TRACK_FOLLOWER_COUNT_GAP = 3600

tags = ['love', 'instagood', 'photooftheday', 'fashion']

session = InstaPy(
    headless_browser=False,
    bypass_suspicious_attempt=True,
    use_firefox=False,
    **env.arguments()
)

with smart_run(session):
    env.report_success(session)
    while True:
        for tag in tags:
            try:
                time.sleep(SLEEP_BETWEEN_EACH_LIKE)
                session.like_by_tags([tag], amount=1, interact=False)
            except Exception as e:
                env.error("like_by_tags", "exception", str(e))

        env.track_follower_count(session, TRACK_FOLLOWER_COUNT_GAP)
