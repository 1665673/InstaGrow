import time
from . import environments as env


def follow_by_list(session, target):
    session.follow_by_list([target],
                           times=9223372036854775807,
                           sleep_delay=1,
                           interact=False)


def unfollow_by_list(session, target):
    session.unfollow_users(customList=(True, [target], "all"),
                           style="RANDOM",
                           unfollow_after=1,
                           sleep_delay=1)


def like_by_tags(session, target):
    session.like_by_tags([target], amount=1, interact=False)


def like_by_locations(session, target):
    session.like_by_locations([target], amount=1)


handlers = {
    "follow-by-list": follow_by_list,
    "unfollow-by-list": unfollow_by_list,
    "like-by-tags": like_by_tags,
    "like-by-locations": like_by_locations
}


def execute(action_type, target, ready):
    current = time.time()
    if current < ready:
        delay = ready - current
        env.log("sleep %1.2fs till task (%s,%s) is ready" % (delay, action_type, target), title="TASK")
        time.sleep(delay)
    else:
        env.log("now performing task (%s,%s)" % (action_type, target), title="TASK")

    session = env.get_session()
    try:
        return handlers[action_type](session, target)
    except Exception as e:
        env.error(action_type, "exception", str(e))
        return None
