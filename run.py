from instapy import InstaPy
from instapy import smart_run
import lib.environments as env
import lib.tasks as tasks

env.config(version="run-1.0", type="run")

TRACK_FOLLOWER_COUNT_GAP = 3600

#
#
#
env.info("loading tasks...")
tasks_dict = tasks.load(env.args().tasks)
maneuver_queue = tasks.ManeuverQueue()
maneuver_queue.add_from_tasks(tasks_dict)

if not maneuver_queue or maneuver_queue.empty():
    env.info("tasks not valid. script quited")
    exit(0)
else:
    env.info("tasks loaded: " + str(env.args().tasks))

session = InstaPy(
    bypass_suspicious_attempt=True,
    headless_browser=True,
    use_firefox=True,
    **env.arguments()
)

with smart_run(session):
    env.report_success(session)
    env.set_session(session)

    while not maneuver_queue.empty():
        maneuver = maneuver_queue.get()
        maneuver.execute()

        env.track_follower_count(session, TRACK_FOLLOWER_COUNT_GAP)
