from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

options = Options()
options.binary_location = "/usr/bin/chromium"  # Adjust if different
options.add_argument("--headless=new")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

service = Service("/usr/bin/chromedriver")  # Adjust if chromedriver is elsewhere

driver = webdriver.Chrome(service=service, options=options)

driver.get("https://example.com")
print(driver.title)
driver.quit()
