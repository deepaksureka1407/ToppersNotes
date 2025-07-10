import os
import pandas as pd
from datetime import datetime, timedelta

# === CONFIGURATION ===
daily_file = os.path.join("merged", "5keywords_combined_daily.csv")
weekly_file = os.path.join("downloads_compare", f"geo_IN_compare.csv")
output_file = os.path.join("merged", "5keywords_combined_daily_scaled.csv")
step_months = 6

# === LOAD DAILY DATA ===
daily_df = pd.read_csv(daily_file)
daily_df["Day"] = pd.to_datetime(daily_df["Day"])

# === LOAD WEEKLY DATA === (skip first 2 metadata lines)
weekly_df = pd.read_csv(weekly_file, skiprows=2)
# Convert Week column to datetime
weekly_df["Week"] = pd.to_datetime(weekly_df["Week"])

# === Identify common trend columns (ignore date) ===
data_columns = [col for col in daily_df.columns if col != "Day"]

# === Define date range for chunking ===
start_date = daily_df["Day"].min()
end_date = daily_df["Day"].max()

current = start_date
scaled_chunks = []

# === SCALE EACH 6-MONTH CHUNK ===
while current < end_date:
    next_date = current + timedelta(days=30 * step_months)
    chunk_end = min(next_date, end_date)

    daily_chunk = daily_df[(daily_df["Day"] >= current) & (daily_df["Day"] < chunk_end)].copy()
    weekly_chunk = weekly_df[(weekly_df["Week"] >= current) & (weekly_df["Week"] < chunk_end)]

    if daily_chunk.empty or weekly_chunk.empty:
        print(f"⚠️ Skipping chunk {current.date()} to {chunk_end.date()} — no data")
        current = next_date
        continue

    print(f"🔄 Scaling chunk: {current.date()} → {chunk_end.date()}")

    for col in data_columns:
        # Ensure numeric data for both daily and weekly
        daily_chunk[col] = pd.to_numeric(daily_chunk[col], errors="coerce")
        weekly_chunk[col] = pd.to_numeric(weekly_chunk[col], errors="coerce")

        daily_avg = daily_chunk[col].mean()
        weekly_avg = weekly_chunk[col].mean()

        if pd.isna(daily_avg) or daily_avg == 0:
            scale_factor = 1
        else:
            scale_factor = weekly_avg / daily_avg

        daily_chunk[col] = daily_chunk[col] * scale_factor

    scaled_chunks.append(daily_chunk)
    current = next_date

# === MERGE AND SAVE FINAL OUTPUT ===
final_df = pd.concat(scaled_chunks)
final_df.sort_values("Day", inplace=True)
final_df.reset_index(drop=True, inplace=True)
final_df.to_csv(output_file, index=False)

print(f"\n✅ Done! Rescaled daily file saved as: {output_file}")
