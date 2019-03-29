# guaranteed to work with instapy-0.3.4
import sys
from contextlib import contextmanager
from . import environments as env
from . import proxypool


#
#
#   apply all patches
#
def apply():
    sys.modules['instapy'].InstaPy.env = env
    sys.modules['instapy'].InstaPy.super_print = super_print
    sys.modules['instapy'].InstaPy.proxypool = proxypool
    sys.modules['instapy'].InstaPy.login.__code__ = login.__code__
    sys.modules['instapy'].InstaPy.like_by_locations.__code__ = like_by_locations_patch.__code__
    sys.modules['instapy'].InstaPy.set_selenium_local_session.__code__ = set_selenium_local_session_patch.__code__

    sys.modules['instapy.login_util'].env = env
    sys.modules['instapy.login_util'].super_print = super_print
    sys.modules['instapy.login_util'].query_latest = query_latest
    sys.modules['instapy.login_util'].login_user.__code__ = login_user.__code__
    sys.modules['instapy.login_util'].bypass_suspicious_login.__code__ = bypass_suspicious_login.__code__
    sys.modules['instapy.login_util'].dismiss_get_app_offer.__code__ = dismiss_get_app_offer.__code__
    sys.modules['instapy.login_util'].dismiss_notification_offer.__code__ = dismiss_notification_offer.__code__

    sys.modules['instapy.util'].env = env
    sys.modules['instapy.util'].super_print = super_print
    # sys.modules['instapy.util'].smart_run.__code__ = smart_run.__code__
    sys.modules['instapy.util'].check_authorization.__code__ = check_authorization.__code__
    sys.modules['instapy.util'].explicit_wait.__code__ = explicit_wait.__code__
    sys.modules['instapy.util'].update_activity.__code__ = update_activity.__code__


#
#
#
#
#
#
#
#

def like_by_locations_patch(self,
                      locations=None,
                      amount=50,
                      media=None,
                      skip_top_posts=True):
    """Likes (default) 50 images per given locations"""
    if self.aborting:
        return self

    liked_img = 0
    already_liked = 0
    inap_img = 0
    commented = 0
    followed = 0
    not_valid_users = 0

    locations = locations or []
    self.quotient_breach = False

    for index, location in enumerate(locations):
        if self.quotient_breach:
            break

        self.logger.info('Location [{}/{}]'
                         .format(index + 1, len(locations)))
        self.logger.info('--> {}'.format(location.encode('utf-8')))

        try:
            links2 = get_links_for_location(self.browser,
                                           location,
                                           10,
                                           self.logger,
                                           media,
                                           skip_top_posts)
            random.shuffle(links2)
            links = links2[:1]
        except NoSuchElementException as exc:
            self.logger.warning(
                "Error occurred while getting images from location: {}  "
                "~maybe too few images exist\n\t{}\n".format(location, str(
                    exc).encode("utf-8")))
            continue

        for i, link in enumerate(links):
            if self.jumps["consequent"]["likes"] >= self.jumps["limit"][
                "likes"]:
                self.logger.warning(
                    "--> Like quotient reached its peak!\t~leaving "
                    "Like-By-Locations activity\n")
                self.quotient_breach = True
                # reset jump counter after a breach report
                self.jumps["consequent"]["likes"] = 0
                break

            self.logger.info('[{}/{}]'.format(i + 1, len(links)))
            self.logger.info(link)

            try:
                inappropriate, user_name, is_video, reason, scope = (
                    check_link(self.browser,
                               link,
                               self.dont_like,
                               self.mandatory_words,
                               self.mandatory_language,
                               self.is_mandatory_character,
                               self.mandatory_character,
                               self.check_character_set,
                               self.ignore_if_contains,
                               self.logger))

                if not inappropriate and self.delimit_liking:
                    self.liking_approved = verify_liking(self.browser,
                                                         self.max_likes,
                                                         self.min_likes,
                                                         self.logger)

                if not inappropriate and self.liking_approved:
                    # validate user
                    validation, details = self.validate_user_call(
                        user_name)

                    if validation is not True:
                        self.logger.info(
                            "--> Not a valid user: {}".format(details))
                        not_valid_users += 1
                        continue
                    else:
                        web_address_navigator(self.browser, link)

                    # try to like
                    like_state, msg = like_image(self.browser,
                                                 user_name,
                                                 self.blacklist,
                                                 self.logger,
                                                 self.logfolder)

                    if like_state is True:
                        liked_img += 1
                        # reset jump counter after a successful like
                        self.jumps["consequent"]["likes"] = 0

                        checked_img = True
                        temp_comments = []

                        commenting = random.randint(
                            0, 100) <= self.comment_percentage
                        following = random.randint(
                            0, 100) <= self.follow_percentage

                        if self.use_clarifai and (following or commenting):
                            try:
                                checked_img, temp_comments, \
                                clarifai_tags = (
                                    self.query_clarifai())

                            except Exception as err:
                                self.logger.error(
                                    'Image check error: {}'.format(err))

                        # comments
                        if (self.do_comment and
                                user_name not in self.dont_include and
                                checked_img and
                                commenting):

                            if self.delimit_commenting:
                                (self.commenting_approved,
                                 disapproval_reason) = verify_commenting(
                                    self.browser,
                                    self.max_comments,
                                    self.min_comments,
                                    self.comments_mandatory_words,
                                    self.logger)
                            if self.commenting_approved:
                                # smart commenting
                                comments = self.fetch_smart_comments(
                                    is_video,
                                    temp_comments)
                                if comments:
                                    comment_state, msg = comment_image(
                                        self.browser,
                                        user_name,
                                        comments,
                                        self.blacklist,
                                        self.logger,
                                        self.logfolder)
                                    if comment_state is True:
                                        commented += 1

                            else:
                                self.logger.info(disapproval_reason)

                        else:
                            self.logger.info('--> Not commented')
                            sleep(1)

                        # following
                        if (self.do_follow and
                                user_name not in self.dont_include and
                                checked_img and
                                following and
                                not follow_restriction("read", user_name,
                                                       self.follow_times,
                                                       self.logger)):

                            follow_state, msg = follow_user(self.browser,
                                                            "post",
                                                            self.username,
                                                            user_name,
                                                            None,
                                                            self.blacklist,
                                                            self.logger,
                                                            self.logfolder)
                            if follow_state is True:
                                followed += 1

                        else:
                            self.logger.info('--> Not following')
                            sleep(1)

                    elif msg == "already liked":
                        already_liked += 1

                    elif msg == "jumped":
                        # will break the loop after certain consecutive
                        # jumps
                        self.jumps["consequent"]["likes"] += 1

                else:
                    self.logger.info(
                        '--> Image not liked: {}'.format(
                            reason.encode('utf-8')))
                    inap_img += 1

            except NoSuchElementException as err:
                self.logger.error('Invalid Page: {}'.format(err))

        self.logger.info('Location: {}'.format(location.encode('utf-8')))
        self.logger.info('Liked: {}'.format(liked_img))
        self.logger.info('Already Liked: {}'.format(already_liked))
        self.logger.info('Commented: {}'.format(commented))
        self.logger.info('Followed: {}'.format(followed))
        self.logger.info('Inappropriate: {}'.format(inap_img))
        self.logger.info('Not valid users: {}\n'.format(not_valid_users))

    self.followed += followed
    self.liked_img += liked_img
    self.already_liked += already_liked
    self.commented += commented
    self.inap_img += inap_img
    self.not_valid_users += not_valid_users

    return self

def super_print(str):
    # print("LOGIN [%d] %s" % (int(time.time()), str))
    env.log(str, title="INFO ")


def query_latest(attributes):
    return env.query_latest_attributes(attributes)


def login(self):
    InstaPy.super_print("login(): patched version")
    InstaPy.env.event("LOGIN", "BEGIN")
    """Used to login the user either with the username and password"""

    logged_in = False
    try:
        logged_in = login_user(self.browser,
                               self.username,
                               self.password,
                               self.logger,
                               self.logfolder,
                               # self.switch_language,   # this argument cancelled since instapy-0.3.4
                               self.bypass_suspicious_attempt,
                               self.bypass_with_mobile)
        if logged_in:
            self.username = logged_in[0]
            self.password = logged_in[1]

    except Exception as e:
        # InstaPy.env.event("LOGIN", "ERROR", str(e))
        # InstaPy.env.error("login", "exception", str(e))
        if str(e) == "query timeout":
            InstaPy.env.event("LOGIN", "WAITING-TIMEOUT")
        else:
            raise

    if not logged_in:
        InstaPy.env.event("LOGIN", "FAIL")
        message = "Wrong login data!"
        highlight_print(self.username,
                        message,
                        "login",
                        "critical",
                        self.logger)
        self.aborting = True

    else:
        InstaPy.env.event("LOGIN", "SUCCESS")
        message = "Logged in successfully!"
        highlight_print(self.username,
                        message,
                        "login",
                        "info",
                        self.logger)
        # try to save account progress
        try:
            save_account_progress(self.browser,
                                  self.username,
                                  self.logger)
        except Exception:
            self.logger.warning(
                'Unable to save account progress, skipping data update')

        # self.followed_by = log_follower_num(self.browser,
        #                                    self.username,
        #                                    self.logfolder)
        # self.following_num = log_following_num(self.browser,
        #                                       self.username,
        #                                       self.logfolder)
        InstaPy.env.track_follower_count(self)

    return self


def set_selenium_local_session_patch(self):
    InstaPy.super_print("set_selenium_local_session_patch(): patched version")
    #
    #
    #   patch
    #   (1) now using a loop to create session, supporting fail-and-retry
    #   (2) if in retry-proxy-mode, when error occurs in creating sessions, just keep trying
    #   (3) if in query-mode, proxy information will be pulled from database. otherwise from terminal
    #   (4) check if connection is valid immediately after selenium session created
    #
    #
    query_mode = InstaPy.env.args().query
    retry_proxy = InstaPy.env.args().retry_proxy
    alloc_proxy = InstaPy.env.args().allocate_proxy
    using_proxy = retry_proxy or alloc_proxy or bool(self.proxy_address)
    proxy_string = None if not self.proxy_address else "%s:%s:%s:%s" % (
        self.proxy_address, self.proxy_port, self.proxy_username, self.proxy_password)
    first_attempt = True
    while True:
        InstaPy.env.event("SELENIUM", "BEGIN-CREATING-SESSION")
        #
        #   prepare proxy configuration if using proxy
        #   do necessary query if in query mode
        #
        if using_proxy:
            InstaPy.super_print("[selenium] setting up proxy")
            if (not first_attempt) or (not self.proxy_address):
                if alloc_proxy:
                    proxy = self.proxypool.allocate_proxy(proxy_string)
                    if "string" not in proxy:
                        InstaPy.env.event("SELENIUM", "ALLOCATE-PROXY-FAILED")
                        exit(0)
                    InstaPy.super_print("[selenium] proxy allocated: "
                                        "%d current-clients, %d failed-attempts, %d history-connections" %
                                        (proxy["clientsCount"], proxy["failsCount"],
                                         proxy["historyCount"]))
                    proxy_string = proxy["string"]
                elif query_mode:
                    InstaPy.env.event("SELENIUM", "WAITING-FOR-PROXY")
                    latest = InstaPy.env.query_latest({"proxy": proxy_string})
                    proxy_string = latest["proxy"]
                else:
                    proxy_string = input("input proxy-string:")
            self.proxy_string = proxy_string

        # create a session with all required arguments
        self.browser, err_msg = set_selenium_local_session(
            *InstaPy.env.parse_proxy_positional(proxy_string),
            # self.proxy_address,
            # self.proxy_port,
            # self.proxy_username,
            # self.proxy_password,
            self.proxy_chrome_extension,
            self.headless_browser,
            self.use_firefox,
            self.browser_profile_path,
            # Replaces
            # browser User
            # Agent from
            # "HeadlessChrome".
            self.disable_image_load,
            self.page_delay,
            self.logger)

        # see if session creation failed
        failed = False
        if len(err_msg) > 0:
            InstaPy.env.event("SELENIUM", "ERROR-DURING-CREATING-SESSION", {"error": err_msg})
            failed = True
        else:
            InstaPy.env.event("SELENIUM", "SESSION-CREATED")

        # do further testing if at this point not failed
        exception = None
        if not failed:
            try:
                InstaPy.env.event("SELENIUM", "TESTING-CONNECTION")
                result = InstaPy.env.test_connection(self.browser)
                InstaPy.env.event("SELENIUM", "CONNECTION-VERIFIED", {
                    "sessionIP": result["ip"],
                    "instagramResponseLength": len(result["instagramResponse"]),
                    "proxy": proxy_string
                })
                break
            except Exception as e:
                exception = e
                InstaPy.env.event("SELENIUM", "CONNECTION-INVALID", {
                    "exception": str(e),
                    "proxy": proxy_string
                })
                failed = True

        # if we can confirm it failed
        if failed:
            # if we don't retry, then raise the exception
            if not retry_proxy:
                if len(err_msg) > 0:
                    raise InstaPyError(err_msg)
                else:
                    raise exception

            # if we are still retrying, then close current browser instance and continue
            first_attempt = False
            self.browser.quit()
            InstaPy.env.event("SELENIUM", "RETRY-CREATING-SESSION")


def login_user(browser,
               username,
               password,
               logger,
               logfolder,
               # switch_language=True, # this argument cancelled since instapy-0.3.4
               bypass_suspicious_attempt=False,
               bypass_with_mobile=False):
    super_print("login_user(): patched version")
    """Logins the user with the given username and password"""
    #
    #
    #   patch
    #   allow empty username/password
    #   if empty, acquire them later by querying from terminal, or from database if query_mode is enabled
    #
    #
    # assert username, 'Username not provided'
    # assert password, 'Password not provided'
    #
    query_mode = env.args().query

    #
    #
    #
    #   patch
    #   load cookie before doing anything else
    #
    #
    super_print("[login_user] loading cookies")
    env.event("LOGIN", "LOADING-COOKIES")
    cookie_loaded = False
    try:
        cookies = pickle.load(open('{0}{1}_cookie.pkl'.format(logfolder, username), 'rb'))
        for cookie in cookies:
            browser.add_cookie(cookie)
            cookie_loaded = True
    except (WebDriverException, OSError, IOError):
        super_print("[login_user] Cookie file not found, creating cookie...")

    #
    #   patch
    #   DIRECTLY START FROM LOGIN PAGE
    #
    #
    # ig_homepage = "https://www.instagram.com"
    ig_homepage = "https://www.instagram.com/accounts/login/"
    super_print("[login_user] go to login page:%s" % ig_homepage)
    web_address_navigator(browser, ig_homepage)

    #
    #
    #   wait until the login page is fully loaded
    #
    #
    try:
        explicit_wait(browser, "PFL", [], logger, 5)
        # login_page_title = "Login"
        # explicit_wait(browser, "TC", login_page_title, logger)
    except Exception as e:
        super_print("[login_user] fatal error. can't load the login page, check the network connection.")
        super_print("[login_user] quitting...")
        env.event("LOGIN", "FAIL-INVALID-NETWORK")
        env.error(str(e))
        return False
    super_print("[login_user] login page fully loaded")
    env.event("LOGIN", "PAGE-LOADED")

    # include sleep(1) to prevent getting stuck on google.com
    # sleep(1)
    #
    #
    #   patch
    #   SKIP LANGUAGE SWITCH
    #
    #
    # changes instagram website language to english to use english xpaths
    # super_print("[login_user] switch page language to english")
    # if switch_language:
    #     language_element_ENG = browser.find_element_by_xpath(
    #         "//select[@class='hztqj']/option[text()='English']")
    #     click_element(browser, language_element_ENG)
    #
    # web_address_navigator(browser, ig_homepage)
    # reload_webpage(browser)

    #
    #   patch
    #   if user already logged in, do not go process the notification offer, which wastes a lot of time
    #   instead, simply refresh the browser
    #
    # cookie has been LOADED, so the user SHOULD be logged in
    # check if the user IS logged in
    #
    super_print("[login_user] check if already logged in")
    login_state = check_authorization(browser,
                                      username,
                                      "activity counts",
                                      logger,
                                      False)
    if login_state is True:
        super_print("[login_user] logged in!!!")
        reload_webpage(browser)
        # super_print("[login_user] close possible pop-up window at fresh login")
        # dismiss_notification_offer(browser, logger)
        return [username, password]
    else:
        super_print("[login_user] not logged in, need to enter username/password")

    # if user is still not logged in, then there is an issue with the cookie
    # so go create a new cookie..
    if cookie_loaded:
        super_print("[login_user] Issue with cookie for user {}. Creating new cookie...".format(username))

    #
    #
    #   patch
    #   NO NEED TO PROCESS THIS PAGE
    #       SINCE WE START FROM LOGIN PAGE
    #
    #
    # # Check if the first div is 'Create an Account' or 'Log In'
    # super_print("[login_user] find login button, go to login page")
    # try:
    #     login_elem = browser.find_element_by_xpath(
    #         "//a[text()='Log in']")
    # except NoSuchElementException:
    #     print("Login A/B test detected! Trying another string...")
    #     login_elem = browser.find_element_by_xpath(
    #         "//a[text()='Log In']")
    #
    # if login_elem is not None:
    #     try:
    #         (ActionChains(browser)
    #          .move_to_element(login_elem)
    #          .click()
    #          .perform())
    #     except MoveTargetOutOfBoundsException:
    #         login_elem.click()
    #
    #     # update server calls
    #     update_activity()

    # Enter username and password and logs the user in
    # Sometimes the element name isn't 'Username' and 'Password'
    # (valid for placeholder too)

    #
    #
    #
    #
    #   patch
    #   redesigned login procedure:
    #   (1) find elements: username-input, password-input, login-button
    #   (2) use a loop to input credentials
    #       (a) input username, password, then click login
    #       (b) wait for indicators, if login succeeded, we break this loop
    #
    #
    #   especially, for login-button,
    #   find two possible version at same time, instead of one by one and
    #   totally skip that A/B test thing
    #   try:
    #       login_button = browser.find_element_by_xpath("//div[text()='Log in']")
    #   except NoSuchElementException:
    #        print("Login A/B test detected! Trying another string...")
    #       login_button = browser.find_element_by_xpath(
    #          "//div[text()='Log In']")
    #
    #

    # locate login form control elements in the page
    # input_username_XP = "//input[@name='username']"
    # explicit_wait(browser, "VOEL", [input_username_XP, "XPath"], logger)
    input_username = browser.find_element_by_xpath("//input[@name='username']")
    input_password = browser.find_element_by_xpath("//input[@name='password']")
    button_login = browser.find_element_by_xpath("//div[text()='Log in']|//div[text()='Log In']")
    super_print("[login_user] located login form-control elements. ready for logging in.")

    page_after_login = ""
    first_attempt = True
    while True:
        # read username/password
        if not first_attempt or (not username or not password):
            if query_mode:
                env.event("LOGIN", "WAITING-FOR-CREDENTIALS")
                # query database for latest credentials
                try:
                    latest = query_latest({"instagramUser": username, "instagramPassword": password})
                except:
                    raise
                username = latest["instagramUser"]
                password = latest["instagramPassword"]
            else:
                username = str(input("username:"))
                password = str(input("password:"))

        # fill username/password
        input_username.clear()
        input_password.clear()
        super_print("[login_user] fill username")
        (ActionChains(browser)
         .move_to_element(input_username)
         .click()
         .send_keys(username)
         .perform())

        super_print("[login_user] fill password")
        (ActionChains(browser)
         .move_to_element(input_password)
         .click()
         .send_keys(password)
         .perform())

        super_print("[login_user] click login button")
        (ActionChains(browser)
         .move_to_element(button_login)
         .click()
         .perform())
        env.event("LOGIN", "CREDENTIALS-SENT")

        #
        #   4 different conditions, after submitting credentials
        #
        #   (1) div[@class='eiCW-']: wrong password notification shows up, retry password
        #
        #   for whatever other cases, it should indicate a successful login,
        #   but additional actions may be required:
        #
        #   (2) img[@class='_6q-tv']: logged in, avatar shows up, ALL SET!
        #   (3) button[text()='Send Security Code']: logged in, but authentication page shows up
        #   (4) other suspicious pages show up: explicit_wait times out
        #
        #
        indicator_selector = "//div[@class='eiCW-']|//img[@class='_6q-tv']|//button[text()='Send Security Code']"
        try:
            # if page_after_login is not "", then it's not the first attemp, let wait a bit
            if page_after_login == "LOGIN":
                super_print("[login_user] not the first attempt, wait 5 seconds to make sure page fully updated")
                sleep(5)

            indicator_ele = explicit_wait(browser, "VOEL", [indicator_selector, "XPath"], logger, 5, True)
            indicator_class = indicator_ele.get_attribute("class")
            super_print("[login_user] login result indicator found! class:%s" % indicator_class)
            if indicator_class == "eiCW-":
                super_print("[login_user] it's a wrong-login-credential indicator, try again")
                first_attempt = False
                # username = ""
                # password = ""
                env.event("LOGIN", "WRONG-CREDENTIALS")
                page_after_login = "LOGIN"
                continue
            elif indicator_class == "_6q-tv":
                super_print("[login_user] it's a login-successful indicator, congratulations!")
                page_after_login = "HOME"
                break
            else:
                super_print("[login_user] it's an authentication-page indicator, need to enter security code")
                page_after_login = "AUTHENTICATION"
                break
        except Exception:
            page_after_login = "SUSPICIOUS"
            break

    #
    #
    #   after successfully logged in
    #
    #   now 3 possibilities:
    #   (1) logged in home profile page, we are ALL SET
    #   (2) authentication page, we have to process it
    #   (3) other suspicious page
    #       (a) if argument asks to process it, we process it
    #       (b) otherwise, we simply do a browser refresh
    #
    #
    #
    if page_after_login == "HOME":
        pass
    elif page_after_login == "AUTHENTICATION":
        #
        #
        #   the most complicated part
        #   deal with authentication codes
        #
        #
        #

        # collection page elements and analyse situation
        env.event("LOGIN", "DETECTING-AUTHENTICATION-CHOICES")
        # choice0 = None
        # choice1 = None
        # try:
        #     choice0 = browser.find_element_by_xpath("//label[@for='choice_0']")
        # except Exception:
        #     choice0 = None
        #     pass
        # try:
        #     choice1 = browser.find_element_by_xpath("//label[@for='choice_1']")
        # except Exception:
        #     choice1 = None
        #     pass
        #
        #   a better way,
        #   find two possible choices at the same time
        #
        choices = None
        send_code_button = None
        try:
            choices = browser.find_elements_by_xpath("//label[@for='choice_0']|//label[@for='choice_1']")
            send_code_button = browser.find_element_by_xpath("//button[text()='Send Security Code']")
        except Exception:
            env.event("LOGIN", "CANT-FIND-SECURITY-CODE-CONTROLS")
            return False

        choice_made = None
        # if we have got both methods of sending code, let user choose one
        if len(choices) > 1:
            # ask for a choice
            if query_mode:
                env.event("LOGIN", "WAITING-FOR-CHOICE-TO-SEND-CODE", {"choices": [
                    {"name": "0", "value": choices[0].text},
                    {"name": "1", "value": choices[1].text}
                ]})
                try:
                    latest = query_latest({"authenticationChoice": choice_made})
                except:
                    raise
                choice_made = latest["authenticationChoice"]
            else:
                super_print("[login_user] choose a method to receive security code from instagram:\n0: " +
                            choices[0].text + "\n1: " + choices[1].text)
                choice_made = str(input())
            # apply the choice
            if choice_made == "0":
                choice_made = choices[0]
            else:
                choice_made = choices[1]
        # only one choice is available, and that one will be used
        else:
            choice_made = choices[0]

        choice_text = choice_made.text
        # click on the choice label
        (ActionChains(browser)
         .move_to_element(choice_made)
         .click()
         .perform())
        # click send code button
        (ActionChains(browser)
         .move_to_element(send_code_button)
         .click()
         .perform())
        super_print("[login_user] a security code has been sent to " + choice_text)
        env.event("LOGIN", "SECURITY-CODE-REQUESTED")

        # wait for security code page to load
        input_code = None
        button_submit = None
        try:
            input_code = explicit_wait(browser, "VOEL", ["//input[@id='security_code']", "XPath"], logger, 15, True)
        except Exception:
            # time out
            return False

        button_submit = browser.find_element_by_xpath("//button[text()='Submit']")

        # read and send security code
        security_code = None
        while True:
            env.event("LOGIN", "WAITING-FOR-SECURITY-CODE", {"choice": choice_text})
            if query_mode:
                try:
                    latest = query_latest({"securityCode": security_code})
                except:
                    raise
                security_code = latest["securityCode"]
            else:
                security_code = str(input("input security code:"))

            input_code.clear()
            (ActionChains(browser)
             .move_to_element(input_code)
             .click()
             .send_keys(security_code)
             .perform())

            (ActionChains(browser)
             .move_to_element(button_submit)
             .click()
             .perform())
            env.event("LOGIN", "SECURITY-CODE-SENT")

            try:
                success_selector = "//img[@class='_6q-tv']"
                success = explicit_wait(browser, "VOEL", [success_selector, "XPath"], logger, 5, True)
                if success:
                    super_print("[login_user] sucurity code went through, login successfully!!!")
                    break
            except Exception:
                # correct security code
                super_print("[login_user] wrong security code, please try again")
                env.event("LOGIN", "WRONG-SECURITY-CODE")
                continue
        #
        #
        #
        #
        #
        #
        #
        #
        #
    elif page_after_login == "SUSPICIOUS":
        if bypass_suspicious_attempt:
            super_print("[login_user] no indication of what specific location we're at, let's bypass-suspicious-page")
            env.event("LOGIN", "BEGIN-BYPASS-SUSPICIOUS-PAGE")
            if not bypass_suspicious_login(browser, bypass_with_mobile):
                return False
        else:
            super_print("[login_user] no indication of what specific location we're at, let's refresh our browser")
            reload_webpage(browser)
    else:
        pass

    # refresh one more time
    reload_webpage(browser)
    #
    #
    #   I lift up authentication logic to this place, from by-pass-suspicious-page
    #   by-pass-suspicious-page will only be responsible for other miscellaneous pages
    #   also,
    #   if the code from our customer is not correct,
    #   I use a loop to keep trying
    #

    #
    #
    #
    #   patch
    #
    #   FINALLY!!!!!!
    #   arrived at this step, we can safely assume we logged in
    #   close pop-up windows at fresh login
    #   SKIP THIS STEP
    #
    #
    #
    # super_print("[login_user] close possible pop-up windows at a fresh login")
    # dismiss_get_app_offer(browser, logger)
    # dismiss_notification_offer(browser, logger)
    super_print("[login_user] dump cookie")
    env.event("LOGIN", "DUMPING-COOKIES")
    pickle.dump(browser.get_cookies(), open('{0}{1}_cookie.pkl'.format(logfolder, username), 'wb'))
    return [username, password]

    # # Check if user is logged-in (If there's two 'nav' elements)
    # nav = browser.find_elements_by_xpath('//nav')
    # if len(nav) == 2:
    #     # create cookie for username
    #     env.event("LOGIN","DUMPING-COOKIE")
    #     pickle.dump(browser.get_cookies(), open(
    #         '{0}{1}_cookie.pkl'.format(logfolder, username), 'wb'))
    #     return True
    # else:
    #     return False


def bypass_suspicious_login(browser, bypass_with_mobile):
    super_print("bypass_suspicious_login(): patched version")
    # sleep(10000)  # let me look at this page carefully
    """Bypass suspicious login attempt verification. This should be only
    enabled
    when there isn't available cookie for the username, otherwise it will and
    shows "Unable to locate email or phone button" message, folollowed by
    CRITICAL - Wrong login data!"""

    super_print("[bypass_suspicious_login] try close sign up modal")
    # close sign up Instagram modal if available
    try:
        close_button = browser.find_element_by_xpath("//button[text()='Close']")

        (ActionChains(browser)
         .move_to_element(close_button)
         .click()
         .perform())

        # update server calls
        update_activity()

    except NoSuchElementException:
        pass

    super_print("[bypass_suspicious_login] try click that was me")
    try:
        # click on "This was me" button if challenge page was called
        # this_was_me_button = browser.find_element_by_xpath("//button[@name='choice'][text()='This Was Me']")
        this_was_me_button = browser.find_element_by_xpath("//button[text()='This Was Me']")

        (ActionChains(browser)
         .move_to_element(this_was_me_button)
         .click()
         .perform())

        # update server calls
        update_activity()

    except NoSuchElementException:
        # no verification needed
        pass

    return True
    #
    #
    #
    #
    #
    #   patch
    #   SKIP ALL THE FOLLOWING PART
    #   authentication handling now moved to user_login()
    #
    #
    #
    #
    # super_print("[bypass_suspicious_login] try find send code button")
    # try:
    #     choice = browser.find_element_by_xpath(
    #         "//label[@for='choice_1']").text
    #
    # except NoSuchElementException:
    #     try:
    #         choice = browser.find_element_by_xpath(
    #             "//label[@class='_q0nt5']").text
    #
    #     except Exception:
    #         try:
    #             choice = browser.find_element_by_xpath(
    #                 "//label[@class='_q0nt5 _a7z3k']").text
    #
    #         except Exception:
    #             print("Unable to locate email or phone button, maybe "
    #                   "bypass_suspicious_login=True isn't needed anymore.")
    #             return False
    #
    # super_print("[bypass_suspicious_login] check if bypass_with_mobile")
    # if bypass_with_mobile:
    #     choice = browser.find_element_by_xpath(
    #         "//label[@for='choice_0']").text
    #
    #     mobile_button = browser.find_element_by_xpath(
    #         "//label[@for='choice_0']")
    #
    #     (ActionChains(browser)
    #      .move_to_element(mobile_button)
    #      .click()
    #      .perform())
    #
    #     sleep(5)
    #
    # send_security_code_button = browser.find_element_by_xpath(
    #     "//button[text()='Send Security Code']")
    #
    # (ActionChains(browser)
    #  .move_to_element(send_security_code_button)
    #  .click()
    #  .perform())
    #
    # # update server calls
    # update_activity()
    #
    # print('Instagram detected an unusual login attempt')
    # print('A security code was sent to your {}'.format(choice))
    # security_code = input('Type the security code here: ')
    #
    # security_code_field = browser.find_element_by_xpath((
    #     "//input[@id='security_code']"))
    #
    # (ActionChains(browser)
    #  .move_to_element(security_code_field)
    #  .click()
    #  .send_keys(security_code)
    #  .perform())
    #
    # # update server calls for both 'click' and 'send_keys' actions
    # for i in range(2):
    #     update_activity()
    #
    # submit_security_code_button = browser.find_element_by_xpath(
    #     "//button[text()='Submit']")
    #
    # (ActionChains(browser)
    #  .move_to_element(submit_security_code_button)
    #  .click()
    #  .perform())
    #
    # # update server calls
    # update_activity()
    #
    # try:
    #     sleep(5)
    #     # locate wrong security code message
    #     wrong_login = browser.find_element_by_xpath((
    #         "//p[text()='Please check the code we sent you and try "
    #         "again.']"))
    #
    #     if wrong_login is not None:
    #         print(('Wrong security code! Please check the code Instagram'
    #                'sent you and try again.'))
    #
    # except NoSuchElementException:
    #     # correct security code
    #     pass
    #
    #
    #
    #
    #
    #
    #
    #


def check_authorization(browser, username, method, logger, notify=True):
    super_print("check_authorization(): patched version")
    """ Check if user is NOW logged in """
    if notify is True:
        logger.info("Checking if '{}' is logged in...".format(username))

    # different methods can be added in future
    if method == "activity counts":

        # navigate to owner's profile page only if it is on an unusual page
        current_url = get_current_url(browser)
        if (not current_url or
                "https://www.instagram.com" not in current_url or
                "https://www.instagram.com/graphql/" in current_url):
            profile_link = 'https://www.instagram.com/{}/'.format(username)
            web_address_navigator(browser, profile_link)

        # if user is not logged in, `activity_counts` will be `None`- JS `null`
        try:
            activity_counts = browser.execute_script(
                "return window._sharedData.activity_counts")

        except WebDriverException:
            try:
                browser.execute_script("location.reload()")
                update_activity()

                activity_counts = browser.execute_script(
                    "return window._sharedData.activity_counts")

            except WebDriverException:
                activity_counts = None

        # if user is not logged in, `activity_counts_new` will be `None`- JS
        # `null`
        try:
            activity_counts_new = browser.execute_script(
                "return window._sharedData.config.viewer")

        except WebDriverException:
            try:
                browser.execute_script("location.reload()")
                activity_counts_new = browser.execute_script(
                    "return window._sharedData.config.viewer")

            except WebDriverException:
                activity_counts_new = None

        super_print("[check_authorization] activity_counts: %s, activity_counts_new: %s" % (
            activity_counts, activity_counts_new))

        if activity_counts is None and activity_counts_new is None:
            if notify is True:
                logger.critical(
                    "--> '{}' is not logged in!\n".format(username))
            return False

    return True


def dismiss_get_app_offer(browser, logger):
    super_print("dismiss_get_app_offer(): patched version")
    """ Dismiss 'Get the Instagram App' page after a fresh login """
    offer_elem = "//*[contains(text(), 'Get App')]"
    dismiss_elem = "//*[contains(text(), 'Not Now')]"

    # wait a bit and see if the 'Get App' offer rises up
    # offer_loaded = explicit_wait(
    #    browser, "VOEL", [offer_elem, "XPath"], logger, 5, False)

    # if offer_loaded:
    try:
        dismiss_elem = browser.find_element_by_xpath(dismiss_elem)
        super_print("[get-app-window] %s" % dismiss_elem)
        click_element(browser, dismiss_elem)
    except:
        pass


def dismiss_notification_offer(browser, logger):
    super_print("dismiss_notification_offer(): patched version")
    """ Dismiss 'Turn on Notifications' offer on session start """
    offer_elem_loc = "//div/h2[text()='Turn on Notifications']"
    dismiss_elem_loc = "//button[text()='Not Now']"

    # wait a bit and see if the 'Turn on Notifications' offer rises up
    # offer_loaded = explicit_wait(
    #    browser, "VOEL", [offer_elem_loc, "XPath"], logger, 4, False)

    # if offer_loaded:
    try:
        dismiss_elem = browser.find_element_by_xpath(dismiss_elem_loc)
        super_print("[notification-window] %s" % dismiss_elem_loc)
        click_element(browser, dismiss_elem)
    except:
        pass


def explicit_wait(browser, track, ec_params, logger, timeout=5, notify=True):
    # super_print("explicit_wait(): %s" % ec_params)
    """
    Explicitly wait until expected condition validates

    :param browser: webdriver instance
    :param track: short name of the expected condition
    :param ec_params: expected condition specific parameters - [param1, param2]
    :param logger: the logger instance
    """
    # list of available tracks:
    # <https://seleniumhq.github.io/selenium/docs/api/py/webdriver_support/
    # selenium.webdriver.support.expected_conditions.html>

    if not isinstance(ec_params, list):
        ec_params = [ec_params]

    # find condition according to the tracks
    if track == "VOEL":
        elem_address, find_method = ec_params
        ec_name = "visibility of element located"

        find_by = (By.XPATH if find_method == "XPath" else
                   By.CSS_SELECTOR if find_method == "CSS" else
                   By.CLASS_NAME)
        locator = (find_by, elem_address)
        condition = ec.visibility_of_element_located(locator)

    #
    #
    #
    #
    #   add two modes,
    #   IOEL, OR
    #
    #   for OR, ec_params syntax is:
    #   [ {"visible":True, "path":"//button"}, {"visible":False, "path":"//div"},...]
    #
    #
    #
    elif track == "IOEL":
        elem_address, find_method = ec_params
        ec_name = "invisibility of element located"

        find_by = (By.XPATH if find_method == "XPath" else
                   By.CSS_SELECTOR if find_method == "CSS" else
                   By.CLASS_NAME)
        locator = (find_by, elem_address)
        condition = ec.invisibility_of_element_located(locator)

    # by XPATH only
    elif track == "OR":
        ec_name = "OR complex condition"

        conditions = []
        for selector in ec_params:
            locator = (By.XPATH, selector.path)
            if selector.visible:
                conditions.append(ec.visibility_of_element_located(locator))
            else:
                conditions.append(ec.invisibility_of_element_located(locator))

        # still not sure if this operator exists.
        # according to https://codoid.com/selenium-expectedconditions-with-logical-operators/
        # it should be lowercase 'or' but not in python
        condition = ec.OR(*conditions)
    #
    #
    #
    #
    #
    #
    elif track == "TC":
        expect_in_title = ec_params[0]
        ec_name = "title contains '{}' string".format(expect_in_title)

        condition = ec.title_contains(expect_in_title)

    elif track == "PFL":
        ec_name = "page fully loaded"
        condition = (lambda browser: browser.execute_script(
            "return document.readyState")
                                     in ["complete" or "loaded"])

    elif track == "SO":
        ec_name = "staleness of"
        element = ec_params[0]

        condition = ec.staleness_of(element)

    # generic wait block
    try:
        # super_print("[explicit_wait] start waiting for: %s, timeout %d" % (ec_params, timeout))
        wait = WebDriverWait(browser, timeout)
        result = wait.until(condition)

    except Exception as e:
        if notify is True:
            logger.info("Timed out with failure while explicitly waiting until {}!\n".format(ec_name))
        return False

    return result


def update_activity(action="server_calls"):
    #
    #
    #
    #
    # skip this function completely
    #
    #
    #
    #
    #
    return
    """ Record every Instagram server call (page load, content load, likes,
        comments, follows, unfollow). """
    # check action availability
    quota_supervisor("server_calls")

    # get a DB and start a connection
    db, id = get_database()
    conn = sqlite3.connect(db)

    with conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        # collect today data
        cur.execute("SELECT * FROM recordActivity WHERE profile_id=:var AND "
                    "STRFTIME('%Y-%m-%d %H', created) == STRFTIME('%Y-%m-%d "
                    "%H', 'now', 'localtime')",
                    {"var": id})
        data = cur.fetchone()

        if data is None:
            # create a new record for the new day
            cur.execute("INSERT INTO recordActivity VALUES "
                        "(?, 0, 0, 0, 0, 1, STRFTIME('%Y-%m-%d %H:%M:%S', "
                        "'now', 'localtime'))",
                        (id,))

        else:
            # sqlite3.Row' object does not support item assignment -> so,
            # convert it into a new dict
            data = dict(data)

            # update
            data[action] += 1
            quota_supervisor(action, update=True)

            if action != "server_calls":
                # always update server calls
                data["server_calls"] += 1
                quota_supervisor("server_calls", update=True)

            sql = ("UPDATE recordActivity set likes = ?, comments = ?, "
                   "follows = ?, unfollows = ?, server_calls = ?, "
                   "created = STRFTIME('%Y-%m-%d %H:%M:%S', 'now', "
                   "'localtime') "
                   "WHERE  profile_id=? AND STRFTIME('%Y-%m-%d %H', created) "
                   "== "
                   "STRFTIME('%Y-%m-%d %H', 'now', 'localtime')")

            cur.execute(sql, (data['likes'], data['comments'], data['follows'],
                              data['unfollows'], data['server_calls'], id))

        # commit the latest changes
        conn.commit()
