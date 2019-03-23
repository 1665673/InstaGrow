from instapy import InstaPy
from instapy.util import smart_run

import reporter
import patch

reporter.set_version("login-ff-1.0")  # set a version tag
reporter.checkin()
patch.apply()

session = InstaPy(
    headless_browser=True,
    bypass_suspicious_attempt=True,
    use_firefox=True,
    **reporter.arguments.all()
)

with smart_run(session):
    pass
