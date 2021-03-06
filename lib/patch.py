# guaranteed to work with instapy-0.3.4
import sys
from contextlib import contextmanager
from . import environments as env
from . import proxypool
# from .proxy_extension import create_proxy_extension
from . import extensions


#
#
#   apply all patches
#
def apply():
    sys.modules['instapy'].InstaPy.env = env
    sys.modules['instapy'].InstaPy.super_print = super_print
    sys.modules['instapy'].InstaPy.proxypool = proxypool
    sys.modules['instapy'].InstaPy.query_latest = query_latest
    sys.modules['instapy'].InstaPy.query_latest1 = query_latest1
    sys.modules['instapy'].InstaPy.end.__code__ = end.__code__
    sys.modules['instapy'].InstaPy.login.__code__ = login.__code__
    sys.modules['instapy'].InstaPy.set_selenium_local_session.__code__ = set_selenium_local_session_patch.__code__

    sys.modules['instapy.login_util'].env = env
    sys.modules['instapy.login_util'].super_print = super_print
    sys.modules['instapy.login_util'].query_latest = query_latest
    sys.modules['instapy.login_util'].query_latest1 = query_latest1
    sys.modules['instapy.login_util'].login_user.__code__ = login_user.__code__
    sys.modules['instapy.login_util'].bypass_suspicious_login.__code__ = bypass_suspicious_login.__code__
    sys.modules['instapy.login_util'].dismiss_get_app_offer.__code__ = dismiss_get_app_offer.__code__
    sys.modules['instapy.login_util'].dismiss_notification_offer.__code__ = dismiss_notification_offer.__code__

    sys.modules['instapy.util'].env = env
    sys.modules['instapy.util'].super_print = super_print
    # sys.modules['instapy.util'].smart_run.__code__ = smart_run.__code__
    sys.modules['instapy.util'].check_authorization.__code__ = check_authorization.__code__
    sys.modules['instapy.util'].web_address_navigator.__code__ = web_address_navigator.__code__
    sys.modules['instapy.util'].explicit_wait.__code__ = explicit_wait.__code__
    sys.modules['instapy.util'].update_activity.__code__ = update_activity.__code__
    sys.modules['instapy.util'].parse_cli_args.__code__ = parse_cli_args.__code__

    sys.modules[
        'instapy.browser'].set_selenium_local_session.__code__ = set_selenium_local_session_browser_patch.__code__
    sys.modules['instapy.browser'].extensions = extensions

    sys.modules['instapy.file_manager'].get_workspace.__code__ = get_workspace.__code__
    sys.modules['instapy.file_manager'].get_chromedriver_location.__code__ = get_chromedriver_location.__code__


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


# accept a dictionary of attributes, with keys being names and old values being values
def query_latest(attributes):
    return env.query_latest_attributes(attributes)


# accept a list of attributes
def query_latest1(attributes):
    return env.query_latest_attributes1(attributes)


def end(self, threaded_session=False):
    #
    #   skip everything here
    #   now I use my own exit-handler for all these SIGINT, SIGTERM, SIGKILL
    #   worked much more reliably
    #
    InstaPy.super_print("[end] script is naturally quitting...")
    InstaPy.env.event("SELENIUM", "SESSION-QUITTING", {"proxy": self.proxy_string, "message": "session finished"})
    InstaPy.env.event("SCRIPT", "QUITTING", {"message": "script finished"})
    return

    # InstaPy.super_print("end(): patched version")
    # InstaPy.super_print("[end] script is quitting")
    # InstaPy.env.event("SESSION", "SCRIPT-QUITTING", {"proxy": self.proxy_string})
    #
    # """Closes the current session"""
    # Settings.InstaPy_is_running = False
    # close_browser(self.browser, threaded_session, self.logger)
    #
    # with interruption_handler():
    #     # close virtual display
    #     if self.nogui:
    #         self.display.stop()
    #
    #     # write useful information
    #     # dump_follow_restriction(self.username,
    #     #                         self.logger,
    #     #                         self.logfolder)
    #     # dump_record_activity(self.username,
    #     #                      self.logger,
    #     #                      self.logfolder)
    #
    #     # with open('{}followed.txt'.format(self.logfolder), 'w') \
    #     #        as followFile:
    #     #    followFile.write(str(self.followed))
    #
    #     # output live stats before leaving
    #     self.live_report()
    #
    #     message = "Session ended!"
    #     highlight_print(self.username, message, "end", "info", self.logger)
    #     print("\n\n")


#
#
#
######################################################################################
#
#
#
#
#
#
#   patches for instapy.py
#
#
#
#
#
#
######################################################################################
#
#
#
def login(self):
    # InstaPy.super_print("login(): patched version")
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
        InstaPy.env.log("-------------------------------------------")
        # message = "Wrong login data!"
        # highlight_print(self.username,
        #                 message,
        #                 "login",
        #                 "critical",
        #                 self.logger)
        # self.aborting = True
        InstaPy.env.safe_quit(self)

    else:
        #
        #   synchronize success status with main server before raising SUCCESS event
        #
        InstaPy.env.report_success(self)
        InstaPy.env.event("LOGIN", "SUCCESS")
        InstaPy.env.log("-------------------------------------------")
        # message = "Login success!"
        # highlight_print(self.username,
        #                 message,
        #                 "login",
        #                 "info",
        #                 self.logger)

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
    # put InstaPy object in environment
    InstaPy.env.set_session(self)

    # InstaPy.super_print("set_selenium_local_session_patch(): patched version")
    if self.browser:
        self.browser.quit()
        self.browser = None
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
    alloc_proxy = InstaPy.env.args().allocate_proxy
    retry_proxy = InstaPy.env.args().retry_proxy

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
            #   if we need a new proxy
            if (not first_attempt) or (not self.proxy_address):
                #  allocate a new proxy, if connection to main server is bad, only 3 attempts allowed
                if alloc_proxy is not None:
                    group = alloc_proxy[0]
                    tag = alloc_proxy[1]
                    proxy = {}
                    allocate_proxy_failed_count = 0
                    while allocate_proxy_failed_count < 3:
                        proxy = self.proxypool.allocate_proxy(group, tag, None)  # , proxy_string)
                        if "string" not in proxy:
                            allocate_proxy_failed_count += 1
                            InstaPy.super_print("[selenium] wait 3 seconds before another attempt of proxy allocation")
                            sleep(3)
                        else:
                            break
                    if allocate_proxy_failed_count == 3:
                        InstaPy.env.event("SELENIUM", "ALLOCATE-PROXY-FAILED")
                        exit(0)
                    # InstaPy.env.event("SELENIUM", "PROXY-ALLOCATED", {"proxy": proxy["string"]})
                    InstaPy.super_print("[selenium] proxy allocated:\n%s\n"
                                        "%d current-clients, %d failed-attempts, %d history-connections" %
                                        (proxy["string"], proxy["clientsCount"],
                                         proxy["failsCount"], proxy["historyCount"]))
                    proxy_string = proxy["string"]
                # query a new proxy delivered by main server through script status
                elif query_mode:
                    InstaPy.env.event("SELENIUM", "WAITING-FOR-PROXY")
                    # latest = InstaPy.query_latest({"proxy": proxy_string})
                    latest = InstaPy.query_latest1(["queryProxy"])
                    proxy_string = latest["queryProxy"]
                    # InstaPy.env.event("SELENIUM", "PROXY-ASSIGNED", {"proxy": proxy_string})
                # get a new proxy from shell
                else:
                    proxy_string = input("input proxy-string:")

            # save the proxy we are using to Instapy object
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
            # if we don't have any retry attempts left, i.e. retry_proxy == 0,
            # then raise the exception, and quit the login process
            if not retry_proxy:
                if len(err_msg) > 0:
                    raise InstaPyError(err_msg)
                else:
                    raise exception

            # if we are still retrying, then close current browser instance and continue
            retry_proxy -= 1
            first_attempt = False
            self.browser.quit()
            self.browser = None
            InstaPy.super_print("[selenium] retry connecting with new proxy. {} attempts left"
                                .format(retry_proxy + 1))
            InstaPy.env.event("SELENIUM", "RETRY-CREATING-SESSION")


def set_selenium_local_session_browser_patch(proxy_address,
                                             proxy_port,
                                             proxy_username,
                                             proxy_password,
                                             proxy_chrome_extension,
                                             headless_browser,
                                             use_firefox,
                                             browser_profile_path,
                                             disable_image_load,
                                             page_delay,
                                             logger):
    """Starts local session for a selenium server.
    Default case scenario."""

    browser = None
    err_msg = ''

    if use_firefox:
        firefox_options = Firefox_Options()
        if headless_browser:
            firefox_options.add_argument('-headless')

        if browser_profile_path is not None:
            firefox_profile = webdriver.FirefoxProfile(
                browser_profile_path)
        else:
            firefox_profile = webdriver.FirefoxProfile()

        if disable_image_load:
            # permissions.default.image = 2: Disable images load,
            # this setting can improve pageload & save bandwidth
            firefox_profile.set_preference('permissions.default.image', 2)

        if proxy_address and proxy_port:
            firefox_profile.set_preference('network.proxy.type', 1)
            firefox_profile.set_preference('network.proxy.http',
                                           proxy_address)
            firefox_profile.set_preference('network.proxy.http_port',
                                           proxy_port)
            firefox_profile.set_preference('network.proxy.ssl',
                                           proxy_address)
            firefox_profile.set_preference('network.proxy.ssl_port',
                                           proxy_port)

        # change user-agent
        firefox_profile.set_preference("general.useragent.override",
                                       "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14.5; rv:66.0) Gecko/20100101 Firefox/66.0")

        browser = webdriver.Firefox(firefox_profile=firefox_profile,
                                    options=firefox_options)

        # converts to custom browser
        # browser = convert_selenium_browser(browser)

        # authenticate with popup alert window
        if (proxy_username and proxy_password):
            proxy_authentication(browser,
                                 logger,
                                 proxy_username,
                                 proxy_password)

        # add extenions to hide selenium
        browser.install_addon(extensions.create_firefox_extension(), temporary=True)

    else:
        chromedriver_location = get_chromedriver_location()
        # print(chromedriver_location)
        chrome_options = Options()
        chrome_options.add_argument('--mute-audio')
        chrome_options.add_argument('--dns-prefetch-disable')
        chrome_options.add_argument('--lang=en-US')
        chrome_options.add_argument('--disable-setuid-sandbox')
        chrome_options.add_argument('disable-infobars')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_argument('--no-sandbox')

        if disable_image_load:
            chrome_options.add_argument('--blink-settings=imagesEnabled=false')

        # this option implements Chrome Headless, a new (late 2017)
        # GUI-less browser. chromedriver 2.9 and above required
        if headless_browser:
            chrome_options.add_argument('--headless')
            # chrome_options.add_argument('--no-sandbox')

            # replaces browser User Agent from "HeadlessChrome".
            user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36"
            chrome_options.add_argument('user-agent={user_agent}'
                                        .format(user_agent=user_agent))

        capabilities = DesiredCapabilities.CHROME

        # Proxy for chrome
        if proxy_address and proxy_port and not proxy_username:
            prox = Proxy()
            proxy = ":".join([proxy_address, str(proxy_port)])
            if headless_browser:
                chrome_options.add_argument(
                    '--proxy-server=http://{}'.format(proxy))
            else:
                prox.proxy_type = ProxyType.MANUAL
                prox.http_proxy = proxy
                prox.socks_proxy = proxy
                prox.ssl_proxy = proxy
                prox.add_to_capabilities(capabilities)

        # add proxy extension
        if proxy_username and not headless_browser:
            proxy = '{0}:{1}@{2}:{3}'.format(proxy_username,
                                             proxy_password,
                                             proxy_address,
                                             proxy_port)
            proxy_chrome_extension = extensions.create_proxy_extension(proxy)
            import os
            proxy_chrome_extension = "{0}/{1}".format(os.getcwd(), proxy_chrome_extension)

        if proxy_chrome_extension and not headless_browser:
            chrome_options.add_extension(proxy_chrome_extension)

        # using saved profile for chrome
        if browser_profile_path is not None:
            chrome_options.add_argument(
                'user-data-dir={}'.format(browser_profile_path))

        chrome_prefs = {
            'intl.accept_languages': 'en-US',
        }

        if disable_image_load:
            chrome_prefs['profile.managed_default_content_settings.images'] = 2

        chrome_options.add_experimental_option('prefs', chrome_prefs)
        try:
            browser = webdriver.Chrome("/usr/local/bin/chromedriver",
                                       desired_capabilities=capabilities,
                                       chrome_options=chrome_options)

            # gets custom instance
            # browser = convert_selenium_browser(browser)

        except WebDriverException as exc:
            logger.exception(exc)
            err_msg = 'ensure chromedriver is installed at {}'.format(
                Settings.chromedriver_location)
            return browser, err_msg

        # prevent: Message: unknown error: call function result missing 'value'
        matches = re.match(r'^(\d+\.\d+)',
                           browser.capabilities['chrome'][
                               'chromedriverVersion'])
        if float(matches.groups()[0]) < Settings.chromedriver_min_version:
            err_msg = 'chromedriver {} is not supported, expects {}+'.format(
                float(matches.groups()[0]), Settings.chromedriver_min_version)
            return browser, err_msg

    browser.implicitly_wait(page_delay)

    # set window size to iphone X
    browser.set_window_size(375, 812)

    # message = "Session started!"
    # highlight_print('browser', message, "initialization", "info", logger)
    # print('')

    return browser, err_msg


#
#
#
######################################################################################
#
#
#
#
#
#
#   patches for login_util.py
#
#
#
#
#
#
######################################################################################
#
#
#
def login_user(browser,
               username,
               password,
               logger,
               logfolder,
               # switch_language=True, # this argument cancelled since instapy-0.3.4
               bypass_suspicious_attempt=False,
               bypass_with_mobile=False):
    # super_print("login_user(): patched version")
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
    no_cookies = env.args().no_cookies
    query_mode = env.args().query
    retry_login = env.args().retry_login

    #
    #
    #   patch 2019-04-27
    #   load cookie before doing anything else
    #
    #   patch 2019-04-28
    #   this logic moved to an earlier stage, in set_selenium_local_session_patch()
    #
    #   patch 2019-04-28-2
    #   this logic is moved back to here, due to very complicated reasons
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
                # print(cookie["name"])
                # if cookie["name"] == "urlgen":
                #     continue
                # print(cookie)
                if "expiry" in cookie:
                    cookie["expiry"] = int(float(cookie["expiry"]))
                browser.add_cookie(cookie)
            cookie_loaded = True
        except Exception as e:
            super_print("[login_user] loading cookie error: " + str(e))
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
    #   just go ahead
    # ---------------------------------2019-04-28----------------------------------------
    #   no, we can't just go ahead
    #   we can't use the login page to test connection, due to very complicated reasons
    #   so at this point, we are not already in the login page,
    #   we still need to go that page now
    #
    # ig_homepage = "https://www.instagram.com"
    ig_login_page = "https://www.instagram.com/accounts/login/"
    super_print("[login_user] go to login page: %s" % ig_login_page)
    web_address_navigator(browser, ig_login_page)
    # ------------------------------------------------------------------------------------

    # ---------------------------------2019-04-27----------------------------------------
    #
    #
    #   wait until the login page is fully loaded
    #
    #
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
    #
    #   patch 2019-04-28
    #   deprecate InstaPy check_authorization
    #   use normal page-element-detecting technique to identify login status a bit faster
    #
    # login_state = check_authorization(browser,
    #                                   username,
    #                                   "activity counts",
    #                                   logger,
    #                                   False)
    login_button_selector = "//div[text()='Log in']|//div[text()='Log In']"
    profile_page_selector = "//img[@class='_6q-tv']"
    suspicious_page_selector = "//button[text()='Close']|//button[text()='This Was Me']"
    login_state_selector = login_button_selector + "|" + profile_page_selector + "|" + suspicious_page_selector
    indicator_ele = explicit_wait(browser, "VOEL", [login_state_selector, "XPath"], logger, 5, True)

    indicator_class = indicator_ele.get_attribute("class")
    indicator_text = indicator_ele.text
    current_page = None

    if indicator_class == "_6q-tv":
        super_print("[login_user] logged in!!!")
        # reload_webpage(browser)
        # super_print("[login_user] close possible pop-up window at fresh login")
        # dismiss_notification_offer(browser, logger)
        return [username, password]

    elif indicator_text == "Log in" or indicator_text == "Log In":
        current_page = "LOGIN"
        super_print("[login_user] not logged in, need to enter username/password")
        # if user is still not logged in, then there is an issue with the cookie
        # so go create a new cookie..
        if cookie_loaded:
            super_print("[login_user] current cookies for {} didn't make an automatic login.".format(username))
    else:
        current_page = "SUSPICIOUS"

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

    if current_page == "LOGIN":
        # locate login form control elements in the page
        # input_username_XP = "//input[@name='username']"
        # explicit_wait(browser, "VOEL", [input_username_XP, "XPath"], logger)
        input_username = browser.find_element_by_xpath("//input[@name='username']")
        input_password = browser.find_element_by_xpath("//input[@name='password']")
        button_login = browser.find_element_by_xpath("//div[text()='Log in']|//div[text()='Log In']")
        super_print("[login_user] located login form-control elements. ready for logging in.")

        retry_credentials = env.args().retry_credentials
        first_attempt = True
        while True:
            # otherwise, read new username/password
            if not first_attempt or (not username or not password):
                if query_mode:
                    env.event("LOGIN", "WAITING-FOR-CREDENTIALS")
                    # query database for latest credentials
                    try:
                        # latest = query_latest({"instagramUser": username, "instagramPassword": password})
                        latest = query_latest1(["queryUsername", "queryPassword"])
                    except:
                        raise
                    username = latest["queryUsername"]
                    password = latest["queryPassword"]
                else:
                    username = str(input("username:"))
                    password = str(input("password:"))

                # mark this script with lastest username
                env.update({"instagramUser": username})

            # store credentials as an entry in main server
            env.json({"username": username, "password": password}, "credentials")

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
            twoway_page_selector = "//input[@name='verificationCode']"
            twoway_page_selector_v2 = "//input[@name='security_code']"
            suspicious_page_selector = "//button[text()='Close']|//button[text()='This Was Me']"
            block_selector = "//input[@name='fullName']"
            indicator_selector = indicator_selector + "|" + \
                                 twoway_page_selector + "|" + twoway_page_selector_v2 + "|" + \
                                 suspicious_page_selector + "|" + block_selector

            try:
                # if page_after_login is not "", then it's not the first attemp, let wait a bit
                if not first_attempt:
                    super_print("[login_user] not the first attempt, wait 3 seconds until page fully updated")
                    sleep(3)

                # erase first_attempt flag
                first_attempt = False

                indicator_ele = explicit_wait(browser, "VOEL", [indicator_selector, "XPath"], logger, 5, True)
                indicator_class = indicator_ele.get_attribute("class")
                indicator_text = indicator_ele.text

                super_print("[login_user] login result indicator found! class:%s, text:%s"
                            % (indicator_class, indicator_text))
                if indicator_class == "eiCW-":
                    super_print("[login_user] it means wrong-login-credential. ({} retry attempts left)"
                                .format(retry_credentials))
                    # if we don't have any retry attempts left, i.e. retry_credentials == 0
                    # then quit the login process
                    if not retry_credentials:
                        return None
                    # otherwise, we try querying and going with credentials
                    # and decrease one remaining attempts
                    retry_credentials -= 1
                    # username = ""
                    # password = ""
                    env.event("LOGIN", "WRONG-CREDENTIALS")
                    continue
                elif indicator_class == "_6q-tv":
                    super_print("[login_user] it means login-successful, congratulations!")
                    current_page = "HOME"
                    break
                elif indicator_text == "Send Security Code":
                    super_print("[login_user] it means authentication-page arrived, need to enter security code")
                    current_page = "AUTHENTICATION"
                    break
                elif indicator_ele.get_attribute("name") == "verificationCode":
                    super_print("[login_user] it means two-way authentication page, need to enter security code")
                    current_page = "TWO-WAY-AUTHENTICATION"
                    break
                elif indicator_ele.get_attribute("name") == "security_code":
                    super_print(
                        "[login_user] it means two-way authentication page (version-2), need to enter security code")
                    current_page = "TWO-WAY-AUTHENTICATION-V2"
                    break
                elif indicator_ele.get_attribute("name") == "fullName":
                    super_print("[login_user] it means we may be blocked. login failed. ({} login retries left)"
                                .format(retry_login))
                    if not retry_login:
                        return None
                    # if we want to give it a re-try, then we must restart the whole thing
                    # and decrease the retry-attempts in new process
                    retry_login -= 1
                    env.event("LOGIN", "RESTARTING-SCRIPT")
                    env.self_restart(None, {"-rl": str(retry_login), "--retry-login": str(retry_login)})
                else:
                    super_print("[login_user] it's an suspicious-page indicator, may simply skip...")
                    current_page = "SUSPICIOUS"
                    break
            except Exception:
                super_print("[login_user] timed out, try again...")
                current_page = "UNKNOWN"
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
    if current_page == "HOME":
        pass
    elif current_page == "AUTHENTICATION" \
            or current_page == "TWO-WAY-AUTHENTICATION" \
            or current_page == "TWO-WAY-AUTHENTICATION-V2":
        #
        #
        #   the most complicated part
        #   deal with authentication codes
        #
        #
        #

        # security code page controls (for both regular-authentication & two-way authentication)
        input_code = None
        button_submit = None
        newcode_link = None
        choice_text = ""
        fail_selector = ""

        #
        # regular-authentication
        #
        if current_page == "AUTHENTICATION":

            env.event("LOGIN", "DETECTING-AUTHENTICATION-CHOICES")

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
                        # latest = query_latest({"authenticationChoice": choice_made})
                        latest = query_latest1(["queryAuthenticationChoice"])
                    except:
                        raise
                    choice_made = latest["queryAuthenticationChoice"]
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

            try:
                input_code = explicit_wait(browser, "VOEL", ["//input[@id='security_code']", "XPath"], logger, 15, True)
                button_submit = browser.find_element_by_xpath("//button[text()='Submit']")
                newcode_link = browser.find_element_by_xpath("//a[text()='Get a new one']")
            except Exception:
                # time out
                return False

            fail_selector = "//p[text()='Please check the code we sent you and try again.']"

        #
        #   two-way-authentication
        #
        elif current_page == "TWO-WAY-AUTHENTICATION":
            input_code = explicit_wait(browser, "VOEL", ["//input[@name='verificationCode']", "XPath"],
                                       logger, 15, True)
            button_submit = browser.find_element_by_xpath("//button[text()='Confirm']")
            newcode_link = browser.find_element_by_xpath("//button[text()='resend it']")
            choice_text = browser.find_element_by_xpath("//div[@id='verificationCodeDescription']").text
            fail_selector = "//p[@id='twoFactorErrorAlert']"

        elif current_page == "TWO-WAY-AUTHENTICATION-V2":
            input_code = explicit_wait(browser, "VOEL", ["//input[@name='security_code']", "XPath"],
                                       logger, 15, True)
            button_submit = browser.find_element_by_xpath("//button[text()='Submit']")
            newcode_link = browser.find_element_by_xpath("//a[text()='Get a new one']")
            choice_text = browser.find_element_by_xpath("//p[contains(@class,'SVI5E')]").text
            fail_selector = "//p[text()='Please check the code we sent you and try again.']"

        # read and send security code
        security_code = None
        first_attempt = True
        while True:
            env.event("LOGIN", "WAITING-FOR-SECURITY-CODE", {"choice": choice_text})
            if query_mode:
                try:
                    # latest = query_latest({"securityCode": security_code})
                    latest = query_latest1(["querySecurityCode"])
                except:
                    raise
                security_code = latest["querySecurityCode"]
            else:
                security_code = str(input("input security code (NEWONE to get a new one):"))

            # get a new code if "NEWONE" was in the input
            if "NEWONE" in security_code:
                (ActionChains(browser)
                 .move_to_element(newcode_link)
                 .click()
                 .perform())
                env.event("LOGIN", "NEW-SECURITY-CODE-REQUESTED")
                continue

            # skip the code if it's not 6-length digits
            if not security_code.isdigit() or not len(security_code) == 6:
                env.event("LOGIN", "WRONG-SECURITY-CODE")
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
                suspicious_page_selector = "//button[text()='Close']|//button[text()='This Was Me']"
                indicator_selector = success_selector + "|" + fail_selector + "|" + suspicious_page_selector

                if not first_attempt:
                    super_print("[login_user] not the first attempt, wait 4 seconds until page fully updated")
                    sleep(4)

                indicator_ele = explicit_wait(browser, "VOEL", [indicator_selector, "XPath"], logger, 5, True)
                #
                #   look at what a fucking ridiculous bug here, if class == "success" ....
                #
                # if indicator_ele.get_attribute("class") == "success":
                if indicator_ele.get_attribute("class") == "_6q-tv":
                    super_print("[login_user] sucurity code went through, login successfully!!!")
                    break
                elif indicator_ele.text == "Close" or indicator_ele.text == "This Was Me":
                    (ActionChains(browser)
                     .move_to_element(indicator_ele)
                     .click()
                     .perform())
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
    elif current_page == "SUSPICIOUS":
        if bypass_suspicious_attempt:
            # super_print("[login_user] no indication of what specific location we're at, let's bypass-suspicious-page")
            # reload_webpage(browser)
            # env.event("LOGIN", "BEGIN-BYPASS-SUSPICIOUS-PAGE")
            # if not bypass_suspicious_login(browser, bypass_with_mobile):
            #     return False
            super_print("[login_user] we are in a suspicious page, and decided to process it...")
            env.event("LOGIN", "BEGIN-BYPASS-SUSPICIOUS-PAGE")
            suspicious_page_selector = "//button[text()='Close']|//button[text()='This Was Me']"
            button = explicit_wait(browser, "VOEL", [suspicious_page_selector, "XPath"], logger, 5, True)
            text = button.text
            (ActionChains(browser)
             .move_to_element(button)
             .click()
             .perform())
            if text == "Close":
                super_print("[login_user] we successfully closed a 'add-phone-number' window")
            else:
                super_print("[login_user] we successfully clicked 'this-was-me'")
        else:
            super_print("[login_user] we are at a suspicious page, and decided to skip it...")

        # refresh the browser no matter decided to process the suspicious page or not
        reload_webpage(browser)

    # we don't know what page we are currently in
    else:
        pass

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
    try:
        pickle.dump(browser.get_cookies(), open('{0}{1}_cookie.pkl'.format(logfolder, username), 'wb'))
    except Exception as e:
        env.error("dumping-cookies", "exception", str(e))
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
    # super_print("bypass_suspicious_login(): patched version")
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


def dismiss_get_app_offer(browser, logger):
    # super_print("dismiss_get_app_offer(): patched version")
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
    # super_print("dismiss_notification_offer(): patched version")
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


#
#
#
######################################################################################
#
#
#
#
#
#
#   patches for util.py
#
#
#
#
#
#
######################################################################################
#
#
#


def check_authorization(browser, username, method, logger, notify=True):
    # super_print("check_authorization(): patched version")
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


def web_address_navigator(browser, link):
    """Checks and compares current URL of web page and the URL to be
    navigated and if it is different, it does navigate"""
    current_url = get_current_url(browser)
    total_timeouts = 0
    page_type = None  # file or directory

    # remove slashes at the end to compare efficiently
    if current_url is not None and current_url.endswith('/'):
        current_url = current_url[:-1]

    if link.endswith('/'):
        link = link[:-1]
        page_type = "dir"  # slash at the end is a directory

    new_navigation = (current_url != link)

    if current_url is None or new_navigation:
        link = link + '/' if page_type == "dir" else link  # directory links
        # navigate faster

        while True:
            try:
                browser.get(link)
                # injected_javascript = ('Object.defineProperties(navigator, {webdriver:{get:()=>undefined}});')
                # if link not in ["https://www.instagram.com/web/search/topsearch/?query=kimkardashian",
                #                 "https://api.ipify.org/"]:
                #     browser.execute_async_script(injected_javascript)

                # update server calls
                update_activity()
                # sleep(2)
                break

            except TimeoutException as exc:
                if total_timeouts >= 7:
                    raise TimeoutException(
                        "Retried {} times to GET '{}' webpage "
                        "but failed out of a timeout!\n\t{}".format(
                            total_timeouts,
                            str(link).encode("utf-8"),
                            str(exc).encode("utf-8")))
                total_timeouts += 1
                # sleep(2)


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

    except TimeoutException:
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
    # super_print("[InstaPy] original InstaPy argument parsing disabled")
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


def get_workspace():
    """ Make a workspace ready for user """

    if WORKSPACE["path"]:
        workspace = verify_workspace_name(WORKSPACE["path"])

    else:
        home_dir = get_home_path()
        workspace = "{}/{}".format(home_dir, WORKSPACE["name"])

    # message = "Workspace in use: \"{}\"".format(workspace)
    # highlight_print(Settings.profile["name"],
    #                 message,
    #                 "workspace",
    #                 "info",
    #                 Settings.logger)
    update_workspace(workspace)
    update_locations()
    return WORKSPACE


def get_chromedriver_location():
    """ Solve chromedriver access issues """
    CD = Settings.chromedriver_location

    if OS_ENV == "windows":
        if not CD.endswith(".exe"):
            CD += ".exe"

    if not file_exists(CD):
        workspace_path = slashen(WORKSPACE["path"], "native")
        assets_path = "{}{}assets".format(workspace_path, native_slash)
        validate_path(assets_path)

        # only import from this package when necessary
        from instapy_chromedriver import binary_path

        CD = binary_path
        chrome_version = pkg_resources.get_distribution("instapy_chromedriver").version
        # message = "Using built in instapy-chromedriver executable (version {})".format(chrome_version)
        # highlight_print(Settings.profile["name"],
        #                 message,
        #                 "workspace",
        #                 "info",
        #                 Settings.logger)

    # save updated path into settings
    Settings.chromedriver_location = CD
    return CD
