"""Working
"""

import pychrome

# create a browser instance
browser = pychrome.Browser(url="http://127.0.0.1:9222")

# create a tab
tab = browser.new_tab()


# Define a callback to handle console messages
def handle_console_event(**kwargs):
    # print("event", event)
    print(kwargs)
    # for arg in kwargs.get("args", []):
    # print(f"Console Log: {arg['value']}")


# Set up the listener for console logs
tab.Runtime.consoleAPICalled = handle_console_event


# register callback if you want
def request_will_be_sent(**kwargs):
    print("loading: %s" % kwargs.get("request").get("url"))


# tab.Network.requestWillBeSent = request_will_be_sent

# start the tab
tab.start()


# Enable the necessary domains
tab.Runtime.enable()

tab.Page.navigate(url="https://google.com")

import time

time.sleep(3)
print("ready")


# Inject JavaScript to handle click events
tab.Runtime.evaluate(
    expression="""
    document.addEventListener('click', function(event) {
        console.log('Element clicked:', event.target.tagName);
    });
"""
)


# tab.Page.enable()

# call method
# tab.Network.enable()
# call method with timeout

# wait for loading
# tab.wait(100)

# stop the tab (stop handle events and stop recv message from chrome)
# tab.stop()

# close tab
# browser.close_tab(tab)

# Keep the script running to capture events
try:
    print("Script is running. Click on the page and check for console output.")
    print("Press Ctrl+C to stop.")
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Stopping...")

# Stop the tab and close it
tab.stop()
browser.close_tab(tab)
