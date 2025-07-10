import streamlit as st
import pandas as pd
import plotly.graph_objs as go
import numpy as np
import os
from datetime import timedelta

# === Load Files ===
weekly_path = "downloads_compare/geo_IN_compare.csv"
daily_path = "merged/5keywords_combined_daily_scaled.csv"
meta_path = "meta/last_processed_date.txt"

weekly_df = pd.read_csv(weekly_path, skiprows=2)
daily_df = pd.read_csv(daily_path)

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
