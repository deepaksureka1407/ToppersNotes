import pandas as pd
import os

# Load old scaled data
old_df = pd.read_csv("5keywords_combined_daily_scaled.csv", parse_dates=["date"])
old_df.set_index("date", inplace=True)

# Load latest incremental raw CSV
latest_file = sorted(
    [f for f in os.listdir("downloads_incremental") if f.endswith(".csv")],
    key=lambda x: os.path.getctime(os.path.join("downloads_incremental", x)),
    reverse=True
)[0]

new_df = pd.read_csv(os.path.join("downloads_incremental", latest_file), parse_dates=["Day"])
new_df.rename(columns={"Day": "date"}, inplace=True)
new_df.set_index("date", inplace=True)

# Intersect dates
common_dates = new_df.index.intersection(old_df.index)

if len(common_dates) == 0:
    print("❌ No common dates found between old and new data.")
    exit()

scaling_factors = {}

for col in new_df.columns:
    if col not in old_df.columns:
        print(f"⚠️ Skipping column '{col}' (not found in old data)")
        continue

    new_vals = new_df.loc[common_dates, col]
    old_vals = old_df.loc[common_dates, col]

    # Avoid divide by zero
    mask = (new_vals > 0) & (old_vals > 0)
    if mask.sum() == 0:
        print(f"⚠️ No valid overlap for column '{col}'")
        continue

    ratios = old_vals[mask] / new_vals[mask]
    scale = ratios.median()
    scaling_factors[col] = scale

    print(f"📏 Scaling factor for '{col}': {scale:.3f}")

# Optional: Apply scaling
scaled_new_df = new_df.copy()
for col, scale in scaling_factors.items():
    scaled_new_df[col] *= scale

# Save rescaled incremental
scaled_new_df.reset_index().to_csv("downloads_incremental/rescaled_incremental.csv", index=False)
print("✅ Saved scaled incremental data.")
