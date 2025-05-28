from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
options.binary_location = "/usr/bin/chromium"
options.add_argument("--headless=new")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(executable_path="/usr/bin/chromedriver", options=options)

driver.get("https://example.com")
print(driver.title)
driver.quit()
