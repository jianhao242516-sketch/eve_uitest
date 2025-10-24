from appium import webdriver
from appium.options.ios import XCUITestOptions
from appium.options.android import UiAutomator2Options
import time

def get_driver(device, appium_server=None):
    if not appium_server:
        raise ValueError('appium_server 必须传入，例如 http://127.0.0.1:4723')
    
    platform = device.get("platformName", "iOS")
    
    if platform == "iOS":
        options = XCUITestOptions()
        options.platform_name = "iOS"
        options.device_name = device.get("name")
        options.automation_name = "XCUITest"
        options.udid = device.get("udid")
        options.no_reset = True
    else:  # Android
        options = UiAutomator2Options()
        options.platform_name = "Android"
        options.device_name = device.get("name")
        options.automation_name = "UiAutomator2"
        options.udid = device.get("udid")
        options.no_reset = True
    
    driver = webdriver.Remote(appium_server, options=options)
    return driver

def restart_app(driver, bundle_id):
    try:
        driver.terminate_app(bundle_id)
    except Exception:
        pass
    time.sleep(1)
    driver.execute_script("mobile: launchApp", {"bundleId": bundle_id})
    time.sleep(2)
