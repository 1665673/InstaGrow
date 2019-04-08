import time

from instapy import InstaPy
from instapy import smart_run

import lib.environments as env

VERSION = "follow-comment-1.0"
######################################
# configuration
#
# main customization
SLEEP_AFTER_ALL_COMMENT = 240
SLEEP_DELAY = 25

locations = ['6889842/paris-france/', '20188833/manhattan-new-york/', '17326249/moscow-russia/',
             '213385402/london-united-kingdom/', '213163910/sao-paulo-brazil/', '212999109/los-angeles-california/']


# the main function
def main():
    env.config(version=VERSION)

    # get an InstaPy session!
    # set headless_browserTrue to run InstaPy in the background
    session = InstaPy(**env.arguments())

    # run the task
    with smart_run(session):
        env.report_success(session)
        session.set_do_comment(enabled=True, percentage=100)
        session.set_comments(comments=['Very good one', 'This is so Great', 'Really great', 'Awesome', 'Really Cool',
                                       'I like your stuff'])

        while True:

            for location in locations:
                cur = time.time()

                session.comment_by_locations([location], amount=1, skip_top_posts=True)

                env.fetch_task_and_execute()

                env.log(60)
                time.sleep(60)

            env.log(SLEEP_AFTER_ALL_COMMENT)
            time.sleep(SLEEP_AFTER_ALL_COMMENT)
            env.log(time.time() - cur)


# call main function
main()
