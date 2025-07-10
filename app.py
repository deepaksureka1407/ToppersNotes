import streamlit as st
import pandas as pd
import plotly.graph_objs as go
import numpy as np

# === Load Files ===
weekly_path = "downloads_compare/geo_IN_compare.csv"
daily_path = "merged/5keywords_combined_daily_scaled.csv"

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
st.subheader("🔴 Daily Trend (Scaled)")
fig2 = go.Figure()
for kw in keywords:
    fig2.add_trace(go.Scatter(x=daily_df["Date"], y=daily_df[kw], mode="lines", name=kw))
fig2.update_layout(height=400, hovermode="x unified", template="plotly_white")
st.plotly_chart(fig2, use_container_width=True)

# === AUC Comparison ===
st.subheader("📐 Area Under Curve (AUC) Comparison — Every 6 Months")
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

        w_values = w_chunk[kw].dropna()
        d_values = d_chunk[kw].dropna()

        if len(w_values) < 2 or len(d_values) < 2:
            continue
        # Convert to numeric, replacing "<1" or non-numeric values with 0
        w_numeric = pd.to_numeric(w_values, errors="coerce").fillna(0)
        d_numeric = pd.to_numeric(d_values, errors="coerce").fillna(0)

        # Compute AUC using numeric values
        w_auc = np.trapz(w_numeric, x=w_chunk["Date"][:len(w_numeric)].astype(np.int64) / 1e9)
        d_auc = np.trapz(d_numeric, x=d_chunk["Date"][:len(d_numeric)].astype(np.int64) / 1e9)
        ratio = d_auc / w_auc if w_auc else np.nan

        auc_rows.append({
            "Keyword": kw,
            "Start": start.date(),
            "End": end.date(),
            "Weekly AUC": round(w_auc, 2),
            "Daily AUC": round(d_auc, 2),
            "AUC Ratio (Daily / Weekly)": round(ratio, 4) if w_auc else "-"
        })

# Show table
auc_df = pd.DataFrame(auc_rows)
st.dataframe(auc_df, use_container_width=True)

# === Optional: Plot AUC Ratios ===
st.subheader("📈 AUC Ratio Trend (Bar Chart)")

for kw in keywords:
    chunk_labels = [f"{row['Start']}→{row['End']}" for row in auc_rows if row["Keyword"] == kw]
    ratios = [row["AUC Ratio (Daily / Weekly)"] for row in auc_rows if row["Keyword"] == kw]

    if ratios:
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(x=chunk_labels, y=ratios, name=kw))
        fig_bar.update_layout(title=f"AUC Ratios for '{kw}'", yaxis_title="Daily / Weekly AUC", xaxis_title="6-Month Chunks", height=400)
        st.plotly_chart(fig_bar, use_container_width=True)
