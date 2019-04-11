import time
import datetime
from . import environments as env


def hold_on(session, target):
    seconds = target
    time.sleep(int(seconds))


def restart_script(session, target):
    message = target
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
    utc = datetime.datetime.utcnow()
    if 7 <= utc.hour < 15:
        env.info("time is between 00:00 and 07:59 PST, skip this action")
        return
    session.like_by_tags([target], amount=2, interact=False)  # set amount = 2


def like_by_location(session, target):
    utc = datetime.datetime.utcnow()
    if 7 <= utc.hour < 15:
        env.info("time is between 00:00 and 07:59 PST, skip this action")
        return
    session.like_by_locations([target], amount=2)  # set amount = 2


def comment_by_location(session, target):
    utc = datetime.datetime.utcnow()
    if 7 <= utc.hour < 15:
        env.info("time is between 00:00 and 07:59 PST, skip this action")
        return
    session.comment_by_locations([target], amount=2, skip_top_posts=True)


handlers = {
    "hold-on": hold_on,
    "restart-script": restart_script,
    "follow-user": follow_user,
    "unfollow-user": unfollow_user,
    "like-by-tag": like_by_tag,
    "like-by-location": like_by_location,
    "comment-by-location": comment_by_location
}


def init_comment_by_location(session):
    session.set_do_comment(enabled=True, percentage=100)
    session.set_comments(comments=['Very good one', 'This is so Great', 'Really great', 'Awesome', 'Really Cool',
                                   'I like your stuff'])


inits = {
    "init-comment-by-location": init_comment_by_location
}


def execute(action_init, action_type, target, ready):
    current = time.time()
    if current < ready:
        delay = ready - current
        env.log("sleep %1.2fs till task (%s, %s) is ready" % (delay, action_type, target), title="TASK ")
        time.sleep(delay)

    env.log("now performing task (%s, %s)" % (action_type, target), title="TASK ")
    session = env.get_session()

    try:
        if action_init:
            inits[action_init](session)
        return handlers[action_type](session, target)
    except Exception as e:
        env.error(action_type, "exception", str(e))
        return None
