from instapy import InstaPy
from instapy import smart_run
import lib.environments as env

env.config(version="1.50", name="run")

TRACK_FOLLOWER_COUNT_GAP = 3600

#
#
env.info("loading tasks...")
action_queue = env.init_action_queue()
env.load_local_tasks(action_queue, env.args().tasks)
env.load_remote_tasks(action_queue, env.args().remote_tasks)
env.load_customer_tasks(action_queue, env.args().username, env.args().customer_tasks)

if not action_queue or action_queue.empty():
    env.info("no valid tasks available. script quiting...")
    exit(0)
else:
    env.info("tasks loaded: " + str(env.get_loaded_task_names()))

session = InstaPy(**env.arguments())

with smart_run(session):
    while not action_queue.empty():
        action = action_queue.get()
        action.execute()

        # env.fetch_tasks(action_queue)
        env.track_follower_count(session, TRACK_FOLLOWER_COUNT_GAP)
