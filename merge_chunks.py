import os
import pandas as pd
import re
from glob import glob

INPUT_FOLDER = "downloads_daily_chunks"  # <-- Use your folder from download
OUTPUT_FOLDER = "merged"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Match pattern like: 5keywords_2020-07-01_to_2021-01-01.csv
file_pattern = re.compile(r"^(.*?)_\d{4}-\d{2}-\d{2}_to_\d{4}-\d{2}-\d{2}\.csv$")

grouped_files = {}

# Group files by prefix (e.g., '5keywords')
for file in glob(os.path.join(INPUT_FOLDER, "*.csv")):
    base = os.path.basename(file)
    match = file_pattern.match(base)
    if match:
        group_key = match.group(1)
        grouped_files.setdefault(group_key, []).append(file)

# Merge for each group
for group, files in grouped_files.items():
    print(f"\n🔄 Merging {len(files)} files for group: {group}")
    dfs = []
    headers = set()

    for file in sorted(files):
        with open(file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Find header row (starts with 'Day')
        header_index = 0
        for idx, line in enumerate(lines):
            if line.lower().startswith("day"):
                header_index = idx
                break

        df = pd.read_csv(file, skiprows=header_index)
        if "Day" not in df.columns:
            print(f"⚠️ Skipping file (no 'Day'): {file}")
            continue

        headers.add(tuple(df.columns))
        dfs.append(df)

    if not dfs:
        print(f"🚫 No valid CSVs found for group: {group}")
        continue

    # Merge logic
    if len(headers) > 1:
        print(f"⚠️ Column mismatch detected. Applying outer merge with renaming.")
        renamed_dfs = []
        for i, df in enumerate(dfs):
            df.columns = [col if col == "Day" else f"{col}_({i+1})" for col in df.columns]
            renamed_dfs.append(df)
        merged = renamed_dfs[0]
        for df in renamed_dfs[1:]:
            merged = pd.merge(merged, df, on="Day", how="outer")
    else:
        merged = pd.concat(dfs, ignore_index=True)
        merged = merged.groupby("Day", as_index=False).mean(numeric_only=True)

    # Final formatting
    merged.sort_values("Day", inplace=True)
    merged.reset_index(drop=True, inplace=True)

    output_file = os.path.join(OUTPUT_FOLDER, f"{group}_combined_daily.csv")
    merged.to_csv(output_file, index=False)
    print(f"✅ Saved merged file: {output_file}")
