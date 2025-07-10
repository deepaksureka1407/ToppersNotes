import csv
import os
import time
import sys
from urllib.parse import quote_plus
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

CSV_FILE = sys.argv[1] if len(sys.argv) > 1 else "keywords.csv"
OUTPUT_DIR = "downloads_compare"
WAIT_TIME = 5

# Step 1: Clean output folder
if os.path.exists(OUTPUT_DIR):
    for file in os.listdir(OUTPUT_DIR):
        os.remove(os.path.join(OUTPUT_DIR, file))
else:
    os.makedirs(OUTPUT_DIR)

# Step 2: Setup Chrome with download folder
options = Options()
options.add_argument("--user-data-dir=C:/Users/lenovo/ChromeProfile")  # Update if needed
prefs = {
    "download.default_directory": os.path.abspath(OUTPUT_DIR),
    "profile.default_content_settings.popups": 0,
    "download.prompt_for_download": False,
    "safebrowsing.enabled": True
}
options.add_experimental_option("prefs", prefs)
driver = webdriver.Chrome(options=options)

# Step 3: Wait for download to complete
def wait_for_download(file_path, timeout=20):
    waited = 0
    while not os.path.exists(file_path) and waited < timeout:
        time.sleep(1)
        waited += 1
    return os.path.exists(file_path)

# Step 4: Click download
def click_download_button(driver):
    try:
        print("⬇️ Looking for download button...")
        download_btn = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.widget-actions-item.export[title='CSV']"))
        )
        driver.execute_script("arguments[0].click();", download_btn)
        print("✅ Download initiated.")
    except Exception as e:
        print(f"❌ Download button error: {e}")

# Step 5: Load CSV data
if not os.path.exists(CSV_FILE):
    print(f"❌ CSV file not found: {CSV_FILE}")
    driver.quit()
    exit()

data_by_geo = {}
with open(CSV_FILE, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        geo = row['geo']
        if geo not in data_by_geo:
            data_by_geo[geo] = []
        data_by_geo[geo].append(row['google_trends_keywords'])

# Step 6: Process each geo group
for geo, topic_codes in data_by_geo.items():
    if len(topic_codes) < 2:
        print(f"⚠️ Skipping geo '{geo}' — less than 2 keywords.")
        continue

    q_param = ",".join(quote_plus(code.strip()) for code in topic_codes)
    url = f"https://trends.google.com/trends/explore?date=today%205-y&geo={geo}&gprop=youtube&q={q_param}&hl=en"

    print(f"\n📊 Comparing topics for geo '{geo}'")
    print("🔗", url)
    driver.get(url)
    time.sleep(5)

    # CAPTCHA check
    if "robot" in driver.page_source.lower() or "captcha" in driver.page_source.lower():
        print("🤖 CAPTCHA triggered. Please solve manually...")
        input("🔓 Press Enter after solving CAPTCHA...")

    # Download
    click_download_button(driver)
    downloaded_file = os.path.join(OUTPUT_DIR, "multiTimeline.csv")
    new_name = f"geo_{geo}_compare.csv"
    new_path = os.path.join(OUTPUT_DIR, new_name)

    if wait_for_download(downloaded_file):
        if os.path.exists(new_path):
            os.remove(new_path)
        os.rename(downloaded_file, new_path)
        print(f"📥 Saved as {new_name}")
    else:
        print(f"❌ Download failed or timed out for geo: {geo}")

    time.sleep(WAIT_TIME)

driver.quit()
