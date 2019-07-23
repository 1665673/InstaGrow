import os
import argparse
import requests
from selenium import webdriver
from dotenv import load_dotenv, find_dotenv
import json

load_dotenv(find_dotenv())
SERVER = os.getenv("SERVER") if os.getenv("SERVER") else "https://admin.socialgrow.live"
DRIVER_CHROME = os.getenv("DRIVER_CHROME") if os.getenv("DRIVER_CHROME") else "/usr/local/bin/chromedriver"
DRIVER_FIREFOX = os.getenv("DRIVER_FIREFOX") if os.getenv("DRIVER_FIREFOX") else "/usr/local/bin/geckodriver"
UPLOAD_COOKIES_URL = SERVER + "/admin/script/upload-cookies"

parser = argparse.ArgumentParser()
parser.add_argument("-c", "--chrome", action="store_true")
args = parser.parse_args()

browser = None
if args.chrome:
    browser = webdriver.Chrome(executable_path=DRIVER_CHROME)
else:
    browser = webdriver.Firefox(executable_path=DRIVER_FIREFOX)

browser.get("https://www.instagram.com/accounts/login/")

while input("enter 'r' when ready to upload cookies: ") != 'r':
    pass

cookies = browser.get_cookies()
browser.quit()

print("cookies from this session:")
print(cookies)
print()

print("ready to upload cookies:")
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
