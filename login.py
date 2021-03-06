from instapy import InstaPy
from instapy.util import smart_run
import lib.environments as env

env.config(version="1.02", name="login")

session = InstaPy(**env.arguments())

with smart_run(session):
    env.track_follower_count(session, 3600)
