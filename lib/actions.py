import time
import datetime
import sys
from . import environments as env


def register_handlers():
    return {
        #
        #   actions
        #
        "hold-on": hold_on,
        "self-restart": self_restart,
        "self-update": self_update,
        "follow-user": follow_user,
        "unfollow-user": unfollow_user,
        "like-by-tag": like_by_tag,
        "like-by-location": like_by_location,
        "comment-by-location": comment_by_location,

        #
        #   sub-task initializers
        #
        "init-comment-by-location": init_comment_by_location
    }


#
#
#   for all action handlers:
#       (1) if it RETURNS a value, it has to be a boolean value indicating if action succeeded
#           the tasks framework will automatically update statistics according to this value
#       (2) if it doesn't RETURN a value, or returns None
#           this action won't go into statistics
#       (3) if you want to do customized complicated statistics other than simply a success/fail count
#           please RETURN None, then implement the customized logic in handler
#
#
def hold_on(session, target):
    seconds = target
    time.sleep(int(seconds))


def self_restart(session, target):
    arguments = target
    env.event("SCRIPT", "SELF-RESTARTING", {"arguments": arguments})
    env.self_restart(session, arguments)


def self_update(session, target):
    env.event("SCRIPT", "SELF-UPDATING")
    env.self_update()


def follow_user(session, target):
    follow_single_user = sys.modules['instapy.unfollow_util'].follow_user
    success = follow_single_user(session.browser, "profile", session.username, target,
                                 None, session.blacklist, session.logger, session.logfolder)
    return success[1] == "success" or (None if "unfollow-user" not in env._action_statistics else False)


def unfollow_user(session, target):
    unfollow_single_user = sys.modules['instapy.unfollow_util'].unfollow_user
    success = unfollow_single_user(session.browser, "profile", session.username, target,
                                   None, None, session.relationship_data, session.logger, session.logfolder)
    return success[1] == "success"


def like_by_tag(session, target):
    utc = datetime.datetime.utcnow()
    if 7 <= utc.hour < 15:
        env.info("time is between 00:00 and 07:59 PST, skip this action")
        return
    # fetch and cache amount = 50 links at a time
    session.like_by_tags([target], amount=50, interact=False)
    return session.like_img_success


def like_by_location(session, target):
    utc = datetime.datetime.utcnow()
    if 7 <= utc.hour < 15:
        env.info("time is between 00:00 and 07:59 PST, skip this action")
        return
    session.like_by_locations([target], amount=50)
    return session.like_img_success


def comment_by_location(session, target):
    utc = datetime.datetime.utcnow()
    if 7 <= utc.hour < 15:
        env.info("time is between 00:00 and 07:59 PST, skip this action")
        return
    session.comment_by_locations([target], amount=50, skip_top_posts=True)
    return session.comment_img_success


def init_comment_by_location(session):
    session.set_do_comment(enabled=True, percentage=100)
    session.set_comments(comments=['Very good one', 'This is so Great', 'Really great', 'Awesome', 'Really Cool',
                                   'I like your stuff'])


#
#
#
#
#
#
#
#
#
#
#   below are interfaces for tasks.py
#   do not modify
#
#
#
#
#
#
#
#
handlers = register_handlers()


def execute(action_type, target, ready):
    current = time.time()
    if current < ready:
        delay = ready - current
        env.log("sleep %1.2fs till task (%s, %s) is ready" % (delay, action_type, target), title="TASK ")
        time.sleep(delay)

    env.log("now performing task (%s, %s)" % (action_type, target), title="TASK ")
    session = env.get_session()
    try:
        success = handlers[action_type](session, target)
        do_statistics(action_type, target, success)
    except Exception as e:
        if not e:
            e = "action-handler-error"
        env.error(action_type, "exception", str(e))
        return None


def init_subtask(handler):
    session = env.get_session()
    if not handler:
        return
    try:
        handlers[handler](session)
    except Exception as e:
        if not e:
            e = "subtask-init-error"
        env.error(handler, "exception", str(e))


def do_statistics(action, target, success):
    if action is None or success is None:
        return
    statistics = env._action_statistics
    if action not in statistics:
        statistics[action] = {
            "success": 0,
            "fail": 0
        }
    if success:
        statistics[action]["success"] += 1
    else:
        statistics[action]["fail"] += 1
    env.update({"actionStatistics": statistics})
