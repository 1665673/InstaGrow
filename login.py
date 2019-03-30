from instapy import InstaPy
from instapy.util import smart_run
import lib.environments as env

env.config(version="login-ff-1.0", type="login")

session = InstaPy(
    headless_browser=True,
    bypass_suspicious_attempt=True,
    use_firefox=True,
    **env.arguments()
)

with smart_run(session):
    env.report_success(session)
