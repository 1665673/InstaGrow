from instapy import InstaPy
from instapy.util import smart_run

import time
import reporter
import patch

reporter.set_version("like-ff-2.1-try")  # set a version tag
reporter.checkin()
patch.apply()

SLEEP_BETWEEN_EACH_LIKE = 20

tags = ['love', 'instagood', 'photooftheday', 'fashion']

session = InstaPy(
    headless_browser=True,
    bypass_suspicious_attempt=True,
    use_firefox=True,
    **reporter.arguments.all()
)

with smart_run(session):
    while True:
        for tag in tags:
            try:
                time.sleep(SLEEP_BETWEEN_EACH_LIKE)
                session.like_by_tags([tag], amount=1, interact=False)
            except Exception as e:
                reporter.error(e)
