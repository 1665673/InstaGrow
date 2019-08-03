import time
import datetime
import sys
import signal
from . import environments as env

TASK_ACTION_TIMEOUT = 120


def register_handlers():
    return {
        #
        #   actions
        #
        "quit": quit,
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
#   NOTE about handlers' return value
#
#   for all action handlers:
#       (1) if it RETURNS a value, it has to be either:
#           (a) a boolean value, indicating if action succeeded, or
#           (b) None
#       (2) if it returns a boolean value
#           tasks.py will automatically update statistics according to this value
#       (3) if it doesn't RETURN a value, or returns None
#           this action won't go into statistics
#       (4) if you want to do customized complicated statistics
#           rather than simply a success/fail count automatically handled by tasks.py
#           please RETURN None, then implement the customized logic in the handler
#
#
def quit(session, target):
    message = target
    env.safe_quit(session, message)


def hold_on(session, target):
    seconds = target
    time.sleep(int(seconds))


def self_restart(session, target):
    arguments = target
    env.event("SCRIPT", "SELF-RESTARTING", {"arguments": arguments})
    env.self_restart(arguments)


def self_update(session, target):
    env.event("SCRIPT", "SELF-UPDATING")
    env.self_update()


def follow_user(session, target):
    follow_single_user = sys.modules['instapy.unfollow_util'].follow_user
    success = follow_single_user(session.browser, "profile", session.username, target,
                                 None, session.blacklist, session.logger, session.logfolder)
    # return None if follow-fails happens at the beginning of running a script
    # this will prevent these false-negative fails going into statistics
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
    session.like_by_tags([target], amount=20, interact=False)
    return session.like_img_success


def like_by_location(session, target):
    utc = datetime.datetime.utcnow()
    if 7 <= utc.hour < 15:
        env.info("time is between 00:00 and 07:59 PST, skip this action")
        return
    session.like_by_locations([target], amount=20)
    return session.like_img_success


def comment_by_location(session, target):
    utc = datetime.datetime.utcnow()
    if 7 <= utc.hour < 15:
        env.info("time is between 00:00 and 07:59 PST, skip this action")
        return
    session.comment_by_locations([target], amount=20, skip_top_posts=True)
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
#
#
#
#
#
class TaskActionTimeout(Exception):
    def __init__(self, message=""):
        self.message = message


def task_action_time_out_handler(*av, **kw):
    raise TaskActionTimeout("task action timed out!")


signal.signal(signal.SIGALRM, task_action_time_out_handler)
handlers = register_handlers()


def execute(action_type, target, ready, action):
    warm_up_status = ""
    if hasattr(action, "rate") and action.rate != 1:
        warm_up_status = " (warm-up {:1.2f}x)".format(action.rate)

    current = time.time()
    if current < ready:
        delay = ready - current
        env.log("sleep %1.2fs%s till action (%s, %s) is ready" % (delay, warm_up_status, action_type, target),
                title="TASK ")
        time.sleep(delay)

    env.log("now performing action (%s, %s)" % (action_type, target), title="TASK ")
    session = env.get_session()
    try:
        signal.alarm(TASK_ACTION_TIMEOUT)
        success = handlers[action_type](session, target)
        signal.alarm(0)
        env.do_statistics(action_type, target, success)
    # if any exceptions raised, mark this action fail in statistics
    except Exception as e:
        env.do_statistics(action_type, target, False)
        env.error(action_type, "exception", str(e))
        # especially, if it's a TaskActionTimeout-Exception
        # re-start selenium and re-login
        if isinstance(e, TaskActionTimeout):
            env.event("TASK", "RESTARTING-SELENIUM")
            env.event("SELENIUM", "SESSION-QUITTING", {"proxy": env._proxy_in_use, "signal": "task timed out"})
            session.browser.quit()
            session.set_selenium_local_session()
            session.login()


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
