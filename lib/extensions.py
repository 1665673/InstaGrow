import zipfile
import os


def create_proxy_extension(proxy):
    """ takes proxy looks like login:password@ip:port """

    ip = proxy.split('@')[1].split(':')[0]
    port = int(proxy.split(':')[-1])
    login = proxy.split(':')[0]
    password = proxy.split('@')[0].split(':')[1]

    manifest_json = """
        {
            "version": "1.0.0",
            "manifest_version": 2,
            "name": "Chrome Proxy",
            "permissions": [
                "proxy",
                "tabs",
                "unlimitedStorage",
                "storage",
                "<all_urls>",
                "webRequest",
                "webRequestBlocking"
            ],
            "background": {
                "scripts": ["background.js"]
            },
            "minimum_chrome_version":"22.0.0"
        }
    """

    background_js = """
        var config = {
                mode: "fixed_servers",
                rules: {
                  singleProxy: {
                    scheme: "http",
                    host: "%s",
                    port: parseInt(%s)
                  },
                  bypassList: ["localhost"]
                }
              };
        chrome.proxy.settings.set({value: config, scope: "regular"}, 
        function() {});
        function callbackFn(details) {
            return {
                authCredentials: {
                    username: "%s",
                    password: "%s"
                }
            };
        }
        chrome.webRequest.onAuthRequired.addListener(
                    callbackFn,
                    {urls: ["<all_urls>"]},
                    ['blocking']
        );
    """ % (ip, port, login, password)

    dir_path = 'assets/chrome_extensions'

    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    pluginfile = '%s/proxy_auth_%s:%s.zip' % (dir_path, ip, port)
    with zipfile.ZipFile(pluginfile, 'w') as zp:
        zp.writestr("manifest.json", manifest_json)
        zp.writestr("background.js", background_js)

    return pluginfile


def create_firefox_extension():
    ext_path = os.path.abspath("firefox/hide_selenium_extension")
    # safe into assets folder

    extension_dir_path = os.path.abspath("assets/firefox_extensions")
    if not os.path.exists(extension_dir_path):
        os.makedirs(extension_dir_path)
        
    zip_file = os.path.abspath(extension_dir_path + "/hide_selenium.xpi")

    files = ["manifest.json", "content.js", "arrive.js"]
    with zipfile.ZipFile(zip_file, "w", zipfile.ZIP_DEFLATED, False) as zipf:
        for file in files:
            zipf.write(ext_path + "/" + file, file)

    return zip_file
