import time
from . import environments as env


def restart_script(session, message):
    env.event("TASK", "RESTARTING-SCRIPT", {"message": message})
    env.restart_script(session, message)


def follow_user(session, target):
    session.follow_by_list([target],
                           times=9223372036854775807,
                           sleep_delay=1,
                           interact=False)


def unfollow_user(session, target):
    session.unfollow_users(customList=(True, [target], "all"),
                           style="RANDOM",
                           unfollow_after=1,
                           sleep_delay=1)


def like_by_tag(session, target):
    session.like_by_tags([target], amount=1, interact=False)


def like_by_location(session, target):
    session.like_by_locations([target], amount=1)


handlers = {
    "restart-script": restart_script,
    "follow-user": follow_user,
    "unfollow-user": unfollow_user,
    "like-by-tag": like_by_tag,
    "like-by-location": like_by_location
}


def execute(action_type, target, ready):
    current = time.time()
    if current < ready:
        delay = ready - current
        env.log("sleep %1.2fs till task (%s, %s) is ready" % (delay, action_type, target), title="TASK")
        time.sleep(delay)

    env.log("now performing task (%s, %s)" % (action_type, target), title="TASK")
    session = env.get_session()
    try:
        return handlers[action_type](session, target)
    except Exception as e:
        env.error(action_type, "exception", str(e))
        return None
