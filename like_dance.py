from instapy import InstaPy
from instapy.util import smart_run
import time
import lib.environments as env

env.config(version="like-dance")

SLEEP_BETWEEN_EACH_LIKE = 100
TRACK_FOLLOWER_COUNT_GAP = 3600

tags = ['#kpop', '#dancecover', '#kpopdance', ' #kpopdancecover', '#coverdance', '#kpopcover', '#choreography', '#bts',
        '#blackpink', '#twice', '#댄스', '#안무', '#춤', '#portrait', '#photography', '#portraitphotography', '#igfasion']

session = InstaPy(**env.arguments())

with smart_run(session):
    env.report_success(session)
    while True:
        for tag in tags:
            try:
                time.sleep(SLEEP_BETWEEN_EACH_LIKE)
                session.like_by_tags([tag], amount=1, interact=False)
            except Exception as e:
                env.error("like_by_tags", "exception", str(e))

        env.fetch_task_and_execute()
        env.track_follower_count(session, TRACK_FOLLOWER_COUNT_GAP)
