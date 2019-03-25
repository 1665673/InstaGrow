# guaranteed to work with instapy-0.3.4
import sys
import environments as reporter


#
#
#   apply all patches
#
def apply():
    sys.modules['instapy'].InstaPy.reporter = reporter
    sys.modules['instapy'].InstaPy.login.__code__ = login.__code__

    sys.modules['instapy.login_util'].reporter = reporter
    sys.modules['instapy.login_util'].printt = printt
    sys.modules['instapy.login_util'].login_user.__code__ = login_user.__code__
    sys.modules['instapy.login_util'].bypass_suspicious_login.__code__ = bypass_suspicious_login.__code__
    sys.modules['instapy.login_util'].dismiss_get_app_offer.__code__ = dismiss_get_app_offer.__code__
    sys.modules['instapy.login_util'].dismiss_notification_offer.__code__ = dismiss_notification_offer.__code__

    sys.modules['instapy.util'].reporter = reporter
    sys.modules['instapy.util'].printt = printt
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
def printt(str):
    # print("LOGIN [%d] %s" % (int(time.time()), str))
    reporter.log(str, title="LOGIN")


def login(self):
    self.reporter.event("LOGIN", "BEGIN")
    """Used to login the user either with the username and password"""
    if not login_user(self.browser,
                      self.username,
                      self.password,
                      self.logger,
                      self.logfolder,
                      # self.switch_language,   # this argument cancelled since instapy-0.3.4
                      self.bypass_suspicious_attempt,
                      self.bypass_with_mobile):
        self.reporter.event("LOGIN", "FAIL")
        message = "Wrong login data!"
        highlight_print(self.username,
                        message,
                        "login",
                        "critical",
                        self.logger)
        self.aborting = True

    else:
        self.reporter.event("LOGIN", "SUCCESS")
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

    self.followed_by = log_follower_num(self.browser,
                                        self.username,
                                        self.logfolder)
    self.following_num = log_following_num(self.browser,
                                           self.username,
                                           self.logfolder)
    self.reporter.data("followers", self.followed_by)

    return self


def login_user(browser,
               username,
               password,
               logger,
               logfolder,
               # switch_language=True, # this argument cancelled since instapy-0.3.4
               bypass_suspicious_attempt=False,
               bypass_with_mobile=False):
    printt("login_user(): patched version")
    """Logins the user with the given username and password"""
    assert username, 'Username not provided'
    assert password, 'Password not provided'
    username = str(username)
    password = str(password)
    # if both username & password are set to "QUERY"
    # then we enable a query-mode, which means this program will try fetch data from database
    query_mode = False
    if username == "QUERY" and password == "QUERY":
        query_mode = True

    #
    #
    #
    #   patch
    #   load cookie before doing anything else
    #
    #
    printt("[login_user] load cookie")
    reporter.event("LOGIN", "LOADING-COOKIES")
    cookie_loaded = False
    try:
        cookies = pickle.load(open('{0}{1}_cookie.pkl'.format(logfolder, username), 'rb'))
        for cookie in cookies:
            browser.add_cookie(cookie)
            cookie_loaded = True
    except (WebDriverException, OSError, IOError):
        printt("[login_user] Cookie file not found, creating cookie...")

    #
    #   patch
    #   DIRECTLY START FROM LOGIN PAGE
    #
    #
    # ig_homepage = "https://www.instagram.com"
    ig_homepage = "https://www.instagram.com/accounts/login/"
    printt("[login_user] go to login page:%s" % ig_homepage)
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
        printt("[login_user] fatal error. can't load the login page, check the network connection.")
        printt("[login_user] quitting...")
        reporter.event("LOGIN", "FAIL-INVALID-NETWORK")
        reporter.error(e)
        return False
    printt("[login_user] login page fully loaded")
    reporter.event("LOGIN", "PAGE-LOADED")

    # include sleep(1) to prevent getting stuck on google.com
    # sleep(1)
    #
    #
    #   patch
    #   SKIP LANGUAGE SWITCH
    #
    #
    # changes instagram website language to english to use english xpaths
    # printt("[login_user] switch page language to english")
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
    printt("[login_user] check if already logged in")
    login_state = check_authorization(browser,
                                      username,
                                      "activity counts",
                                      logger,
                                      False)
    if login_state is True:
        printt("[login_user] logged in!!!")
        reload_webpage(browser)
        # printt("[login_user] close possible pop-up window at fresh login")
        # dismiss_notification_offer(browser, logger)
        return True
    else:
        printt("[login_user] not logged in, need to enter username/password")

    # if user is still not logged in, then there is an issue with the cookie
    # so go create a new cookie..
    if cookie_loaded:
        printt("[login_user] Issue with cookie for user {}. Creating new cookie...".format(username))

    #
    #
    #   patch
    #   NO NEED TO PROCESS THIS PAGE
    #       SINCE WE START FROM LOGIN PAGE
    #
    #
    # # Check if the first div is 'Create an Account' or 'Log In'
    # printt("[login_user] find login button, go to login page")
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
    printt("[login_user] located login form-control elements. ready for logging in.")

    page_after_login = ""
    while True:
        reporter.event("LOGIN", "WAITING-FOR-CREDENTIALS")

        # read username/password
        if not username or not password or query_mode:
            if query_mode:
                # query database for latest credentials
                pass
            else:
                username = str(input("username:"))
                password = str(input("password:"))

        # fill username/password
        input_username.clear()
        input_password.clear()
        printt("[login_user] fill username")
        (ActionChains(browser)
         .move_to_element(input_username)
         .click()
         .send_keys(username)
         .perform())

        printt("[login_user] fill password")
        (ActionChains(browser)
         .move_to_element(input_password)
         .click()
         .send_keys(password)
         .perform())

        printt("[login_user] click login button")
        (ActionChains(browser)
         .move_to_element(button_login)
         .click()
         .perform())
        reporter.event("LOGIN", "CREDENTIALS-SENT")

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
                printt("[login_user] not the first attempt, wait 5 seconds to make sure page fully updated")
                sleep(5)

            indicator_ele = explicit_wait(browser, "VOEL", [indicator_selector, "XPath"], logger, 5, True)
            indicator_class = indicator_ele.get_attribute("class")
            printt("[login_user] login result indicator found! class:%s" % indicator_class)
            if indicator_class == "eiCW-":
                printt("[login_user] it's a wrong-login-credential indicator, try again")
                username = ""
                password = ""
                reporter.event("LOGIN", "WRONG-CREDENTIALS")
                page_after_login = "LOGIN"
                continue
            elif indicator_class == "_6q-tv":
                printt("[login_user] it's a login-successful indicator, congratulations!")
                page_after_login = "HOME"
                break
            else:
                printt("[login_user] it's an authentication-page indicator, need to enter security code")
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
        choice0 = None
        choice1 = None
        send_code_button = None
        try:
            choice0 = browser.find_element_by_xpath("//label[@for='choice_0']")
        except Exception:
            choice0 = None
            pass
        try:
            choice1 = browser.find_element_by_xpath("//label[@for='choice_1']")
        except Exception:
            choice1 = None
            pass
        try:
            send_code_button = browser.find_element_by_xpath("//button[text()='Send Security Code']")
        except Exception:
            pass

        choice_made = None
        # if we have got both methods of sending code, let user choose one
        if choice0 and choice1:
            reporter.event("LOGIN", "CHOOSE-METHOD-TO-SEND-CODE")
            # ask for a choice
            if query_mode:
                pass
            else:
                printt("[login_user] choose a method to receive security code from instagram:\n0: " +
                       choice0.text + "\n1: " + choice1.text + "\n")
                choice_made = str(input())
            # apply the choice
            if choice_made == "0":
                choice_made = choice0
            else:
                choice_made = choice1
        # only one choice is available, and that one will be used
        else:
            if choice0:
                choice_made = choice0
            else:
                choice_made = choice1
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
        printt("[login_user] a security code has been sent to " + choice_made.text)
        reporter.event("LOGIN", "SECURITY-CODE-REQUESTED")

        # wait for security code page to load
        input_code = None
        button_submit = None
        try:
            input_code = explicit_wait(browser, "VOEL", ["//input[@id='security_code']", "XPath"], logger, 15, True)
        except Exception:
            # time out
            return False
            pass
        button_submit = browser.find_element_by_xpath("//button[text()='Submit']")

        # read and send security code
        while True:
            reporter.event("LOGIN", "WAITING-FOR-SECURITY-CODE")
            security_code = None
            if query_mode:
                pass
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
            reporter.event("LOGIN", "SECURITY-CODE-SENT")

            try:
                success_selector = "//img[@class='_6q-tv']"
                success = explicit_wait(browser, "VOEL", [success_selector, "XPath"], logger, 5, True)
                if success:
                    printt("[login_user] sucurity code went through, login successfully!!!")
                    break
            except Exception:
                # correct security code
                printt("[login_user] wrong security code, please try again")
                reporter.event("LOGIN", "WRONG-SECURITY-CODE")
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
            printt("[login_user] no indication of what specific location we're at, let's bypass-suspicious-page")
            reporter.event("LOGIN", "BEGIN-BYPASS-SUSPICIOUS-PAGE")
            if not bypass_suspicious_login(browser, bypass_with_mobile):
                return False
        else:
            printt("[login_user] no indication of what specific location we're at, let's refresh our browser")
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
    # printt("[login_user] close possible pop-up windows at a fresh login")
    # dismiss_get_app_offer(browser, logger)
    # dismiss_notification_offer(browser, logger)
    printt("[login_user] dump cookie")
    reporter.event("LOGIN", "DUMPING-COOKIES")
    pickle.dump(browser.get_cookies(), open('{0}{1}_cookie.pkl'.format(logfolder, username), 'wb'))
    return True

    # # Check if user is logged-in (If there's two 'nav' elements)
    # nav = browser.find_elements_by_xpath('//nav')
    # if len(nav) == 2:
    #     # create cookie for username
    #     reporter.event("LOGIN","DUMPING-COOKIE")
    #     pickle.dump(browser.get_cookies(), open(
    #         '{0}{1}_cookie.pkl'.format(logfolder, username), 'wb'))
    #     return True
    # else:
    #     return False


def bypass_suspicious_login(browser, bypass_with_mobile):
    printt("bypass_suspicious_login(): patched version")
    sleep(10000)  # let me look at this page carefully
    """Bypass suspicious login attempt verification. This should be only
    enabled
    when there isn't available cookie for the username, otherwise it will and
    shows "Unable to locate email or phone button" message, folollowed by
    CRITICAL - Wrong login data!"""

    printt("[bypass_suspicious_login] try close sign up modal")
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

    printt("[bypass_suspicious_login] try click that was me")
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
    # printt("[bypass_suspicious_login] try find send code button")
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
    # printt("[bypass_suspicious_login] check if bypass_with_mobile")
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
    printt("check_authorization(): patched version")
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

        printt("[check_authorization] activity_counts: %s, activity_counts_new: %s" % (
            activity_counts, activity_counts_new))

        if activity_counts is None and activity_counts_new is None:
            if notify is True:
                logger.critical(
                    "--> '{}' is not logged in!\n".format(username))
            return False

    return True


def dismiss_get_app_offer(browser, logger):
    printt("dismiss_get_app_offer(): patched version")
    """ Dismiss 'Get the Instagram App' page after a fresh login """
    offer_elem = "//*[contains(text(), 'Get App')]"
    dismiss_elem = "//*[contains(text(), 'Not Now')]"

    # wait a bit and see if the 'Get App' offer rises up
    # offer_loaded = explicit_wait(
    #    browser, "VOEL", [offer_elem, "XPath"], logger, 5, False)

    # if offer_loaded:
    try:
        dismiss_elem = browser.find_element_by_xpath(dismiss_elem)
        printt("[get-app-window] %s" % dismiss_elem)
        click_element(browser, dismiss_elem)
    except:
        pass


def dismiss_notification_offer(browser, logger):
    printt("dismiss_notification_offer(): patched version")
    """ Dismiss 'Turn on Notifications' offer on session start """
    offer_elem_loc = "//div/h2[text()='Turn on Notifications']"
    dismiss_elem_loc = "//button[text()='Not Now']"

    # wait a bit and see if the 'Turn on Notifications' offer rises up
    # offer_loaded = explicit_wait(
    #    browser, "VOEL", [offer_elem_loc, "XPath"], logger, 4, False)

    # if offer_loaded:
    try:
        dismiss_elem = browser.find_element_by_xpath(dismiss_elem_loc)
        printt("[notification-window] %s" % dismiss_elem_loc)
        click_element(browser, dismiss_elem)
    except:
        pass


def explicit_wait(browser, track, ec_params, logger, timeout=5, notify=True):
    # printt("explicit_wait(): %s" % ec_params)
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
        # printt("[explicit_wait] start waiting for: %s, timeout %d" % (ec_params, timeout))
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
