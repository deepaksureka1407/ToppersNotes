import pandas as pd
import os
import re

def safe_filename(name):
    return re.sub(r'[\\/:"*?<>|]+', "_", name)

# === SETTINGS ===
REFERENCE_KEYWORD = "Combined Graduate Level Examination: (India)"
INPUT_FOLDER = "downloads_daily_chunks"
OUTPUT_FOLDER = "merged"

safe_keyword = safe_filename(REFERENCE_KEYWORD)
output_file = f"{OUTPUT_FOLDER}/{safe_keyword}_combined_daily_scaled.csv"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# === STEP 1: Gather all daily chunk CSVs ===
files = sorted([
    os.path.join(INPUT_FOLDER, f)
    for f in os.listdir(INPUT_FOLDER)
    if f.endswith(".csv")
])

if not files:
    print("[ERROR] No files found in downloads_daily_chunks/")
    exit()

# === STEP 2: Find GLOBAL MAX of the reference keyword across all chunks ===
global_max = 0
for file in files:
    df = pd.read_csv(file, skiprows=2)
    if REFERENCE_KEYWORD not in df.columns:
        print(f"[ERROR] Reference keyword '{REFERENCE_KEYWORD}' not found in {file}")
        exit()
    ref_vals = pd.to_numeric(df[REFERENCE_KEYWORD], errors="coerce").fillna(0)
    global_max = max(global_max, ref_vals.max())

print(f" Global max for '{REFERENCE_KEYWORD}': {global_max}")

# Step 3: Scale others relative to reference keyword
rescaled_chunks = []

for file in files:
    df = pd.read_csv(file, skiprows=2)
    df.rename(columns={"Day": "Date"}, inplace=True)
    df["Date"] = pd.to_datetime(df["Date"])
    
    df_scaled = df.copy()
    ref_col = pd.to_numeric(df[REFERENCE_KEYWORD], errors="coerce").fillna(0)

    for col in df.columns:
        if col != "Date" and col != REFERENCE_KEYWORD:
            other_col = pd.to_numeric(df[col], errors="coerce").fillna(0)
            df_scaled[col] = (other_col / ref_col.replace(0, pd.NA)) * 100  # avoid div by 0
            df_scaled[col] = df_scaled[col].fillna(0)
    
    df_scaled[REFERENCE_KEYWORD] = ref_col  # keep ref keyword unchanged
    rescaled_chunks.append(df_scaled)

# === STEP 4: Concatenate all chunks and save ===
final_df = pd.concat(rescaled_chunks).sort_values("Date")
final_df.to_csv(output_file, index=False)
print(f"Saved combined scaled data to {output_file}")