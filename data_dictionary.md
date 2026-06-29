# Data Dictionary - Bluestock Mutual Fund Database

This data dictionary documents the tables, column names, data types, constraints, and business definitions of the SQLite database (`bluestock_mf.db`) and the cleaned datasets under `data/processed/`.

---

## 🏛️ Dimension Tables

### 1. `dim_fund`
Master registry of all mutual fund schemes.
* **Source Reference**: `01_fund_master.csv`

| Column Name | SQLite Data Type | Key/Constraint | Business Definition / Description |
| :--- | :--- | :--- | :--- |
| `amfi_code` | INTEGER | PRIMARY KEY | Unique identifier for a mutual fund scheme assigned by AMFI (Association of Mutual Funds in India). |
| `fund_house` | TEXT | NOT NULL | Asset Management Company (AMC) name. |
| `scheme_name` | TEXT | NOT NULL | Official name of the mutual fund scheme. |
| `category` | TEXT | Nullable | Asset class category (e.g., Equity, Debt, Hybrid). |
| `sub_category` | TEXT | Nullable | Granular categorization of the fund (e.g., Large Cap, Small Cap, Liquid). |
| `plan` | TEXT | Nullable | Type of plan (e.g., Growth, IDCW, Direct, Regular). |
| `launch_date` | TEXT | Nullable (YYYY-MM-DD) | Date the mutual fund scheme was first launched. |
| `benchmark` | TEXT | Nullable | Underlying benchmark index name (e.g., Nifty 50, S&P BSE 200). |
| `expense_ratio_pct` | REAL | Nullable | Percentage of total assets dedicated to managing the fund. |
| `exit_load_pct` | REAL | Nullable | Exit fee percentage charged to investors on redemption before a specified time. |
| `min_sip_amount` | INTEGER | Nullable | Minimum amount required for a Systemic Investment Plan installment. |
| `min_lumpsum_amount` | INTEGER | Nullable | Minimum amount required for a single lumpsum purchase. |
| `fund_manager` | TEXT | Nullable | Name of the primary fund manager(s). |
| `risk_category` | TEXT | Nullable | Risk tier of the fund (e.g., Low, Moderate, High, Very High). |
| `sebi_category_code` | TEXT | Nullable | Unique category code as classified by SEBI guidelines. |

---

### 2. `dim_date`
Calendar and date dimension table used for analytical date grouping and joins.
* **Source Reference**: Dynamically generated calendar.

| Column Name | SQLite Data Type | Key/Constraint | Business Definition / Description |
| :--- | :--- | :--- | :--- |
| `date` | TEXT | PRIMARY KEY (YYYY-MM-DD) | The calendar date. |
| `year` | INTEGER | NOT NULL | Year component of the date (e.g., 2024). |
| `month` | INTEGER | NOT NULL | Month number component (1–12). |
| `quarter` | INTEGER | NOT NULL | Financial/calendar quarter (1–4). |
| `day` | INTEGER | NOT NULL | Day of the month (1–31). |
| `day_of_week` | INTEGER | NOT NULL | Zero-indexed day indicator (0 = Monday, 6 = Sunday). |
| `day_name` | TEXT | NOT NULL | Text name of the day (e.g., Monday, Tuesday). |
| `month_name` | TEXT | NOT NULL | Text name of the month (e.g., January, February). |
| `is_weekend` | INTEGER | NOT NULL (0 or 1) | Binary flag where 1 represents a weekend (Saturday/Sunday) and 0 represents a weekday. |

---

## 📈 Fact Tables

### 3. `fact_nav`
Daily Net Asset Value (NAV) values for mutual fund schemes.
* **Source Reference**: `02_nav_history.csv` (Holidays/weekends forward-filled).

| Column Name | SQLite Data Type | Key/Constraint | Business Definition / Description |
| :--- | :--- | :--- | :--- |
| `amfi_code` | INTEGER | PK, FK (`dim_fund.amfi_code`) | Scheme code associated with the NAV record. |
| `date` | TEXT | PK, FK (`dim_date.date`) | Date of the NAV record (YYYY-MM-DD). |
| `nav` | REAL | NOT NULL | Net Asset Value (price per unit) on that date. |

---

### 4. `fact_transactions`
Individual transaction histories for mock investors.
* **Source Reference**: `08_investor_transactions.csv`

| Column Name | SQLite Data Type | Key/Constraint | Business Definition / Description |
| :--- | :--- | :--- | :--- |
| `transaction_id` | INTEGER | PRIMARY KEY (AUTOINCREMENT) | Auto-generated unique identifier for each transaction. |
| `investor_id` | TEXT | NOT NULL | Unique identifier of the investor. |
| `transaction_date` | TEXT | FK (`dim_date.date`) | Date of the transaction (YYYY-MM-DD). |
| `amfi_code` | INTEGER | FK (`dim_fund.amfi_code`) | Scheme code traded in the transaction. |
| `transaction_type` | TEXT | NOT NULL (Check Constraint) | Class of transaction: `SIP`, `Lumpsum`, or `Redemption`. |
| `amount_inr` | REAL | NOT NULL | Transaction amount in Indian Rupees (INR). |
| `state` | TEXT | Nullable | Indian State of the investor's residence. |
| `city` | TEXT | Nullable | City of the investor. |
| `city_tier` | INTEGER | Nullable | Tier categorization of the city (1, 2, or 3). |
| `age_group` | TEXT | Nullable | Age bracket of the investor (e.g., 18-25, 26-35). |
| `gender` | TEXT | Nullable | Gender of the investor (`Male`, `Female`). |
| `annual_income_lakh` | REAL | Nullable | Annual income of the investor in Lakhs INR. |
| `payment_mode` | TEXT | Nullable | Payment method used (e.g., UPI, Cheque, Net Banking). |
| `kyc_status` | TEXT | Check Constraint | KYC verification status: `Verified` or `Pending`. |

---

### 5. `fact_performance`
Calculated performance ratios and historical returns of schemes.
* **Source Reference**: `07_scheme_performance.csv`

| Column Name | SQLite Data Type | Key/Constraint | Business Definition / Description |
| :--- | :--- | :--- | :--- |
| `amfi_code` | INTEGER | PRIMARY KEY, FK (`dim_fund.amfi_code`) | Scheme code associated with the performance record. |
| `return_1yr_pct` | REAL | Nullable | Compound Annual Return of the scheme over 1 year. |
| `return_3yr_pct` | REAL | Nullable | Compound Annual Return of the scheme over 3 years. |
| `return_5yr_pct` | REAL | Nullable | Compound Annual Return of the scheme over 5 years. |
| `benchmark_3yr_pct` | REAL | Nullable | Compound Annual Return of the scheme's benchmark over 3 years. |
| `alpha` | REAL | Nullable | Measure of active return relative to the benchmark index (positive indicates outperformance). |
| `beta` | REAL | Nullable | Measure of systematic risk/volatility relative to the benchmark market index. |
| `sharpe_ratio` | REAL | Nullable | Risk-adjusted return metric (higher is better). |
| `sortino_ratio` | REAL | Nullable | Downside risk-adjusted return metric. |
| `std_dev_ann_pct` | REAL | Nullable | Annualized standard deviation (measure of historical volatility). |
| `max_drawdown_pct` | REAL | Nullable | Maximum observed peak-to-trough drop percentage. |
| `aum_crore` | REAL | Nullable | Scheme Assets Under Management in Crores INR. |
| `expense_ratio_pct` | REAL | Nullable | Expense ratio of the specific plan. |
| `morningstar_rating` | INTEGER | Nullable | Rating score assigned by Morningstar (1–5 stars). |
| `risk_grade` | TEXT | Nullable | Risk category description matching AMC specifications. |

---

### 6. `fact_aum`
Assets Under Management (AUM) values tracked by Fund House and Date.
* **Source Reference**: `03_aum_by_fund_house.csv`

| Column Name | SQLite Data Type | Key/Constraint | Business Definition / Description |
| :--- | :--- | :--- | :--- |
| `aum_id` | INTEGER | PRIMARY KEY (AUTOINCREMENT) | Auto-generated unique identifier for AUM snapshot. |
| `date` | TEXT | FK (`dim_date.date`) | Ending date of the AUM tracking period (YYYY-MM-DD). |
| `fund_house` | TEXT | NOT NULL | Name of the Asset Management Company (AMC). |
| `aum_lakh_crore` | REAL | Nullable | AUM value in Lakh Crores INR. |
| `aum_crore` | REAL | Nullable | AUM value in Crores INR. |
| `num_schemes` | INTEGER | Nullable | Number of active schemes run by the AMC. |

---

## 📈 Supporting Tables

### 7. `monthly_sip_inflows`
Monthly SIP inflow data and growth rates across the mutual fund industry.
* **Source Reference**: `04_monthly_sip_inflows.csv`

| Column Name | SQLite Data Type | Key/Constraint | Business Definition / Description |
| :--- | :--- | :--- | :--- |
| `month` | TEXT | PRIMARY KEY (YYYY-MM-DD) | Start date of the recorded month. |
| `sip_inflow_crore` | REAL | Nullable | SIP inflow amount in Crores INR. |
| `active_sip_accounts_crore` | REAL | Nullable | Number of active SIP accounts in Crores. |
| `new_sip_accounts_lakh` | REAL | Nullable | Number of new SIP accounts registered in Lakhs. |
| `sip_aum_lakh_crore` | REAL | Nullable | Total SIP AUM value in Lakh Crores INR. |
| `yoy_growth_pct` | REAL | Nullable | Year-over-Year percentage growth of SIP inflow. |

---

### 8. `category_inflows`
Industry-wide mutual fund category net inflows.
* **Source Reference**: `05_category_inflows.csv`

| Column Name | SQLite Data Type | Key/Constraint | Business Definition / Description |
| :--- | :--- | :--- | :--- |
| `category_inflow_id` | INTEGER | PRIMARY KEY (AUTOINCREMENT) | Unique identifier for category inflow record. |
| `month` | TEXT | NOT NULL (YYYY-MM-DD) | Start date of the recorded month. |
| `category` | TEXT | NOT NULL | Asset class category (e.g., Equity, Debt). |
| `net_inflow_crore` | REAL | Nullable | Net inflow (inflows minus outflows) in Crores INR. |

---

### 9. `industry_folio_count`
Broad folio account counts across industry asset types.
* **Source Reference**: `06_industry_folio_count.csv`

| Column Name | SQLite Data Type | Key/Constraint | Business Definition / Description |
| :--- | :--- | :--- | :--- |
| `month` | TEXT | PRIMARY KEY (YYYY-MM-DD) | Start date of the recorded month. |
| `total_folios_crore` | REAL | Nullable | Total folio count in Crores. |
| `equity_folios_crore` | REAL | Nullable | Equity folio count in Crores. |
| `debt_folios_crore` | REAL | Nullable | Debt folio count in Crores. |
| `hybrid_folios_crore` | REAL | Nullable | Hybrid folio count in Crores. |
| `others_folios_crore` | REAL | Nullable | Other asset class folio count in Crores. |

---

### 10. `portfolio_holdings`
Stock allocation weightings and values inside the mutual fund portfolios.
* **Source Reference**: `09_portfolio_holdings.csv`

| Column Name | SQLite Data Type | Key/Constraint | Business Definition / Description |
| :--- | :--- | :--- | :--- |
| `holding_id` | INTEGER | PRIMARY KEY (AUTOINCREMENT) | Unique identifier of the portfolio holding entry. |
| `amfi_code` | INTEGER | FK (`dim_fund.amfi_code`) | Scheme code holding the stock. |
| `stock_symbol` | TEXT | NOT NULL | Stock exchange ticker symbol (e.g., HDFCBANK, POWERGRID). |
| `stock_name` | TEXT | Nullable | Official company name of the stock. |
| `sector` | TEXT | Nullable | Industry sector classification (e.g., Banking, IT). |
| `weight_pct` | REAL | Nullable | Percentage allocation weight of the stock in the fund. |
| `market_value_cr` | REAL | Nullable | Value of the holdings in Crores INR. |
| `current_price_inr` | REAL | Nullable | Trading price of the individual stock share in INR. |
| `portfolio_date` | TEXT | FK (`dim_date.date`) | Date of the portfolio snapshot. |

---

### 11. `benchmark_indices`
Daily values of major Indian benchmark indices.
* **Source Reference**: `10_benchmark_indices.csv`

| Column Name | SQLite Data Type | Key/Constraint | Business Definition / Description |
| :--- | :--- | :--- | :--- |
| `benchmark_index_id` | INTEGER | PRIMARY KEY (AUTOINCREMENT) | Unique identifier for index value record. |
| `date` | TEXT | FK (`dim_date.date`) | Date of the closing price (YYYY-MM-DD). |
| `index_name` | TEXT | NOT NULL | Benchmark index name (e.g., NIFTY50, SENSEX). |
| `close_value` | REAL | Nullable | Market closing price of the index on that date. |
