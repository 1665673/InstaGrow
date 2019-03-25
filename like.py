from instapy import InstaPy
from instapy.util import smart_run
import time
import environments as env

env.config(version="like-ff-2.1")

SLEEP_BETWEEN_EACH_LIKE = 40

tags = ['love', 'instagood', 'photooftheday', 'fashion']

session = InstaPy(
    headless_browser=True,
    bypass_suspicious_attempt=True,
    use_firefox=True,
    **env.arguments()
)

with smart_run(session):
    while True:
        for tag in tags:
            try:
                time.sleep(SLEEP_BETWEEN_EACH_LIKE)
                session.like_by_tags([tag], amount=1, interact=False)
            except Exception as e:
                env.error("like_by_tags", "exception", e)
