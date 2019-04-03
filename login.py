from instapy import InstaPy
from instapy.util import smart_run
import lib.environments as env

env.config(version="login-ff-1.0", name="login")

session = InstaPy(**env.arguments())

with smart_run(session):
    env.report_success(session)
