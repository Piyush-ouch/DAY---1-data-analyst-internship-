# Bluestock Mutual Fund ETL & Data Ingestion System
## Day 1: Project Setup + Data Ingestion (ETL)

Welcome to the **Bluestock Data Analyst Internship - Day 1** project repository. This repository contains a production-grade, highly optimized ETL (Extract, Transform, Load) pipeline and live data ingestion system built using Python and Pandas.

The system handles batch loading and analysis of historical mutual fund datasets, validates data integrity, and performs multithreaded fetching of live/historical NAV (Net Asset Value) data from the public Mutual Fund API (`mfapi.in`).

---

## 🚀 Key Features

* **High-Performance Ingestion**: Uses optimal pandas data types (`float32`, `int32`, `int16`, `int8`) to reduce memory footprint by up to 60%.
* **Multithreaded API Client**: Concurrent fetching of historical/live NAVs for mutual fund schemes using Python's `ThreadPoolExecutor` and socket connection pooling (`requests.Session`).
* **Data Quality Profiling**: Auto-generates a detailed quality report documenting dataset shapes, missing values, duplicate rows, and data anomalies.
* **Referential Integrity Validation**: Validates AMFI codes across datasets to ensure perfect relational mapping.
* **Discrepancy Logging**: Identifies mapping anomalies between client-defined scheme names and actual API meta-responses.

---

## 📁 Repository Structure

```text
├── data/
│   ├── raw/
│   │   ├── 01_fund_master.csv           # Master list of mutual fund schemes
│   │   ├── 02_nav_history.csv           # Historical NAV values for AMFI codes
│   │   ├── 03_aum_by_fund_house.csv     # Assets Under Management (AUM) by AMC
│   │   ├── 04_monthly_sip_inflows.csv   # Historical SIP inflow trends
│   │   ├── 05_category_inflows.csv      # Category-wise mutual fund inflows
│   │   ├── 06_industry_folio_count.csv  # Monthly folio counts of the industry
│   │   ├── 07_scheme_performance.csv    # Scheme performance metrics (Alpha, Beta, Sharpe, etc.)
│   │   ├── 08_investor_transactions.csv # Mock/historical investor transaction records
│   │   ├── 09_portfolio_holdings.csv    # Scheme-wise stock holdings
│   │   ├── 10_benchmark_indices.csv     # Benchmark index closing prices
│   │   ├── *_nav.csv                    # Fetch-specific historical NAV data files
│   │   └── live_nav_fetched_all.csv     # Combined fetched NAV dataset
│   └── processed/                       # Directory reserved for processed output
├── reports/
│   └── data_quality_report.md           # Auto-generated profiling report
├── data_ingestion.py                    # ETL pipeline for loading, profiling, & reports
├── live_nav_fetch.py                    # Multithreaded API ingestion engine
├── requirements.txt                     # Project dependencies
└── README.md                            # Project documentation
```

---

## 📊 Ingested Datasets Summary

| Dataset File Name | Shape (Rows, Cols) | Primary Key / Key Columns | Description |
| :--- | :---: | :--- | :--- |
| **01_fund_master.csv** | (40, 15) | `amfi_code` | Meta-data for 40 schemes, exit loads, expense ratios, managers. |
| **02_nav_history.csv** | (46000, 3) | `amfi_code`, `date` | Historical NAV values spanning multiple years. |
| **03_aum_by_fund_house.csv** | (90, 5) | `fund_house`, `date` | AMC-level Asset Under Management details. |
| **04_monthly_sip_inflows.csv** | (48, 6) | `month` | Monthly aggregate SIP inflows, accounts active, new creations. |
| **05_category_inflows.csv** | (144, 3) | `month`, `category` | Inflows divided by broad asset classes (Equity, Debt, etc.) |
| **06_industry_folio_count.csv** | (21, 6) | `month` | Category-wise retail customer account (folio) statistics. |
| **07_scheme_performance.csv** | (40, 19) | `amfi_code` | Risk/Return metrics (Sharpe, Sortino, Std Dev, Max Drawdown). |
| **08_investor_transactions.csv** | (32778, 13) | `investor_id` | Mock transaction history showing age, gender, state, mode. |
| **09_portfolio_holdings.csv** | (322, 8) | `amfi_code`, `stock_symbol` | Individual stock holdings and weights for the mutual funds. |
| **10_benchmark_indices.csv** | (8050, 3) | `date`, `index_name` | Underlying index values (e.g., Nifty 50) for benchmark checks. |

---

## ⚙️ Core Technical Optimizations

### 1. Memory Downcasting (dtype Mapping)
Pandas by default parses integer columns as `int64` and floating columns as `float64`, consuming unnecessary RAM. Our ingestion script loads data with custom mappings to use minimal, precise bit sizes:
```python
DTYPES_MAPPING = {
    "amfi_code": "int32",
    "expense_ratio_pct": "float32",
    "min_sip_amount": "int32",
    "min_lumpsum_amount": "int32",
    "num_schemes": "int16",
    "morningstar_rating": "int8"
}
```
This downcasting drastically optimizes memory performance, critical for scaling to millions of rows (like in `08_investor_transactions.csv`).

### 2. High-Speed API Ingestion with ThreadPoolExecutor
Rather than downloading historical data for schemes sequentially (which is slow and bound by Network I/O latency), `live_nav_fetch.py` executes concurrent HTTP requests:
* **Session Pooling**: Keeps sockets alive using `requests.Session()` to bypass TCP handshake overhead.
* **Concurrent Futures**: Spawns worker threads matching the workload size via `ThreadPoolExecutor(max_workers=len(schemes))` to parallelize downloads.
* **Progressive Retries**: Employs an exponential timeout strategy to survive occasional API rate-limiting and high-latency spikes.

---

## ⚠️ Upstream API Mapping Discrepancies

During API validation, we observed mismatched mappings between requested scheme codes and metadata returned by `mfapi.in`:

* **Code 125497**: Assigned as *HDFC Top 100 Direct* ➔ API returns **SBI Small Cap Fund - Direct Plan - Growth**
* **Code 119551**: Assigned as *SBI Bluechip* ➔ API returns **Aditya Birla Sun Life Banking & PSU Debt Fund - DIRECT - IDCW**
* **Code 120503**: Assigned as *ICICI Bluechip* ➔ API returns **Axis ELSS Tax Saver Fund - Direct Plan - Growth Option**
* **Code 119092**: Assigned as *Axis Bluechip* ➔ API returns **HDFC Money Market Fund - Growth Option - Direct Plan**
* **Code 120841**: Assigned as *Kotak Bluechip* ➔ API returns **quant Mid Cap Fund - Growth Option - Direct Plan**

*Note: The API responses have been successfully downloaded and preserved under their official code names in `data/raw/` to ensure data authenticity.*

---

## 🛠️ How to Set Up and Run

### Prerequisites
* Python 3.8 or above
* pip (Python package installer)

### Installation
1. Clone the repository (if not already done):
   ```bash
   git clone https://github.com/Piyush-ouch/DAY---1-data-analyst-internship-.git
   cd DAY---1-data-analyst-internship-
   ```
2. Set up a virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Scripts

1. **Execute Dataset Load, Validation & Profiling**:
   ```bash
   python data_ingestion.py
   ```
   *This reads raw datasets from `data/raw/`, validates the integrity of AMFI codes, profiles missing data, and outputs an updated quality report in `reports/data_quality_report.md`.*

2. **Run Live/Historical NAV API Fetcher**:
   ```bash
   python live_nav_fetch.py
   ```
   *This concurrently fetches historical NAV files from `mfapi.in` for the selected schemes, writes individual raw files inside `data/raw/`, and outputs a consolidated dataset: `data/raw/live_nav_fetched_all.csv`.*

---

## 📝 Contact / Contribution
Feel free to open issues or pull requests. Maintained as part of the **Bluestock Data Analyst Internship**.
* **Intern**: Piyush
* **Email**: piyushjangade06@gmail.com
