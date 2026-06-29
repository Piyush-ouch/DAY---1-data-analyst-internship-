-- schema.sql
-- SQLite Database Schema for Bluestock Mutual Fund ETL Project

-- Enable foreign key support in SQLite
PRAGMA foreign_keys = ON;

-- Drop tables if they exist to allow clean re-runs
DROP TABLE IF EXISTS benchmark_indices;
DROP TABLE IF EXISTS portfolio_holdings;
DROP TABLE IF EXISTS industry_folio_count;
DROP TABLE IF EXISTS category_inflows;
DROP TABLE IF EXISTS monthly_sip_inflows;
DROP TABLE IF EXISTS fact_aum;
DROP TABLE IF EXISTS fact_performance;
DROP TABLE IF EXISTS fact_transactions;
DROP TABLE IF EXISTS fact_nav;
DROP TABLE IF EXISTS dim_date;
DROP TABLE IF EXISTS dim_fund;

-- 1. Dimension Table: Funds
CREATE TABLE dim_fund (
    amfi_code INTEGER PRIMARY KEY,
    fund_house TEXT NOT NULL,
    scheme_name TEXT NOT NULL,
    category TEXT,
    sub_category TEXT,
    plan TEXT,
    launch_date TEXT,
    benchmark TEXT,
    expense_ratio_pct REAL,
    exit_load_pct REAL,
    min_sip_amount INTEGER,
    min_lumpsum_amount INTEGER,
    fund_manager TEXT,
    risk_category TEXT,
    sebi_category_code TEXT
);

-- 2. Dimension Table: Date (Calendar)
CREATE TABLE dim_date (
    date TEXT PRIMARY KEY, -- 'YYYY-MM-DD'
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    day INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,
    day_name TEXT NOT NULL,
    month_name TEXT NOT NULL,
    is_weekend INTEGER NOT NULL CHECK (is_weekend IN (0, 1))
);

-- 3. Fact Table: Daily NAV History
CREATE TABLE fact_nav (
    amfi_code INTEGER,
    date TEXT,
    nav REAL NOT NULL,
    PRIMARY KEY (amfi_code, date),
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code) ON DELETE CASCADE,
    FOREIGN KEY (date) REFERENCES dim_date(date)
);

-- 4. Fact Table: Investor Transactions
CREATE TABLE fact_transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    investor_id TEXT NOT NULL,
    transaction_date TEXT NOT NULL,
    amfi_code INTEGER NOT NULL,
    transaction_type TEXT NOT NULL CHECK (transaction_type IN ('SIP', 'Lumpsum', 'Redemption')),
    amount_inr REAL NOT NULL,
    state TEXT,
    city TEXT,
    city_tier INTEGER,
    age_group TEXT,
    gender TEXT,
    annual_income_lakh REAL,
    payment_mode TEXT,
    kyc_status TEXT CHECK (kyc_status IN ('Verified', 'Pending')),
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code) ON DELETE CASCADE,
    FOREIGN KEY (transaction_date) REFERENCES dim_date(date)
);

-- 5. Fact Table: Scheme Performance
CREATE TABLE fact_performance (
    amfi_code INTEGER PRIMARY KEY,
    return_1yr_pct REAL,
    return_3yr_pct REAL,
    return_5yr_pct REAL,
    benchmark_3yr_pct REAL,
    alpha REAL,
    beta REAL,
    sharpe_ratio REAL,
    sortino_ratio REAL,
    std_dev_ann_pct REAL,
    max_drawdown_pct REAL,
    aum_crore REAL,
    expense_ratio_pct REAL,
    morningstar_rating INTEGER,
    risk_grade TEXT,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code) ON DELETE CASCADE
);

-- 6. Fact Table: AUM by Fund House
CREATE TABLE fact_aum (
    aum_id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    fund_house TEXT NOT NULL,
    aum_lakh_crore REAL,
    aum_crore REAL,
    num_schemes INTEGER,
    FOREIGN KEY (date) REFERENCES dim_date(date)
);

-- 7. Supporting Table: Monthly SIP Inflows
CREATE TABLE monthly_sip_inflows (
    month TEXT PRIMARY KEY, -- 'YYYY-MM-DD' representing start of month
    sip_inflow_crore REAL,
    active_sip_accounts_crore REAL,
    new_sip_accounts_lakh REAL,
    sip_aum_lakh_crore REAL,
    yoy_growth_pct REAL
);

-- 8. Supporting Table: Category Inflows
CREATE TABLE category_inflows (
    category_inflow_id INTEGER PRIMARY KEY AUTOINCREMENT,
    month TEXT NOT NULL, -- 'YYYY-MM-DD'
    category TEXT NOT NULL,
    net_inflow_crore REAL
);

-- 9. Supporting Table: Industry Folio Count
CREATE TABLE industry_folio_count (
    month TEXT PRIMARY KEY, -- 'YYYY-MM-DD'
    total_folios_crore REAL,
    equity_folios_crore REAL,
    debt_folios_crore REAL,
    hybrid_folios_crore REAL,
    others_folios_crore REAL
);

-- 10. Supporting Table: Portfolio Holdings
CREATE TABLE portfolio_holdings (
    holding_id INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code INTEGER NOT NULL,
    stock_symbol TEXT NOT NULL,
    stock_name TEXT,
    sector TEXT,
    weight_pct REAL,
    market_value_cr REAL,
    current_price_inr REAL,
    portfolio_date TEXT NOT NULL,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code) ON DELETE CASCADE,
    FOREIGN KEY (portfolio_date) REFERENCES dim_date(date)
);

-- 11. Supporting Table: Benchmark Indices
CREATE TABLE benchmark_indices (
    benchmark_index_id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL, -- 'YYYY-MM-DD'
    index_name TEXT NOT NULL,
    close_value REAL,
    FOREIGN KEY (date) REFERENCES dim_date(date)
);
