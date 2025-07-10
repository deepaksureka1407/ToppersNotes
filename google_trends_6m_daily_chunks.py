import csv
import os
import time
from urllib.parse import quote_plus
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
from collections import Counter

# === CONFIGURATION ===
CSV_FILE = "keywords.csv"
OUTPUT_DIR = "downloads_daily_chunks"
WAIT_TIME = 5

# === SETUP OUTPUT DIRECTORY ===
if os.path.exists(OUTPUT_DIR):
    for file in os.listdir(OUTPUT_DIR):
        os.remove(os.path.join(OUTPUT_DIR, file))
else:
    os.makedirs(OUTPUT_DIR)

# === SETUP CHROME ===
options = Options()
options.add_argument("--user-data-dir=C:/Users/lenovo/ChromeProfile")  # Adjust if needed
prefs = {
    "download.default_directory": os.path.abspath(OUTPUT_DIR),
    "profile.default_content_settings.popups": 0,
    "download.prompt_for_download": False,
    "safebrowsing.enabled": True
}
options.add_experimental_option("prefs", prefs)
driver = webdriver.Chrome(options=options)

# === HELPERS ===
def wait_for_download(file_path, timeout=30):
    waited = 0
    while not os.path.exists(file_path) and waited < timeout:
        time.sleep(1)
        waited += 1
    return os.path.exists(file_path)

def click_download_button():
    try:
        print("⬇️ Clicking download...")
        download_btn = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.widget-actions-item.export[title='CSV']"))
        )
        driver.execute_script("arguments[0].click();", download_btn)
        print("✅ CSV download initiated.")
    except Exception as e:
        print(f"❌ Download button error: {e}")

def get_6_month_ranges(start_date, end_date):
    ranges = []
    current = start_date
    while current < end_date:
        next_date = current + timedelta(days=30*6)
        if next_date > end_date:
            next_date = end_date
        ranges.append((current.strftime('%Y-%m-%d'), next_date.strftime('%Y-%m-%d')))
        current = next_date
    return ranges

# === READ KEYWORDS CSV ===
keywords = []
geos = []

with open(CSV_FILE, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        keywords.append(row['google_trends_keywords'].strip())
        geos.append(row['geo'].strip())

if len(set(keywords)) < 2:
    print("❌ Need at least 2 unique keywords for comparison.")
    driver.quit()
    exit()

# === USE MOST COMMON GEO (OR SET FIXED) ===
geo = Counter(geos).most_common(1)[0][0]
print(f"\n🌍 Using GEO: {geo}")

# === CREATE DATE RANGES ===
end = datetime.now()
start = end - timedelta(days=5*365)
date_ranges = get_6_month_ranges(start, end)

# === RUN LOOP FOR EACH 6-MONTH INTERVAL ===
q_param = ",".join(quote_plus(k) for k in keywords)
safe_name = "5keywords"  # or build from names if needed

for date_start, date_end in date_ranges:
    url = f"https://trends.google.com/trends/explore?date={date_start}%20{date_end}&geo={geo}&gprop=youtube&q={q_param}&hl=en"
    print(f"\n📊 {date_start} → {date_end}")
    print("🔗", url)

    driver.get(url)
    time.sleep(5)

    # CAPTCHA Check
    if "captcha" in driver.page_source.lower() or "robot" in driver.page_source.lower():
        print("🤖 CAPTCHA detected. Please solve it manually.")
        input("🔓 Press Enter once done...")

    # Download
    click_download_button()
    downloaded_file = os.path.join(OUTPUT_DIR, "multiTimeline.csv")
    new_name = f"{safe_name}_{date_start}_to_{date_end}.csv"
    new_path = os.path.join(OUTPUT_DIR, new_name)

    if wait_for_download(downloaded_file):
        if os.path.exists(new_path):
            os.remove(new_path)
        os.rename(downloaded_file, new_path)
        print(f"📥 Saved: {new_name}")
    else:
        print("❌ Download failed or timeout.")

    time.sleep(WAIT_TIME + 2)

driver.quit()
