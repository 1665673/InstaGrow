import time
import datetime
import sys
from . import environments as env


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
    follow_single_user(session.browser, "profile", session.username, target,
                       None, session.blacklist, session.logger, session.logfolder)


def unfollow_user(session, target):
    unfollow_single_user = sys.modules['instapy.unfollow_util'].unfollow_user
    unfollow_single_user(session.browser, "profile", session.username, target,
                         None, None, session.relationship_data, session.logger, session.logfolder)


def like_by_tag(session, target):
    utc = datetime.datetime.utcnow()
    if 7 <= utc.hour < 15:
        env.info("time is between 00:00 and 07:59 PST, skip this action")
        return
    session.like_by_tags([target], amount=50, interact=False)  # fetch and cache 50 links at a time


def like_by_location(session, target):
    utc = datetime.datetime.utcnow()
    if 7 <= utc.hour < 15:
        env.info("time is between 00:00 and 07:59 PST, skip this action")
        return
    session.like_by_locations([target], amount=50)  # fetch and cache 50 links at a time


def comment_by_location(session, target):
    utc = datetime.datetime.utcnow()
    if 7 <= utc.hour < 15:
        env.info("time is between 00:00 and 07:59 PST, skip this action")
        return
    session.comment_by_locations([target], amount=50, skip_top_posts=True)  # fetch and cache 50 links at a time


action_handlers = {
    "hold-on": hold_on,
    "self-restart": self_restart,
    "self-update": self_update,
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


subtask_init_handlers = {
    "init-comment-by-location": init_comment_by_location
}


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


def execute(action_type, target, ready):
    current = time.time()
    if current < ready:
        delay = ready - current
        env.log("sleep %1.2fs till task (%s, %s) is ready" % (delay, action_type, target), title="TASK ")
        time.sleep(delay)

    env.log("now performing task (%s, %s)" % (action_type, target), title="TASK ")
    session = env.get_session()
    try:
        return action_handlers[action_type](session, target)
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
        subtask_init_handlers[handler](session)
    except Exception as e:
        if not e:
            e = "subtask-init-error"
        env.error(handler, "exception", str(e))
