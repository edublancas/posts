"""Not working
"""

from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.support.events import (
    EventFiringWebDriver,
    AbstractEventListener,
)


class MyListener(AbstractEventListener):
    def before_click(self, element, driver):
        print(f"About to click on {element.tag_name}")

    def after_click(self, element, driver):
        print(f"Clicked on {element.tag_name}")

    # You can override other methods like before_change_value_of, after_change_value_of, etc.


chrome_options = Options()
chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

driver = webdriver.Chrome(options=chrome_options)


# Wrap it in an EventFiringWebDriver
ef_driver = EventFiringWebDriver(driver, MyListener())

# Use ef_driver instead of driver for your Selenium operations
ef_driver.get("https://wikipedia.org")
