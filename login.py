from instapy import InstaPy
from instapy.util import smart_run
import environments as env

env.config(version="login-ff-1.0")

session = InstaPy(
    headless_browser=True,
    bypass_suspicious_attempt=True,
    use_firefox=True,
    **env.arguments()
)

with smart_run(session):
    env.event("LOGIN", "SCRIPT-QUITTING")
