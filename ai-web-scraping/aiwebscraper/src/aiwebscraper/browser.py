import getpass
import random
import time

from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException


def find_text_by_xpath_if_exists(element, xpath):
    try:
        return element.find_element(By.XPATH, xpath).text
    except NoSuchElementException:
        return None


class Browser:
    def __init__(self, url, connect_to_existing=False) -> None:
        chrome_options = Options()

        if connect_to_existing:
            chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

        # required for running as root in a container
        if getpass.getuser() == "root":
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--headless")

        self.driver = webdriver.Chrome(options=chrome_options)

        self.wait_long = WebDriverWait(self.driver, 10)
        self.wait_short = WebDriverWait(self.driver, 2)
        self.driver.get(url)

    def find_element_by_xpath(self, xpath, wait_long=True):
        wait = self.wait_long if wait_long else self.wait_short
        return wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))

    def find_all_elements_by_xpath(self, xpath):
        return self.driver.find_elements(By.XPATH, xpath)

    def smooth_scroll(self, distance=500):
        self.driver.execute_script(
            f"window.scrollBy({{top: {distance}, behavior: 'smooth'}})"
        )
        self.wait_randomly(1.5, 2.5)

    def wait_randomly(self, low=1, high=2):
        time.sleep(random.uniform(low, high))
