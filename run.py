from instapy import InstaPy
from instapy import smart_run
import lib.environments as env

env.config(version="run-1.31", type="run")

TRACK_FOLLOWER_COUNT_GAP = 3600

#
#
env.info("loading tasks...")
action_queue = env.load_tasks(env.args().tasks)

if not action_queue or action_queue.empty():
    env.info("tasks not valid. script quited")
    exit(0)
else:
    env.info("tasks loaded: " + str(env.args().tasks))

session = InstaPy(**env.arguments())

with smart_run(session):
    env.report_success(session)

    while not action_queue.empty():
        action = action_queue.get()
        action.execute()

        env.fetch_tasks(action_queue)
        env.track_follower_count(session, TRACK_FOLLOWER_COUNT_GAP)
