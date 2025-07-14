# 📊 ToppersNotes Google Trends Analyzer

A fully automated and interactive platform to scrape, process, compare, and visualize Google Trends data for 5 different keywords — including long-term trends (5 years), weekly views, and daily comparisons with scaling.

This project is built using **Python**, **Pandas**, and **Streamlit**.

---

## 🚀 Features

- 🔍 Scrape Google Trends data for 5 keyword limit
- 📆 Compare weekly and daily interest over time (IOT)
- 📐 Automatically calculate and apply **scaling factors**
- 🧮 Support for **incremental updates** (only new data is fetched)
- 🧷 **Fixed Reference Scaling** mode to anchor all other keywords to a single reference (e.g., SSC CGL)
- 📊 Streamlit dashboard with interactive visualizations
- ☁️ One-click deploy on Streamlit Cloud

---

## 📁 Project Structure

```

ToopersNotes/
├── app.py                            # Main Streamlit dashboard
├── google\_trends\_5y\_weekly.py        # Scraper for 5-year weekly data
├── google\_trends\_6m\_daily\_chunks.py  # Scraper for daily 6-month chunks
├── merge\_chunks.py                   # Merge chunked daily data
├── rescale\_chunks\_fixed\_reference.py # Scale daily data using fixed keyword
├── calculate\_incremental\_scaling.py  # Incremental scaling update script
├── google\_trends\_incremental\_scraper.py
├── meta/
│   └── last\_processed\_date.txt       # Stores the last processed date
├── merged/                           # Output: merged/scaled CSVs
├── downloads\_daily\_chunks/           # Input: chunked daily CSVs
├── downloads\_compare/                # Input: weekly CSVs
├── downloads\_incremental/            # Input: new incremental daily scrapes
├── keywords.csv                      # Master keyword+geo+category list
├── requirements.txt                  # Python dependencies
└── README.md                         # You're here!

````

---

## 🔧 How to Run

### 1. Clone and install

```bash
git clone https://github.com/deepaksureka1407/ToopersNotes.git
cd ToopersNotes
pip install -r requirements.txt
````

### 2. Run the web app

```bash
streamlit run app.py
```

> 📝 Make sure your `merged/` and `downloads_compare/` folders contain the required CSVs before launching the app.

---

## 🌐 Deployed App

🔗 [Try the Live Demo](https://tpntstrendsanalyser.streamlit.app/)

---

## 📐 Fixed Reference Scaling (What is this?)

Google Trends uses a **dynamic scale** — meaning the highest point in any search is set to 100. This makes **cross-keyword comparisons unreliable**, especially across time or locations.

To fix this, we introduce **Fixed Reference Scaling**:

* Set one dominant keyword (e.g. **SSC CGL**) as the **absolute reference**
* All other keywords are scaled **relative to it**
* Ensures that comparisons stay consistent across all time chunks

---

## 🧠 Use Cases

* Analyze popularity trends across exams
* Compare interest levels between regions or exam categories
* Track exam seasonality, peak demand, and emerging patterns

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

## 🙌 Contributing

We welcome PRs, ideas, and feedback!
Please check [`CONTRIBUTING.md`](CONTRIBUTING.md) to get started.

