# clean_and_load.py
# Python pipeline to clean mutual fund datasets and load them into a SQLite database.

import os
import sqlite3
import logging
from pathlib import Path
import pandas as pd
import numpy as np
from sqlalchemy import create_engine

# Configure professional logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Directory definitions
RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
DB_PATH = Path("bluestock_mf.db")
SCHEMA_PATH = Path("schema.sql")

def init_directories():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directories exist: {PROCESSED_DIR}")

def execute_sql_schema():
    """Reads schema.sql and initializes the SQLite database tables."""
    logger.info(f"Initializing database at {DB_PATH} using {SCHEMA_PATH}...")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        with open(SCHEMA_PATH, "r") as f:
            sql_script = f.read()
            
        cursor.executescript(sql_script)
        conn.commit()
        conn.close()
        logger.info("Database schema initialized successfully.")
    except Exception as e:
        logger.error(f"Error executing schema script: {e}")
        raise

def generate_calendar_dim(start_date: str = "2022-01-01", end_date: str = "2026-12-31") -> pd.DataFrame:
    """Generates a complete date dimension DataFrame."""
    logger.info(f"Generating calendar dimension from {start_date} to {end_date}...")
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    
    df_date = pd.DataFrame({"date": date_range})
    df_date['year'] = df_date['date'].dt.year
    df_date['month'] = df_date['date'].dt.month
    df_date['quarter'] = df_date['date'].dt.quarter
    df_date['day'] = df_date['date'].dt.day
    df_date['day_of_week'] = df_date['date'].dt.dayofweek # 0 is Monday
    df_date['day_name'] = df_date['date'].dt.day_name()
    df_date['month_name'] = df_date['date'].dt.month_name()
    df_date['is_weekend'] = df_date['day_of_week'].apply(lambda x: 1 if x >= 5 else 0)
    
    # Format date as YYYY-MM-DD
    df_date['date'] = df_date['date'].dt.strftime('%Y-%m-%d')
    return df_date

def clean_nav_history() -> pd.DataFrame:
    """Cleans nav_history.csv: sorts, removes duplicates, validates NAV > 0, and ffills holidays/weekends."""
    logger.info("Cleaning NAV History...")
    file_path = RAW_DIR / "02_nav_history.csv"
    df = pd.read_csv(file_path)
    
    # Parse dates
    df['date'] = pd.to_datetime(df['date'])
    
    # Deduplicate & validate NAV
    df = df.drop_duplicates()
    initial_rows = len(df)
    df = df[df['nav'] > 0]
    dropped_zeros = initial_rows - len(df)
    if dropped_zeros > 0:
        logger.warning(f"Dropped {dropped_zeros} rows from NAV history due to nav <= 0.")
        
    # Forward-fill weekends & holidays per scheme
    filled_groups = []
    for code, group in df.groupby('amfi_code'):
        group = group.sort_values('date')
        min_date = group['date'].min()
        max_date = group['date'].max()
        
        # Complete daily index
        idx = pd.date_range(start=min_date, end=max_date, freq='D')
        group_filled = group.set_index('date').reindex(idx)
        
        # Fill missing values
        group_filled['amfi_code'] = code
        group_filled['nav'] = group_filled['nav'].ffill()
        
        group_filled = group_filled.reset_index().rename(columns={'index': 'date'})
        filled_groups.append(group_filled)
        
    df_clean = pd.concat(filled_groups, ignore_index=True)
    
    # Handle any nulls that might occur at the beginning of the series
    null_navs = df_clean['nav'].isnull().sum()
    if null_navs > 0:
        logger.warning(f"Found {null_navs} null NAV values after forward-filling. Attempting backward-fill...")
        df_clean['nav'] = df_clean.groupby('amfi_code')['nav'].bfill()
        
    # Sort by amfi_code + date
    df_clean = df_clean.sort_values(['amfi_code', 'date']).reset_index(drop=True)
    df_clean['date'] = df_clean['date'].dt.strftime('%Y-%m-%d')
    
    logger.info(f"NAV History cleaned: rows went from {len(df)} to {len(df_clean)} due to forward-filling.")
    return df_clean

def clean_investor_transactions() -> pd.DataFrame:
    """Cleans investor_transactions.csv: standardizes type, checks KYC, formats dates, validates amount > 0."""
    logger.info("Cleaning Investor Transactions...")
    file_path = RAW_DIR / "08_investor_transactions.csv"
    df = pd.read_csv(file_path)
    
    # Standardize transaction type
    type_map = {
        'sip': 'SIP',
        'lumpsum': 'Lumpsum',
        'redemption': 'Redemption'
    }
    df['transaction_type'] = df['transaction_type'].str.strip().str.lower().map(type_map)
    # Check for unmapped types
    unmapped = df['transaction_type'].isnull().sum()
    if unmapped > 0:
        logger.error(f"Found {unmapped} unmapped transaction types in transactions dataset!")
        
    # Validate amount > 0
    invalid_amounts = (df['amount_inr'] <= 0).sum()
    if invalid_amounts > 0:
        logger.warning(f"Found {invalid_amounts} transaction rows with amount <= 0. Removing them...")
        df = df[df['amount_inr'] > 0]
        
    # Standardize dates
    df['transaction_date'] = pd.to_datetime(df['transaction_date']).dt.strftime('%Y-%m-%d')
    
    # Standardize KYC
    kyc_map = {
        'verified': 'Verified',
        'pending': 'Pending'
    }
    df['kyc_status'] = df['kyc_status'].str.strip().str.lower().map(kyc_map)
    
    # Check for invalid/missing KYC
    missing_kyc = df['kyc_status'].isnull().sum()
    if missing_kyc > 0:
        logger.warning(f"Found {missing_kyc} transaction rows with invalid/missing KYC. Defaulting to 'Pending'.")
        df['kyc_status'] = df['kyc_status'].fillna('Pending')
        
    return df

def clean_scheme_performance() -> pd.DataFrame:
    """Cleans scheme_performance.csv: validates numeric values, flags anomalies in expense ratio."""
    logger.info("Cleaning Scheme Performance...")
    file_path = RAW_DIR / "07_scheme_performance.csv"
    df = pd.read_csv(file_path)
    
    # Validate numeric returns
    return_cols = ['return_1yr_pct', 'return_3yr_pct', 'return_5yr_pct', 'benchmark_3yr_pct']
    for col in return_cols:
        non_numeric = pd.to_numeric(df[col], errors='coerce').isnull().sum()
        if non_numeric > 0:
            logger.warning(f"Column {col} has {non_numeric} non-numeric/null values.")
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
        
    # Validate expense ratio range: 0.1% to 2.5%
    out_of_bounds = df[(df['expense_ratio_pct'] < 0.1) | (df['expense_ratio_pct'] > 2.5)]
    if not out_of_bounds.empty:
        logger.warning(f"Found {len(out_of_bounds)} schemes with expense ratios outside 0.1%-2.5% range: {out_of_bounds[['amfi_code', 'scheme_name', 'expense_ratio_pct']].to_dict(orient='records')}")
        
    return df

def clean_monthly_dataset(file_name: str) -> pd.DataFrame:
    """Standardizes month column in monthly datasets to YYYY-MM-DD (start of month)."""
    logger.info(f"Cleaning monthly dataset: {file_name}")
    df = pd.read_csv(RAW_DIR / file_name)
    
    # Map month column (like '2022-01') to first day of the month ('2022-01-01')
    if 'month' in df.columns:
        df['month'] = pd.to_datetime(df['month'], format='%Y-%m').dt.strftime('%Y-%m-01')
    return df

def clean_fund_master() -> pd.DataFrame:
    """Standardizes fund_master.csv."""
    logger.info("Cleaning Fund Master...")
    df = pd.read_csv(RAW_DIR / "01_fund_master.csv")
    df['launch_date'] = pd.to_datetime(df['launch_date']).dt.strftime('%Y-%m-%d')
    return df

def clean_aum() -> pd.DataFrame:
    """Standardizes aum_by_fund_house.csv."""
    logger.info("Cleaning AUM by Fund House...")
    df = pd.read_csv(RAW_DIR / "03_aum_by_fund_house.csv")
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
    return df

def clean_portfolio_holdings() -> pd.DataFrame:
    """Standardizes portfolio_holdings.csv."""
    logger.info("Cleaning Portfolio Holdings...")
    df = pd.read_csv(RAW_DIR / "09_portfolio_holdings.csv")
    df['portfolio_date'] = pd.to_datetime(df['portfolio_date']).dt.strftime('%Y-%m-%d')
    return df

def clean_benchmark_indices() -> pd.DataFrame:
    """Standardizes benchmark_indices.csv."""
    logger.info("Cleaning Benchmark Indices...")
    df = pd.read_csv(RAW_DIR / "10_benchmark_indices.csv")
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
    return df

def main():
    init_directories()
    execute_sql_schema()
    
    engine = create_engine(f"sqlite:///{DB_PATH}")
    
    # 1. Generate & Load Date Dimension
    df_date = generate_calendar_dim()
    df_date.to_csv(PROCESSED_DIR / "dim_date.csv", index=False)
    df_date.to_sql("dim_date", con=engine, if_exists="append", index=False)
    logger.info(f"Loaded dim_date: {len(df_date)} rows.")
    
    # 2. Fund Master
    df_fund = clean_fund_master()
    df_fund.to_csv(PROCESSED_DIR / "01_fund_master.csv", index=False)
    df_fund.to_sql("dim_fund", con=engine, if_exists="append", index=False)
    logger.info(f"Loaded dim_fund: {len(df_fund)} rows.")
    
    # 3. NAV History (fact_nav)
    df_nav = clean_nav_history()
    df_nav.to_csv(PROCESSED_DIR / "02_nav_history.csv", index=False)
    df_nav.to_sql("fact_nav", con=engine, if_exists="append", index=False)
    logger.info(f"Loaded fact_nav: {len(df_nav)} rows.")
    
    # 4. AUM (fact_aum)
    df_aum = clean_aum()
    df_aum.to_csv(PROCESSED_DIR / "03_aum_by_fund_house.csv", index=False)
    df_aum.to_sql("fact_aum", con=engine, if_exists="append", index=False)
    logger.info(f"Loaded fact_aum: {len(df_aum)} rows.")
    
    # 5. Monthly SIP Inflows
    df_sip = clean_monthly_dataset("04_monthly_sip_inflows.csv")
    df_sip.to_csv(PROCESSED_DIR / "04_monthly_sip_inflows.csv", index=False)
    df_sip.to_sql("monthly_sip_inflows", con=engine, if_exists="append", index=False)
    logger.info(f"Loaded monthly_sip_inflows: {len(df_sip)} rows.")
    
    # 6. Category Inflows
    df_cat_inflow = clean_monthly_dataset("05_category_inflows.csv")
    df_cat_inflow.to_csv(PROCESSED_DIR / "05_category_inflows.csv", index=False)
    df_cat_inflow.to_sql("category_inflows", con=engine, if_exists="append", index=False)
    logger.info(f"Loaded category_inflows: {len(df_cat_inflow)} rows.")
    
    # 7. Industry Folios
    df_folios = clean_monthly_dataset("06_industry_folio_count.csv")
    df_folios.to_csv(PROCESSED_DIR / "06_industry_folio_count.csv", index=False)
    df_folios.to_sql("industry_folio_count", con=engine, if_exists="append", index=False)
    logger.info(f"Loaded industry_folio_count: {len(df_folios)} rows.")
    
    # 8. Scheme Performance (fact_performance)
    df_perf = clean_scheme_performance()
    df_perf.to_csv(PROCESSED_DIR / "07_scheme_performance.csv", index=False)
    # Drop columns not in the schema (since they are in dim_fund)
    db_perf_cols = [
        'amfi_code', 'return_1yr_pct', 'return_3yr_pct', 'return_5yr_pct', 'benchmark_3yr_pct',
        'alpha', 'beta', 'sharpe_ratio', 'sortino_ratio', 'std_dev_ann_pct', 'max_drawdown_pct',
        'aum_crore', 'expense_ratio_pct', 'morningstar_rating', 'risk_grade'
    ]
    df_perf_db = df_perf[db_perf_cols]
    df_perf_db.to_sql("fact_performance", con=engine, if_exists="append", index=False)
    logger.info(f"Loaded fact_performance: {len(df_perf_db)} rows.")
    
    # 9. Investor Transactions (fact_transactions)
    df_tx = clean_investor_transactions()
    df_tx.to_csv(PROCESSED_DIR / "08_investor_transactions.csv", index=False)
    df_tx.to_sql("fact_transactions", con=engine, if_exists="append", index=False)
    logger.info(f"Loaded fact_transactions: {len(df_tx)} rows.")
    
    # 10. Portfolio Holdings
    df_holdings = clean_portfolio_holdings()
    df_holdings.to_csv(PROCESSED_DIR / "09_portfolio_holdings.csv", index=False)
    df_holdings.to_sql("portfolio_holdings", con=engine, if_exists="append", index=False)
    logger.info(f"Loaded portfolio_holdings: {len(df_holdings)} rows.")
    
    # 11. Benchmark Indices
    df_indices = clean_benchmark_indices()
    df_indices.to_csv(PROCESSED_DIR / "10_benchmark_indices.csv", index=False)
    df_indices.to_sql("benchmark_indices", con=engine, if_exists="append", index=False)
    logger.info(f"Loaded benchmark_indices: {len(df_indices)} rows.")
    
    # ROW COUNT VERIFICATION REPORT
    print("\n" + "="*50)
    print("           VERIFICATION SUMMARY REPORT")
    print("="*50)
    print(f"{'Table / Dataset Name':<30} | {'Source CSV Rows':<15} | {'DB Rows':<10}")
    print("-"*62)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    mappings = [
        ("01_fund_master.csv", "dim_fund"),
        ("02_nav_history.csv", "fact_nav"),
        ("03_aum_by_fund_house.csv", "fact_aum"),
        ("04_monthly_sip_inflows.csv", "monthly_sip_inflows"),
        ("05_category_inflows.csv", "category_inflows"),
        ("06_industry_folio_count.csv", "industry_folio_count"),
        ("07_scheme_performance.csv", "fact_performance"),
        ("08_investor_transactions.csv", "fact_transactions"),
        ("09_portfolio_holdings.csv", "portfolio_holdings"),
        ("10_benchmark_indices.csv", "benchmark_indices")
    ]
    
    for csv_file, table_name in mappings:
        csv_len = len(pd.read_csv(PROCESSED_DIR / csv_file))
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        db_len = cursor.fetchone()[0]
        match_str = "MATCH" if csv_len == db_len else "MISMATCH (Expected for ffill / checks)"
        print(f"{table_name:<30} | {csv_len:<15} | {db_len:<10} | {match_str}")
        
    conn.close()
    print("="*50)
    logger.info("ETL run and database insertion complete.")

if __name__ == "__main__":
    main()
