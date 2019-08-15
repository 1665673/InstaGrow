import os
import time
import argparse
import requests
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options as ChromeOptions
from dotenv import load_dotenv, find_dotenv
import json
from lib import extensions

load_dotenv(find_dotenv())
SERVER = os.getenv("SERVER") if os.getenv("SERVER") else "https://admin.socialgrow.live"
DRIVER_CHROME = os.getenv("DRIVER_CHROME") if os.getenv("DRIVER_CHROME") else "/usr/local/bin/chromedriver"
DRIVER_FIREFOX = os.getenv("DRIVER_FIREFOX") if os.getenv("DRIVER_FIREFOX") else "/usr/local/bin/geckodriver"
UPLOAD_COOKIES_URL = SERVER + "/admin/script/upload-cookies"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--chrome", action="store_true")
    parser.add_argument("-x", "--proxy", type=str)
    args = parser.parse_args()

    browser = None
    proxy = args.proxy.split(":") if args.proxy else []

    # open browser, and setup proxy if applicable
    if args.chrome:
        chrome_options = ChromeOptions()
        if proxy:
            proxy_string = '{0}:{1}@{2}:{3}'.format(proxy[2],
                                                    proxy[3],
                                                    proxy[0],
                                                    proxy[1])
            proxy_chrome_extension = extensions.create_proxy_extension(proxy_string)
            proxy_chrome_extension = "{0}/{1}".format(os.getcwd(), proxy_chrome_extension)
            chrome_options.add_extension(proxy_chrome_extension)
        browser = webdriver.Chrome(executable_path=DRIVER_CHROME,
                                   options=chrome_options)

    else:
        firefox_profile = webdriver.FirefoxProfile()
        if proxy:
            firefox_profile.set_preference('network.proxy.type', 1)
            firefox_profile.set_preference('network.proxy.http',
                                           proxy[0])
            firefox_profile.set_preference('network.proxy.http_port',
                                           int(proxy[1]))
            firefox_profile.set_preference('network.proxy.ssl',
                                           proxy[0])
            firefox_profile.set_preference('network.proxy.ssl_port',
                                           int(proxy[1]))
        browser = webdriver.Firefox(executable_path=DRIVER_FIREFOX,
                                    firefox_profile=firefox_profile)

        if proxy and proxy[2]:
            firefox_proxy_authentication(browser, proxy[2], proxy[3])

        # add extenions to hide selenium
        browser.install_addon(extensions.create_firefox_extension(), temporary=True)

    # go to instagram login page
    browser.set_window_size(375, 812)  # iphone X
    browser.get("https://www.instagram.com/accounts/login/")

    while input("enter 'r' when ready to upload cookies: ") != 'r':
        pass

    cookies = browser.get_cookies()
    browser.quit()

    print("cookies from this session:")
    print(cookies)
    print()

    print("provide instagram account info for '--pull' purpose:")
    username = ""
    while not username:
        username = input("instagram username:")
    password = input("instagram password:")

    print("uploading cookies...")
    requests.post(
        url=UPLOAD_COOKIES_URL,
        headers={'content-type': 'application/json'},
        data=json.dumps({
            "instagramUser": username,
            "instagramPassword": password,
            "cookies": cookies
        })
    )

    print("ALL SET")


def firefox_proxy_authentication(firefox_browser,
                                 proxy_username,
                                 proxy_password):
    try:
        time.sleep(1)
        alert_popup = firefox_browser.switch_to.alert
        alert_popup.send_keys('{username}{tab}{password}{tab}'
                              .format(username=proxy_username,
                                      tab=Keys.TAB,
                                      password=proxy_password))
        alert_popup.accept()
    except Exception as e:
        print('Unable to proxy authenticate: {}'.format(str(e)))
        firefox_browser.quit()
        exit(0)


# call the main function
main()
