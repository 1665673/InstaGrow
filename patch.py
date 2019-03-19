import sys
import time


#
#
def apply():
    sys.modules['instapy.login_util'].printt = printt
    sys.modules['instapy.util'].printt = printt
    sys.modules['instapy.login_util'].login_user.__code__ = login_user.__code__
    sys.modules['instapy.login_util'].bypass_suspicious_login.__code__ = bypass_suspicious_login.__code__
    sys.modules['instapy.login_util'].dismiss_get_app_offer.__code__ = dismiss_get_app_offer.__code__
    sys.modules['instapy.login_util'].dismiss_notification_offer.__code__ = dismiss_notification_offer.__code__
    sys.modules['instapy.util'].check_authorization.__code__ = check_authorization.__code__
    sys.modules['instapy.util'].explicit_wait.__code__ = explicit_wait.__code__


#
#
#
#
#
#
#
#
def printt(*a, **k):
    print("[%d]" % int(time.time()), *a, **k)


def login_user(browser,
               username,
               password,
               logger,
               logfolder,
               switch_language=True,
               bypass_suspicious_attempt=False,
               bypass_with_mobile=False):
    printt("login_user(): patched version")
    """Logins the user with the given username and password"""
    assert username, 'Username not provided'
    assert password, 'Password not provided'

    #
    #
    #
    #   patch
    #   load cookie before doing anything else
    #
    #
    printt("[login_user]", "load cookie")
    try:
        for cookie in pickle.load(open(
                '{0}{1}_cookie.pkl'.format(logfolder, username), 'rb')):
            browser.add_cookie(cookie)
            cookie_loaded = True
    except (WebDriverException, OSError, IOError):
        print("Cookie file not found, creating cookie...")

    #
    #   patch
    #   DIRECTLY START FROM LOGIN PAGE
    #
    #
    # ig_homepage = "https://www.instagram.com"
    ig_homepage = "https://www.instagram.com/accounts/login/"

    printt("[login_user]", "go to login page:", ig_homepage)
    web_address_navigator(browser, ig_homepage)
    cookie_loaded = False

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

    # cookie has been LOADED, so the user SHOULD be logged in
    # check if the user IS logged in
    printt("[login_user] check if already logged in")
    login_state = check_authorization(browser,
                                      username,
                                      "activity counts",
                                      logger,
                                      False)
    if login_state is True:
        printt("[login_user] logged in!!!")
        printt("[login_user] close possible pop-up window at fresh login")
        dismiss_notification_offer(browser, logger)
        return True
    else:
        printt("[login_user] not logged in, need to input username/password")

    # if user is still not logged in, then there is an issue with the cookie
    # so go create a new cookie..
    if cookie_loaded:
        print("Issue with cookie for user {}. Creating "
              "new cookie...".format(username))

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

    # wait until it navigates to the login page
    login_page_title = "Login"
    explicit_wait(browser, "TC", login_page_title, logger)
    printt("[login_user] arrived login page")

    # wait until the 'username' input element is located and visible
    input_username_XP = "//input[@name='username']"
    explicit_wait(browser, "VOEL", [input_username_XP, "XPath"], logger)

    printt("[login_user] input username")
    input_username = browser.find_element_by_xpath(input_username_XP)

    (ActionChains(browser)
     .move_to_element(input_username)
     .click()
     .send_keys(username)
     .perform())

    # update server calls for both 'click' and 'send_keys' actions
    for i in range(2):
        update_activity()

    # sleep(1)

    #  password
    input_password = browser.find_elements_by_xpath(
        "//input[@name='password']")

    if not isinstance(password, str):
        password = str(password)

    printt("[login_user] input password")
    (ActionChains(browser)
     .move_to_element(input_password[0])
     .click()
     .send_keys(password)
     .perform())

    # update server calls for both 'click' and 'send_keys' actions
    for i in range(2):
        update_activity()

    printt("[login_user] find login button")
    #
    #
    #
    #   patch
    #   find login button
    #   try two possible case at the same time
    #
    #
    #
    #
    # try:
    #     login_button = browser.find_element_by_xpath("//div[text()='Log in']")
    # except NoSuchElementException:
    #     print("Login A/B test detected! Trying another string...")
    #     login_button = browser.find_element_by_xpath(
    #         "//div[text()='Log In']")
    login_button = browser.find_element_by_xpath("//div[text()='Log in']|//div[text()='Log In']")

    printt("[login_user] click login button")
    (ActionChains(browser)
     .move_to_element(login_button)
     .click()
     .perform())

    # update server calls
    update_activity()

    #
    #
    #
    #
    #   patch
    #   check login status one more time
    #       right after click the login button
    #
    #   explicitly wait until user avartar show up !!! very important!!!
    #   use explicitly wait message to monitor page change
    #       instead of the original sleep and check method
    #
    #   img[@class='_6q-tv'] for avartar image, which indicates a successful login
    #   div[@class='eiCW-'] for wrong password message
    #
    indicator_selector = "//img[@class='_6q-tv']|//div[@class='eiCW-']"
    try:
        indicator_ele = explicit_wait(browser, "VOEL", [indicator_selector, "XPath"], logger, 5, True)
        indicator_class = indicator_ele.get_attribute("class")
        printt("[login_user]", "login indicator found! class:", indicator_class)
        if indicator_class == "eiCW-":
            printt("[login_user]", "it's a wrong login data indicator, quit")
            return False

    except TimeoutException:
        printt("[login_user]", "no indication of login success/fail, go bypass suspicious page")
        if bypass_suspicious_attempt is True:
            bypass_suspicious_login(browser, bypass_with_mobile)
        # wait until page fully load
        explicit_wait(browser, "PFL", [], logger, 5)


    # login_state = check_authorization(browser,
    #                                   username,
    #                                   "activity counts",
    #                                   logger,
    #                                   False)
    #
    #
    #
    #
    #
    #
    #


    #
    #
    #   close pop-up windows at fresh login
    #   SKIP THIS STEP
    #
    #
    #
    # printt("[login_user] close possible pop-up windows at a fresh login")
    # dismiss_get_app_offer(browser, logger)
    # dismiss_notification_offer(browser, logger)

    printt("[login_user] dump cookie")
    # Check if user is logged-in (If there's two 'nav' elements)
    nav = browser.find_elements_by_xpath('//nav')
    if len(nav) == 2:
        # create cookie for username
        pickle.dump(browser.get_cookies(), open(
            '{0}{1}_cookie.pkl'.format(logfolder, username), 'wb'))
        return True
    else:
        return False


def bypass_suspicious_login(browser, bypass_with_mobile):
    printt("bypass_suspicious_login(): patched version")
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

    printt("[bypass_suspicious_login] try find send code button")
    try:
        choice = browser.find_element_by_xpath(
            "//label[@for='choice_1']").text

    except NoSuchElementException:
        try:
            choice = browser.find_element_by_xpath(
                "//label[@class='_q0nt5']").text

        except Exception:
            try:
                choice = browser.find_element_by_xpath(
                    "//label[@class='_q0nt5 _a7z3k']").text

            except Exception:
                print("Unable to locate email or phone button, maybe "
                      "bypass_suspicious_login=True isn't needed anymore.")
                return False

    printt("[bypass_suspicious_login] check if bypass_with_mobile")
    if bypass_with_mobile:
        choice = browser.find_element_by_xpath(
            "//label[@for='choice_0']").text

        mobile_button = browser.find_element_by_xpath(
            "//label[@for='choice_0']")

        (ActionChains(browser)
         .move_to_element(mobile_button)
         .click()
         .perform())

        sleep(5)

    send_security_code_button = browser.find_element_by_xpath(
        "//button[text()='Send Security Code']")

    (ActionChains(browser)
     .move_to_element(send_security_code_button)
     .click()
     .perform())

    # update server calls
    update_activity()

    print('Instagram detected an unusual login attempt')
    print('A security code was sent to your {}'.format(choice))
    security_code = input('Type the security code here: ')

    security_code_field = browser.find_element_by_xpath((
        "//input[@id='security_code']"))

    (ActionChains(browser)
     .move_to_element(security_code_field)
     .click()
     .send_keys(security_code)
     .perform())

    # update server calls for both 'click' and 'send_keys' actions
    for i in range(2):
        update_activity()

    submit_security_code_button = browser.find_element_by_xpath(
        "//button[text()='Submit']")

    (ActionChains(browser)
     .move_to_element(submit_security_code_button)
     .click()
     .perform())

    # update server calls
    update_activity()

    try:
        sleep(5)
        # locate wrong security code message
        wrong_login = browser.find_element_by_xpath((
            "//p[text()='Please check the code we sent you and try "
            "again.']"))

        if wrong_login is not None:
            print(('Wrong security code! Please check the code Instagram'
                   'sent you and try again.'))

    except NoSuchElementException:
        # correct security code
        pass


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

        printt("[check]", "activity_counts:", activity_counts, ",activity_counts_new", activity_counts_new)

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
        printt("[get-app-window]", dismiss_elem)
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
        printt("[notification-window]", dismiss_elem_loc)
        click_element(browser, dismiss_elem)
    except:
        pass


def explicit_wait(browser, track, ec_params, logger, timeout=5, notify=True):
    printt("explicit_wait():", ec_params)
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
        printt("[explicit_wait]", "start waiting for:", ec_params, "timeout:", timeout)
        wait = WebDriverWait(browser, timeout)
        result = wait.until(condition)

    except TimeoutException:
        if notify is True:
            logger.info(
                "Timed out with failure while explicitly waiting until {}!\n"
                    .format(ec_name))
        return False

    return result
