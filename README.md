# 📈 ToppersNotes Google Trends Analyzer

This project automates the end-to-end analysis of Google Trends data (YouTube search) for top 200 exams using both **weekly** and **daily** data over the past 5 years. It scales daily data against weekly averages, plots interactive visualizations, and compares the **Area Under the Curve (AUC)** for accuracy and trend alignment.

---

## 🚀 Features

📅 **Scrape Google Trends data**
📅 Supports 5 keywords per comparison
📅 Daily data scraped in 6-month chunks
📅 Weekly data scraped for full 5 years
📅 Daily values **scaled** using weekly AUC
📅 Interactive Streamlit dashboard
📅 AUC comparison in every 6-month interval
📅 Supports **incremental updates** when new data is added
📅 Charts with toggleable visibility for all keywords
📅 Bar chart to track AUC match % (Daily/Weekly)

---

## 📁 Project Structure

```
ToppersNotes/
├── app.py                          # Streamlit Dashboard
├── google_trends_6months.py       # Script to scrape daily 5y data in 6m chunks
├── google_trends_5y_weekly.py     # Script to scrape weekly 5y comparison
├── merge_chunks.py                # Merge daily chunks into a single file
├── google_trends_5y_daily_rescaled.py  # Scale daily using weekly AUC
├── last_processed_date.txt        # Tracks last processed date for incremental updates
├── downloads/                     # Raw CSV downloads from Google Trends
├── downloads_compare/             # Weekly trend CSVs (e.g. geo_IN_compare.csv)
├── merged/                        # Final merged & scaled daily CSVs
├── trend_csvs/                    # (Optional) trend charts from Google Trends
├── keywords.csv                   # Input keyword list with geo and name
├── templates/                     # HTML or CSV template support (optional)
└── README.md                      # ← This file
```

---

## 📆 Dependencies

Install all required packages via:

```bash
pip install -r requirements.txt
```

Minimal list includes:

```text
streamlit
pandas
numpy
plotly
selenium
```

---

## 📄 Keywords CSV Format

Input file: `keywords.csv`

```csv
name,keyword,geo,category_code
SSC CGL,/g/11c265kd70,IN,45
NDA,/g/11gxpsg25n,IN,45
...
```

---

## 🔠 Usage

### 1. Scrape Weekly Data (5 years)

```bash
python google_trends_5y_weekly.py
```

Generates file:
`downloads_compare/geo_IN_compare.csv`

---

### 2. Scrape Daily Data (6-month chunks for 5 years)

```bash
python google_trends_6months.py
```

Files saved in: `downloads_daily_chunks/`

---

### 3. Merge Daily Chunks

```bash
python merge_chunks.py
```

Creates file:
`merged/5keywords_combined_daily.csv`

---

### 4. Scale Daily Data using Weekly Averages

```bash
python google_trends_5y_daily_rescaled.py
```

Creates file:
`merged/5keywords_combined_daily_scaled.csv`

---

### 5. Launch Streamlit Dashboard

```bash
streamlit run app.py
```

---

## 📊 Dashboard Features

* 📘 Weekly trend line chart
* 🔴 Daily trend (after scaling) line chart
* 📐 AUC comparison table (every 6 months)
* 📈 AUC ratio bar chart for each keyword
* 🟢 **Weekly average overlay** on daily chart
* 🔄 Support for incremental new data updates (only updates new days based on `last_processed_date.txt`)

---

## 📅 Incremental Data Update Support

Once processed, the script stores the **last processed date** in:

```
last_processed_date.txt
```

Next time you rerun the scraper or dashboard, it only updates with **new daily/weekly data after this date** — improving performance and preventing re-scaling the entire dataset again.

---

## 📃 License

MIT License © 2025 [Deepak Sureka](https://github.com/deepaksureka1407)

---

## 🙌 Acknowledgements

This project is built using:

* Google Trends Web Interface (YouTube Search)
* Streamlit
* Plotly
* NumPy
* Pandas
