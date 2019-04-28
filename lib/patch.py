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
    sys.modules['instapy'].InstaPy.end.__code__ = end.__code__
    sys.modules['instapy'].InstaPy.login.__code__ = login.__code__
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
    sys.modules['instapy.util'].parse_cli_args.__code__ = parse_cli_args.__code__


#
#
#
#
#
#
#
#


def super_print(str):
    # print("LOGIN [%d] %s" % (int(time.time()), str))
    env.log(str, title="INFO ")


def query_latest(attributes):
    return env.query_latest_attributes(attributes)


def end(self, threaded_session=False):
    InstaPy.super_print("end(): patched version")
    InstaPy.super_print("[end] script is quitting")
    InstaPy.env.event("SESSION", "SCRIPT-QUITTING", {"proxy": self.proxy_string})

    """Closes the current session"""
    Settings.InstaPy_is_running = False
    close_browser(self.browser, threaded_session, self.logger)

    with interruption_handler():
        # close virtual display
        if self.nogui:
            self.display.stop()

        # write useful information
        # dump_follow_restriction(self.username,
        #                         self.logger,
        #                         self.logfolder)
        # dump_record_activity(self.username,
        #                      self.logger,
        #                      self.logfolder)

        # with open('{}followed.txt'.format(self.logfolder), 'w') \
        #        as followFile:
        #    followFile.write(str(self.followed))

        # output live stats before leaving
        self.live_report()

        message = "Session ended!"
        highlight_print(self.username, message, "end", "info", self.logger)
        print("\n\n")


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
            #
            #   synchronize user information in InstaPy object
            #
            self.username = logged_in[0]
            self.password = logged_in[1]
            self.logger = self.logger = self.get_instapy_logger(self.show_logs)

    except Exception as e:
        # InstaPy.env.event("LOGIN", "ERROR", str(e))
        # InstaPy.env.error("login", "exception", str(e))
        if str(e) == "query timeout":
            InstaPy.env.event("LOGIN", "WAITING-TIMEOUT")
        else:
            InstaPy.env.error("LOGIN", "exception", str(e))

    if not logged_in:
        InstaPy.env.event("LOGIN", "FAIL")
        message = "Wrong login data!"
        highlight_print(self.username,
                        message,
                        "login",
                        "critical",
                        self.logger)
        # self.aborting = True
        InstaPy.env.safe_quit(self)

    else:
        InstaPy.env.event("LOGIN", "SUCCESS")
        message = "Login success! synchronizing status with server..."
        highlight_print(self.username,
                        message,
                        "login",
                        "info",
                        self.logger)

        # try to save account progress
        # try:
        #     save_account_progress(self.browser,
        #                           self.username,
        #                           self.logger)
        # except Exception:
        #     self.logger.warning(
        #         'Unable to save account progress, skipping data update')

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
    retry_proxy = InstaPy.env.args().retry_proxy == "on"
    alloc_proxy = InstaPy.env.args().allocate_proxy

    proxy_string = None if not self.proxy_address else "%s:%s:%s:%s" % (
        self.proxy_address, self.proxy_port, self.proxy_username, self.proxy_password)
    self.proxy_string = None
    first_attempt = True
    while True:
        InstaPy.env.event("SELENIUM", "BEGIN-CREATING-SESSION")
        #
        #   prepare proxy configuration if using proxy
        #   do necessary query if in query mode
        #
        using_proxy = bool(alloc_proxy) or bool(self.proxy_address) or (retry_proxy and not first_attempt)
        if using_proxy:
            InstaPy.super_print("[selenium] setting up proxy")
            if (not first_attempt) or (not self.proxy_address):
                if alloc_proxy is not None:
                    group = alloc_proxy[0]
                    tag = alloc_proxy[1]
                    proxy = self.proxypool.allocate_proxy(group, tag, proxy_string)
                    if "string" not in proxy:
                        InstaPy.env.event("SELENIUM", "ALLOCATE-PROXY-FAILED")
                        exit(0)
                    InstaPy.super_print("[selenium] proxy allocated:\n%s\n"
                                        "%d current-clients, %d failed-attempts, %d history-connections" %
                                        (proxy["string"], proxy["clientsCount"],
                                         proxy["failsCount"], proxy["historyCount"]))
                    proxy_string = proxy["string"]
                elif query_mode:
                    InstaPy.env.event("SELENIUM", "WAITING-FOR-PROXY")
                    latest = InstaPy.env.query_latest({"proxy": proxy_string})
                    proxy_string = latest["proxy"]
                else:
                    proxy_string = input("input proxy-string:")
            self.proxy_string = proxy_string

        # create a session with all required arguments
        failed = False
        exception = None
        err_msg = ''
        try:
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
        except Exception as e:
            exception = e
            failed = True

        if len(err_msg) > 0:
            failed = True

        # see if session creation failed
        if failed:
            InstaPy.env.event("SELENIUM", "ERROR-DURING-CREATING-SESSION", {"error": err_msg})
        else:
            InstaPy.env.event("SELENIUM", "SESSION-CREATED")

        # do further testing if at this point not failed
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
    no_cookies = env.args().no_cookies

    #
    #
    #
    #   patch
    #   load cookie before doing anything else
    #
    #
    cookie_loaded = False
    if not no_cookies:
        super_print("[login_user] loading cookies")
        env.event("LOGIN", "LOADING-COOKIES")
        try:
            if env._pulled_cookies:
                cookies = env._pulled_cookies
                env.info("cookies restored from server")
            else:
                cookies = pickle.load(open('{0}{1}_cookie.pkl'.format(logfolder, username), 'rb'))
            for cookie in cookies:
                browser.add_cookie(cookie)
                cookie_loaded = True
        except (WebDriverException, OSError, IOError):
            super_print("[login_user] Cookie file not found, creating cookie...")
    else:
        super_print("[login_user] ignored previous cookies")

    #
    #   patch
    #   DIRECTLY START FROM LOGIN PAGE
    #
    #

    # ---------------------------------2019-04-27----------------------------------------
    #   new logic: we directly used the login page to verify connection
    #   so, as long as our code arrives here, we are already in the login page
    #   just go ahead1
    #
    # ig_homepage = "https://www.instagram.com"
    # ig_homepage = "https://www.instagram.com/accounts/login/"
    # super_print("[login_user] go to login page:%s" % ig_homepage)
    # web_address_navigator(browser, ig_homepage)
    # ------------------------------------------------------------------------------------

    #
    #
    #   wait until the login page is fully loaded
    #
    #

    # ---------------------------------2019-04-27----------------------------------------
    # try:
    #     explicit_wait(browser, "PFL", [], logger, 5)
    #     # login_page_title = "Login"
    #     # explicit_wait(browser, "TC", login_page_title, logger)
    # except Exception as e:
    #     super_print("[login_user] fatal error. can't load the login page, check the network connection.")
    #     super_print("[login_user] quitting...")
    #     env.event("LOGIN", "FAIL-INVALID-NETWORK")
    #     env.error(str(e))
    #     return False
    # super_print("[login_user] login page fully loaded")
    # env.event("LOGIN", "PAGE-LOADED")
    # ------------------------------------------------------------------------------------

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
        # reload_webpage(browser)
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

    retry_credentials = env.args().retry_credentials == "on"
    page_after_login = ""
    first_attempt = True
    while True:
        # otherwise, read new username/password
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

        # erase first_attempt flag
        first_attempt = False

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
        suspicious_selector = "//button[text()='Close']|//button[text()='This Was Me']"
        phone_selector = "//h2[text()='Add Your Phone Number']"
        block_selector = "//input[@name='fullName']"
        indicator_selector = indicator_selector + "|" + suspicious_selector + \
                             "|" + phone_selector + "|" + block_selector

        try:
            # if page_after_login is not "", then it's not the first attemp, let wait a bit
            if page_after_login == "LOGIN":
                super_print("[login_user] not the first attempt, wait 3 seconds until page fully updated")
                sleep(3)

            indicator_ele = explicit_wait(browser, "VOEL", [indicator_selector, "XPath"], logger, 5, True)
            indicator_class = indicator_ele.get_attribute("class")
            indicator_text = indicator_ele.text

            super_print("[login_user] login result indicator found! class:%s, text:%s"
                        % (indicator_class, indicator_text))
            if indicator_class == "eiCW-":
                # if arguments says do not retry, then we quit
                if not retry_credentials:
                    return None
                # otherwise, we keep trying new credentials
                super_print("[login_user] it's a wrong-login-credential indicator, try again")
                # username = ""
                # password = ""
                env.event("LOGIN", "WRONG-CREDENTIALS")
                page_after_login = "LOGIN"
                continue
            elif indicator_class == "_6q-tv":
                super_print("[login_user] it's a login-successful indicator, congratulations!")
                page_after_login = "HOME"
                break
            elif indicator_text == "Send Security Code":
                super_print("[login_user] it's an authentication-page indicator, need to enter security code")
                page_after_login = "AUTHENTICATION"
                break
            elif indicator_ele.get_attribute("name") == "fullName":
                super_print("[login_user] entered into the blocked version of login page. login failed")
                return False
            else:
                super_print("[login_user] it's an suspicious-page indicator, may simply skip...")
                page_after_login = "SUSPICIOUS"
                break
        except Exception:
            super_print("[login_user] timed out, try again...")
            page_after_login = "UNKNOWN"
            continue

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
        newcode_link = None
        try:
            input_code = explicit_wait(browser, "VOEL", ["//input[@id='security_code']", "XPath"], logger, 15, True)
            button_submit = browser.find_element_by_xpath("//button[text()='Submit']")
            newcode_link = browser.find_element_by_xpath("//a[text()='Get a new one']")
        except Exception:
            # time out
            return False

        # read and send security code
        security_code = None
        first_attempt = True
        while True:
            env.event("LOGIN", "WAITING-FOR-SECURITY-CODE", {"choice": choice_text})
            if query_mode:
                try:
                    latest = query_latest({"securityCode": security_code})
                except:
                    raise
                security_code = latest["securityCode"]
            else:
                security_code = str(input("input security code (NEWONE to get a new one):"))

            # get a new code if "NEWONE" was in the input
            if "NEWONE" in security_code:
                (ActionChains(browser)
                 .move_to_element(newcode_link)
                 .click()
                 .perform())
                env.event("LOGIN", "SECURITY-CODE-GOT-NEW-ONE")
                continue

            # skip the code if it's not 6-length digits
            if not security_code.isdigit() or not len(security_code) == 6:
                continue

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
                # fail_selector = "//p[text()='Please check the code we sent you and try again.']"
                indicator_selector = success_selector  # + "|" + fail_selector

                if not first_attempt:
                    super_print("[login_user] not the first attempt, wait 4 seconds until page fully updated")
                    sleep(4)

                indicator_ele = explicit_wait(browser, "VOEL", [indicator_selector, "XPath"], logger, 5, True)
                if indicator_ele.get_attribute("class") == "success":
                    super_print("[login_user] sucurity code went through, login successfully!!!")
                    break
                else:
                    first_attempt = False
                    super_print("[login_user] wrong security code, try again...")
                    env.event("LOGIN", "WRONG-SECURITY-CODE")
            except Exception:
                # correct security code
                # super_print("[login_user] wrong security code, please try again")
                # env.event("LOGIN", "WRONG-SECURITY-CODE")
                super_print("[login_user] unexpected page, try again...")
                env.event("LOGIN", "WRONG-SECURITY-CODE")
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
            # super_print("[login_user] no indication of what specific location we're at, let's bypass-suspicious-page")
            reload_webpage(browser)
            # env.event("LOGIN", "BEGIN-BYPASS-SUSPICIOUS-PAGE")
            # if not bypass_suspicious_login(browser, bypass_with_mobile):
            #     return False
        else:
            # super_print("[login_user] no indication of what specific location we're at, let's refresh our browser")
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
    # print(browser.get_cookies())
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


def parse_cli_args():
    super_print("[InstaPy] original InstaPy argument parsing disabled")
    args = type('EmptyArgumentsObject', (object,), {})
    args.username = None
    args.password = None
    args.use_firefox = None
    args.page_delay = None
    args.proxy_address = None
    args.proxy_port = None
    args.headless_browser = None
    args.disable_image_load = None
    args.bypass_suspicious_attempt = None
    args.bypass_with_mobile = None
    return args
    """ Parse arguments passed by command line interface """

    # AP_kwargs = dict(prog="InstaPy",
    #                  description="Parse InstaPy constructor's arguments",
    #                  epilog="And that's how you'd pass arguments by CLI..",
    #                  conflict_handler="resolve")
    # if python_version() < "3.5":
    #     parser = CustomizedArgumentParser(**AP_kwargs)
    # else:
    #     AP_kwargs.update(allow_abbrev=False)
    #     parser = ArgumentParser(**AP_kwargs)
    #
    # """ Flags that REQUIRE a value once added
    # ```python quickstart.py --username abc```
    # """
    # parser.add_argument(
    #     "-u", "--username", help="Username", type=str, metavar="abc")
    # parser.add_argument(
    #     "-p", "--password", help="Password", type=str, metavar="123")
    # parser.add_argument(
    #     "-pd", "--page-delay", help="Implicit wait", type=int, metavar=25)
    # parser.add_argument(
    #     "-pa", "--proxy-address", help="Proxy address",
    #     type=str, metavar="192.168.1.1")
    # parser.add_argument(
    #     "-pp", "--proxy-port", help="Proxy port", type=int, metavar=8080)
    #
    # """ Auto-booleans: adding these flags ENABLE themselves automatically
    # ```python quickstart.py --use-firefox```
    # """
    # parser.add_argument(
    #     "-uf", "--use-firefox", help="Use Firefox",
    #     action="store_true", default=None)
    # parser.add_argument(
    #     "-hb", "--headless-browser", help="Headless browser",
    #     action="store_true", default=None)
    # parser.add_argument(
    #     "-dil", "--disable-image-load", help="Disable image load",
    #     action="store_true", default=None)
    # parser.add_argument(
    #     "-bsa", "--bypass-suspicious-attempt",
    #     help="Bypass suspicious attempt", action="store_true", default=None)
    # parser.add_argument(
    #     "-bwm", "--bypass-with-mobile", help="Bypass with mobile phone",
    #     action="store_true", default=None)
    #
    # """ Style below can convert strings into booleans:
    # ```parser.add_argument("--is-debug",
    #                        default=False,
    #                        type=lambda x: (str(x).capitalize() == "True"))```
    #
    # So that, you can pass bool values explicitly from CLI,
    # ```python quickstart.py --is-debug True```
    #
    # NOTE: This style is the easiest of it and currently not being used.
    # """
    #
    # args, args_unknown = parser.parse_known_args()
    # """ Once added custom arguments if you use a reserved name of core flags
    # and don't parse it, e.g.,
    # `-ufa` will misbehave cos it has `-uf` reserved flag in it.
    #
    # But if you parse it, it's okay.
    # """
    #
    # return args
