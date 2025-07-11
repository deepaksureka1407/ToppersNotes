import csv
import os
import sys
import time
import datetime
from urllib.parse import quote_plus
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ========== CLI DATE RANGE ==========
if len(sys.argv) < 3:
    print("[ERROR] Please provide start and end dates in YYYY-MM-DD format.")
    print("Example: python google_trends_incremental_scraper.py 2025-07-01 2025-07-11")
    sys.exit(1)

start_date = sys.argv[1]
end_date = sys.argv[2]

# ========== CONFIG ==========
CSV_FILE = "keywords.csv"
OUTPUT_DIR = "downloads_incremental"
WAIT_TIME = 5

# ========== SETUP ==========
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Chrome setup
options = Options()
options.add_argument("--user-data-dir=C:/Users/lenovo/ChromeProfile")  # ✅ Your existing profile
prefs = {
    "download.default_directory": os.path.abspath(OUTPUT_DIR),
    "profile.default_content_settings.popups": 0,
    "download.prompt_for_download": False,
    "safebrowsing.enabled": True
}
options.add_experimental_option("prefs", prefs)
driver = webdriver.Chrome(options=options)

def wait_for_download(file_path, timeout=20):
    waited = 0
    while not os.path.exists(file_path) and waited < timeout:
        time.sleep(1)
        waited += 1
    return os.path.exists(file_path)

def click_download_button(driver):
    try:
        print(" Looking for download button...")
        download_btn = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.widget-actions-item.export[title='CSV']"))
        )
        driver.execute_script("arguments[0].click();", download_btn)
        print(" Download initiated.")
    except Exception as e:
        print(f"[ERROR] Download button error: {e}")

# ========== LOAD KEYWORDS ==========
if not os.path.exists(CSV_FILE):
    print(f"[ERROR] CSV file not found: {CSV_FILE}")
    driver.quit()
    sys.exit(1)

data_by_geo = {}
with open(CSV_FILE, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        geo = row['geo']
        if geo not in data_by_geo:
            data_by_geo[geo] = []
        data_by_geo[geo].append(row['google_trends_keywords'])

# ========== PROCESS EACH GEO ==========
for geo, topic_codes in data_by_geo.items():
    if len(topic_codes) < 2:
        print(f"[ATTENTION] Skipping geo '{geo}' — less than 2 keywords.")
        continue

    q_param = ",".join(quote_plus(code.strip()) for code in topic_codes)
    date_param = f"{start_date} {end_date}"
    url = f"https://trends.google.com/trends/explore?date={date_param}&geo={geo}&gprop=youtube&q={q_param}&hl=en"

    print(f"\n Fetching daily trends for geo '{geo}' from {start_date} to {end_date}")
    print("Link: ", url)
    driver.get(url)
    time.sleep(5)

    # CAPTCHA check
    if "robot" in driver.page_source.lower() or "captcha" in driver.page_source.lower():
        print(" CAPTCHA triggered. Please solve manually...")
        input(" Press Enter after solving CAPTCHA...")

    # Download
    click_download_button(driver)
    downloaded_file = os.path.join(OUTPUT_DIR, "multiTimeline.csv")
    new_name = f"geo_{geo}_{start_date}_to_{end_date}_compare.csv"
    new_path = os.path.join(OUTPUT_DIR, new_name)

    if wait_for_download(downloaded_file):
        if os.path.exists(new_path):
            os.remove(new_path)
        os.rename(downloaded_file, new_path)
        print(f" Saved: {new_name}")
    else:
        print(f"[ERROR] Download failed or timed out for geo: {geo}")

    time.sleep(WAIT_TIME)

driver.quit()
print("Done scraping all geos.")
