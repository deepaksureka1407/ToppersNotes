import streamlit as st
import pandas as pd
import plotly.graph_objs as go
import numpy as np
import os
from datetime import timedelta
import subprocess
import datetime
import glob
import matplotlib.pyplot as plt
import re

# === Load Files ===
weekly_path = "downloads_compare/geo_IN_compare.csv"
daily_path = "merged/5keywords_combined_daily_scaled.csv"
meta_path = "meta/last_processed_date.txt"

weekly_df = pd.read_csv(weekly_path, skiprows=2)
daily_df = pd.read_csv(daily_path)

# Define fixed reference keyword
ref_keyword = "Combined Graduate Level Examination: (India)"

# Safe file name conversion
def safe_filename(name):
    return re.sub(r'[\\/:"*?<>|]+', "_", name)

safe_name = safe_filename(ref_keyword)
fixed_path = f"merged/{safe_name}_combined_daily_scaled.csv"

if os.path.exists(fixed_path):
    daily_fixed_df = pd.read_csv(fixed_path)
    daily_fixed_df.rename(columns={"Day": "Date"}, inplace=True)
    daily_fixed_df["Date"] = pd.to_datetime(daily_fixed_df["Date"])
else:
    st.warning("⚠️ Fixed reference scaled file not found. Skipping extra plot.")
    daily_fixed_df = None
weekly_df.rename(columns={"Week": "Date"}, inplace=True)
daily_df.rename(columns={"Day": "Date"}, inplace=True)

weekly_df["Date"] = pd.to_datetime(weekly_df["Date"])
daily_df["Date"] = pd.to_datetime(daily_df["Date"])

# Get common keywords
weekly_keywords = [col for col in weekly_df.columns if col != "Date"]
daily_keywords = [col for col in daily_df.columns if col != "Date"]
keywords = list(set(weekly_keywords) & set(daily_keywords))

# === UI ===
st.set_page_config(layout="wide")
st.title("📊 Google Trends Comparison Dashboard")
st.write("Comparison of original weekly and scaled daily data over 5 years.")

# === Weekly Chart ===
st.subheader("📘 Weekly Trend (Original)")
fig1 = go.Figure()
for kw in keywords:
    fig1.add_trace(go.Scatter(x=weekly_df["Date"], y=weekly_df[kw], mode="lines", name=kw))
fig1.update_layout(height=400, hovermode="x unified", template="plotly_white")
st.plotly_chart(fig1, use_container_width=True)

# === Daily Chart ===
st.subheader("🔴 Daily Trend (Scaled) with Weekly Averages")
fig2 = go.Figure()
for kw in keywords:
    fig2.add_trace(go.Scatter(x=daily_df["Date"], y=daily_df[kw], mode="lines", name=f"{kw} (Daily)"))

    # Add weekly avg to same chart
    weekly_avg = weekly_df[["Date", kw]].rename(columns={kw: f"{kw} (Weekly Avg)"})
    fig2.add_trace(go.Scatter(x=weekly_avg["Date"], y=weekly_avg[f"{kw} (Weekly Avg)"],
                              mode="lines", name=f"{kw} (Weekly Avg)", line=dict(dash="dot")))

fig2.update_layout(height=400, hovermode="x unified", template="plotly_white")
st.plotly_chart(fig2, use_container_width=True)

if daily_fixed_df is not None:
    st.subheader(f"🟢 Daily Trend (Fixed Reference: `{ref_keyword}`)")
    fig_fixed = go.Figure()
    for kw in keywords:
        if kw in daily_fixed_df.columns:
            fig_fixed.add_trace(go.Scatter(x=daily_fixed_df["Date"], y=daily_fixed_df[kw], mode="lines", name=kw))
    fig_fixed.update_layout(
        height=400,
        hovermode="x unified",
        template="plotly_white"
    )
    st.plotly_chart(fig_fixed, use_container_width=True)


# Get common keywords (already calculated above)
for kw in keywords:
    st.markdown(f"### 📈 Keyword: `{kw}`")

    fig, ax = plt.subplots(figsize=(10, 4))

    # Plot weekly data
    ax.plot(weekly_df["Date"], weekly_df[kw], label="Weekly (Original)", linestyle="--", alpha=0.7)

    # Plot daily scaled data (fixed reference)
    ax.plot(daily_df["Date"], daily_df[kw], label="Daily (Rescaled with Fixed Reference)", alpha=0.9)

    ax.set_ylabel("Interest")
    ax.set_xlabel("Date")
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)

# === AUC Comparison Every 6 Months ===
st.subheader("📀 Area Under Curve (AUC) Comparison — Every 6 Months")
start_date = weekly_df["Date"].min().normalize()
end_date = weekly_df["Date"].max().normalize()
chunks = []

while start_date < end_date:
    next_date = start_date + pd.DateOffset(months=6)
    chunks.append((start_date, min(next_date, end_date)))
    start_date = next_date

auc_rows = []

for kw in keywords:
    for start, end in chunks:
        w_chunk = weekly_df[(weekly_df["Date"] >= start) & (weekly_df["Date"] < end)].dropna()
        d_chunk = daily_df[(daily_df["Date"] >= start) & (daily_df["Date"] < end)].dropna()

        w_values = pd.to_numeric(w_chunk[kw], errors="coerce").fillna(0)
        d_values = pd.to_numeric(d_chunk[kw], errors="coerce").fillna(0)

        if len(w_values) < 2 or len(d_values) < 2:
            continue

        w_auc = np.trapz(w_values, x=w_chunk["Date"].astype(np.int64) / 1e9)
        d_auc = np.trapz(d_values, x=d_chunk["Date"].astype(np.int64) / 1e9)
        ratio = d_auc / w_auc if w_auc else np.nan

        auc_rows.append({
            "Keyword": kw,
            "Start": start.date(),
            "End": end.date(),
            "Weekly AUC": round(w_auc, 2),
            "Daily AUC": round(d_auc, 2),
            "AUC Ratio (Daily / Weekly)": round(ratio, 4) if w_auc else "-"
        })

st.dataframe(pd.DataFrame(auc_rows), use_container_width=True)

# === AUC Ratio Bar Chart ===
st.subheader("📈 AUC Ratio Trend (Bar Chart)")
for kw in keywords:
    chunk_labels = [f"{row['Start']}→{row['End']}" for row in auc_rows if row["Keyword"] == kw]
    ratios = [row["AUC Ratio (Daily / Weekly)"] for row in auc_rows if row["Keyword"] == kw]

    if ratios:
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(x=chunk_labels, y=ratios, name=kw))
        fig_bar.update_layout(title=f"AUC Ratios for '{kw}'", yaxis_title="Daily / Weekly AUC",
                              xaxis_title="6-Month Chunks", height=400)
        st.plotly_chart(fig_bar, use_container_width=True)

# === NEW: Recent N-Day Update Section ===
st.subheader("🆕 Recent Update Comparison")

# Load last processed date if exists
last_processed_date = None
if os.path.exists(meta_path):
    with open(meta_path, 'r') as f:
        last_processed_date = pd.to_datetime(f.read().strip())

if last_processed_date:
    st.info(f"Last update was until: {last_processed_date.date()}")
    recent_start = last_processed_date + timedelta(days=1)
    recent_end = max(weekly_df["Date"].max(), daily_df["Date"].max())
    st.write(f"Checking data from {recent_start.date()} to {recent_end.date()}")

    update_rows = []
    for kw in keywords:
        w_recent = weekly_df[(weekly_df["Date"] >= recent_start)].dropna()
        d_recent = daily_df[(daily_df["Date"] >= recent_start)].dropna()

        w_vals = pd.to_numeric(w_recent[kw], errors="coerce").fillna(0)
        d_vals = pd.to_numeric(d_recent[kw], errors="coerce").fillna(0)

        if len(w_vals) > 1 and len(d_vals) > 1:
            w_auc = np.trapz(w_vals, x=w_recent["Date"].astype(np.int64) / 1e9)
            d_auc = np.trapz(d_vals, x=d_recent["Date"].astype(np.int64) / 1e9)
            ratio = d_auc / w_auc if w_auc else np.nan

            update_rows.append({
                "Keyword": kw,
                "Start": recent_start.date(),
                "End": recent_end.date(),
                "Weekly AUC": round(w_auc, 2),
                "Daily AUC": round(d_auc, 2),
                "AUC Ratio": round(ratio, 4) if w_auc else "-"
            })

    if update_rows:
        st.dataframe(pd.DataFrame(update_rows), use_container_width=True)
else:
    st.warning("No meta/last_processed_date.txt found. Create it to enable incremental comparison.")

# === Detect & Process Only New Data ===
st.subheader("🆕 Newly Added Data Analysis (Incremental)")

history_file = "auc_history.csv"
last_date = None

if os.path.exists(history_file):
    hist_df = pd.read_csv(history_file)
    last_date = pd.to_datetime(hist_df["End"]).max()
else:
    hist_df = pd.DataFrame()

# Determine new time window
new_start = last_date + pd.Timedelta(days=1) if last_date else weekly_df["Date"].min()
new_end = weekly_df["Date"].max()

if new_start >= new_end:
    st.info("✅ No new data to process. All data already analyzed.")
else:
    st.success(f"🔄 Analyzing new data from **{new_start.date()}** to **{new_end.date()}**")

    new_rows = []
    for kw in keywords:
        w_chunk = weekly_df[(weekly_df["Date"] >= new_start) & (weekly_df["Date"] <= new_end)].dropna()
        d_chunk = daily_df[(daily_df["Date"] >= new_start) & (daily_df["Date"] <= new_end)].dropna()

        if w_chunk.empty or d_chunk.empty:
            continue

        w_values = pd.to_numeric(w_chunk[kw], errors="coerce").fillna(0)
        d_values = pd.to_numeric(d_chunk[kw], errors="coerce").fillna(0)

        if len(w_values) < 2 or len(d_values) < 2:
            continue

        w_auc = np.trapz(w_values, x=w_chunk["Date"][:len(w_values)].astype(np.int64) / 1e9)
        d_auc = np.trapz(d_values, x=d_chunk["Date"][:len(d_values)].astype(np.int64) / 1e9)
        ratio = d_auc / w_auc if w_auc else np.nan

        new_rows.append({
            "Keyword": kw,
            "Start": new_start.date(),
            "End": new_end.date(),
            "Weekly AUC": round(w_auc, 2),
            "Daily AUC": round(d_auc, 2),
            "AUC Ratio (Daily / Weekly)": round(ratio, 4) if w_auc else "-"
        })

    if new_rows:
        new_df = pd.DataFrame(new_rows)
        st.dataframe(new_df, use_container_width=True)

        # Append to history
        updated_df = pd.concat([hist_df, new_df], ignore_index=True)
        updated_df.to_csv(history_file, index=False)
        st.success("✅ New AUC results saved to 'auc_history.csv'")
    else:
        st.warning("⚠️ No valid new data rows to process.")

st.markdown("---")
st.subheader("🔄 Fetch & Append New Google Trends Data")

# Read last processed date
with open("meta/last_processed_date.txt", "r") as f:
    last_processed_date = datetime.datetime.strptime(f.read().strip(), "%Y-%m-%d").date()

today = datetime.date.today()
st.info(f"Last processed date: {last_processed_date}")

if today <= last_processed_date:
    st.success("✅ Data is already up to date!")
else:
    if st.button("📥 Fetch Incremental Google Trends Data"):
        st.write(f"📆 Fetching daily data from {last_processed_date + datetime.timedelta(days=1)} to {today}...")

        # Call the new incremental scraper
        result = subprocess.run(["python", "google_trends_incremental_scraper.py", str(last_processed_date + datetime.timedelta(days=1)), str(today)], capture_output=True, text=True)

        if result.returncode == 0:
            st.success("✅ New incremental data scraped successfully!")
            st.text(result.stdout)

            # Find latest downloaded CSV file
            files = glob.glob("downloads_incremental/*.csv")
            if files:
                latest_file = max(files, key=os.path.getctime)
                st.info(f"📄 Showing recently downloaded file: `{os.path.basename(latest_file)}`")

                # Read and show dataframe
                df = pd.read_csv(latest_file)
                st.dataframe(df)
            else:
                st.warning("⚠️ No downloaded file found to display.")
        else:
            st.error("❌ Failed to scrape data.")
            st.text(result.stderr)

# Run fixed-reference rescaler
REFERENCE_KEYWORD = "Combined Graduate Level Examination: (India)"
st.info(f"📌 Rescaling daily chunks using reference: {REFERENCE_KEYWORD}")

result = subprocess.run(
    ["python", "rescale_chunks_fixed_reference.py", REFERENCE_KEYWORD],
    capture_output=True, text=True
)

if result.returncode == 0:
    st.success("✅ Daily data successfully rescaled using fixed reference.")
    st.text(result.stdout)
else:
    st.error("❌ Failed to rescale daily data with fixed reference.")
    st.text(result.stderr)

st.markdown("### 📊 Scaling Factor Comparison (New Data vs. Historical Daily)")

try:
    # 1. Load historical data
    df_hist = pd.read_csv("merged/5keywords_combined_daily_scaled.csv", parse_dates=["Day"])

    # 2. Find latest incremental file
    incremental_files = sorted(glob.glob("downloads_incremental/geo_IN_*.csv"), reverse=True)
    if not incremental_files:
        st.warning("⚠️ No new incremental file found.")
    else:
        latest_file = incremental_files[0]
        df_new = pd.read_csv(latest_file, skiprows=1)  # skip metadata
        df_new.rename(columns={df_new.columns[0]: "Day"}, inplace=True)
        df_new["Day"] = pd.to_datetime(df_new["Day"])

        # 3. Scaling factor calculation
        results = []
        for col in df_new.columns[1:]:
            if col not in df_hist.columns:
                continue

            merged = pd.merge(
                df_hist[["Day", col]], 
                df_new[["Day", col]], 
                on="Day", 
                suffixes=("_hist", "_new")
            )

            if merged.empty:
                continue

            old_mean = merged[f"{col}_hist"].mean()
            new_mean = merged[f"{col}_new"].mean()
            scaling = round(old_mean / new_mean, 3) if new_mean != 0 else "∞"

            results.append({
                "Keyword": col,
                "Historical Mean": round(old_mean, 2),
                "New Data Mean": round(new_mean, 2),
                "Scaling Factor": scaling
            })

        if results:
            st.dataframe(pd.DataFrame(results))
        else:
            st.info("No matching keywords found for scaling comparison.")

except Exception as e:
    st.error("❌ Error comparing new and historical data.")
    st.text(str(e))