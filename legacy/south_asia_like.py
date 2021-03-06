from instapy import InstaPy
from instapy.util import smart_run
import time
import lib.environments as env

env.config(version="south-asia-ff-1.1")

SLEEP_BETWEEN_EACH_LIKE = 60
TRACK_FOLLOWER_COUNT_GAP = 3600

tags = ['215567918/kathmandu-nepal/', '278360789/nepal/', '498870164/new-delhi/', '302416621/taiwan/']

session = InstaPy(**env.arguments())

with smart_run(session):
    while True:
        for tag in tags:
            try:
                time.sleep(SLEEP_BETWEEN_EACH_LIKE)
                session.like_by_locations([tag], amount=1)
            except Exception as e:
                env.error("like_by_tags", "exception", str(e))

        env.fetch_task_and_execute()
        env.track_follower_count(session, TRACK_FOLLOWER_COUNT_GAP)
