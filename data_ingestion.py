import os
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any
import pandas as pd

# Configure professional logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Optimal data types mapping for memory footprint reduction (downcasts 64-bit to 32/16/8-bit)
DTYPES_MAPPING = {
    "01_fund_master.csv": {
        "amfi_code": "int32",
        "expense_ratio_pct": "float32",
        "exit_load_pct": "float32",
        "min_sip_amount": "int32",
        "min_lumpsum_amount": "int32"
    },
    "02_nav_history.csv": {
        "amfi_code": "int32",
        "nav": "float32"
    },
    "03_aum_by_fund_house.csv": {
        "aum_lakh_crore": "float32",
        "aum_crore": "int32",
        "num_schemes": "int16"
    },
    "04_monthly_sip_inflows.csv": {
        "sip_inflow_crore": "int32",
        "active_sip_accounts_crore": "float32",
        "new_sip_accounts_lakh": "float32",
        "sip_aum_lakh_crore": "float32",
        "yoy_growth_pct": "float32"
    },
    "05_category_inflows.csv": {
        "net_inflow_crore": "float32"
    },
    "06_industry_folio_count.csv": {
        "total_folios_crore": "float32",
        "equity_folios_crore": "float32",
        "debt_folios_crore": "float32",
        "hybrid_folios_crore": "float32",
        "others_folios_crore": "float32"
    },
    "07_scheme_performance.csv": {
        "amfi_code": "int32",
        "return_1yr_pct": "float32",
        "return_3yr_pct": "float32",
        "return_5yr_pct": "float32",
        "benchmark_3yr_pct": "float32",
        "alpha": "float32",
        "beta": "float32",
        "sharpe_ratio": "float32",
        "sortino_ratio": "float32",
        "std_dev_ann_pct": "float32",
        "max_drawdown_pct": "float32",
        "aum_crore": "int32",
        "expense_ratio_pct": "float32",
        "morningstar_rating": "int8"
    },
    "08_investor_transactions.csv": {
        "amfi_code": "int32",
        "amount_inr": "int32",
        "annual_income_lakh": "float32"
    },
    "09_portfolio_holdings.csv": {
        "amfi_code": "int32",
        "weight_pct": "float32",
        "market_value_cr": "float32",
        "current_price_inr": "float32"
    },
    "10_benchmark_indices.csv": {
        "close_value": "float32"
    }
}

def load_and_inspect_datasets(data_dir: Path) -> Tuple[Dict[str, pd.DataFrame], List[str]]:
    csv_files = list(DTYPES_MAPPING.keys())
    loaded_data = {}
    anomalies_log = []
    
    logger.info("Starting batch dataset loading & profiling...")
    
    for file_name in csv_files:
        file_path = data_dir / file_name
        if not file_path.exists():
            logger.warning(f"{file_name} not found in {data_dir}")
            continue
            
        try:
            # Load file with optimized data types to reduce memory footprint
            df = pd.read_csv(file_path, dtype=DTYPES_MAPPING.get(file_name, {}))
            loaded_data[file_name] = df
            
            logger.info(f"Loaded {file_name}: Shape={df.shape}, Memory footprint={df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
            
            # Profile anomalies
            missing_cols = df.isnull().sum()
            missing_cols = missing_cols[missing_cols > 0]
            dup_count = df.duplicated().sum()
            
            file_anomalies = []
            if not missing_cols.empty:
                file_anomalies.append(f"Missing values details: {missing_cols.to_dict()}")
            if dup_count > 0:
                file_anomalies.append(f"Duplicate rows detected: {dup_count}")
                
            if file_name == "01_fund_master.csv" and "scheme_code" in df.columns:
                non_numeric_codes = pd.to_numeric(df['scheme_code'], errors='coerce').isnull().sum()
                if non_numeric_codes > 0:
                    file_anomalies.append(f"Non-numeric AMFI codes: {non_numeric_codes}")
                    
            if file_anomalies:
                anomalies_log.append(f"**{file_name}**:\n" + "\n".join([f"- {a}" for a in file_anomalies]))
            else:
                anomalies_log.append(f"**{file_name}**: No basic anomalies detected.")
                
        except Exception as e:
            logger.error(f"Error reading {file_name}: {e}")
            anomalies_log.append(f"**{file_name}**: Failed to load due to error: {e}")
            
    return loaded_data, anomalies_log

def explore_fund_master(df: pd.DataFrame) -> Dict[str, Any]:
    logger.info("Exploring Fund Master data...")
    cols = df.columns
    
    # Locate column handles using case-insensitive partial searches
    fund_house_col = next((c for c in cols if 'fund_house' in c.lower() or 'amc' in c.lower()), None)
    category_col = next((c for c in cols if 'category' in c.lower() and 'sub' not in c.lower()), None)
    sub_category_col = next((c for c in cols if 'sub_category' in c.lower() or 'subcategory' in c.lower()), None)
    risk_col = next((c for c in cols if 'risk' in c.lower()), None)
    code_col = next((c for c in cols if 'code' in c.lower()), None)
    
    exploration_results = {}
    
    if fund_house_col:
        exploration_results['fund_houses'] = sorted(df[fund_house_col].dropna().unique().tolist())
    if category_col:
        exploration_results['categories'] = sorted(df[category_col].dropna().unique().tolist())
    if sub_category_col:
        exploration_results['sub_categories'] = sorted(df[sub_category_col].dropna().unique().tolist())
    if risk_col:
        exploration_results['risk_grades'] = sorted(df[risk_col].dropna().unique().tolist())
    if code_col:
        scheme_codes = df[code_col].dropna()
        digits = scheme_codes.astype(str).str.len().unique().tolist()
        exploration_results['scheme_code_lengths'] = digits
        exploration_results['code_range'] = (int(scheme_codes.min()), int(scheme_codes.max()))
        
    return exploration_results

def validate_amfi_codes(df_master: pd.DataFrame, df_history: pd.DataFrame) -> Dict[str, Any]:
    logger.info("Validating AMFI Code referential integrity...")
    master_cols = df_master.columns
    history_cols = df_history.columns
    
    master_code_col = next((c for c in master_cols if 'code' in c.lower()), None)
    history_code_col = next((c for c in history_cols if 'code' in c.lower()), None)
    
    if not master_code_col or not history_code_col:
        return {
            "mismatch": True,
            "summary_text": "Failed: Could not locate code columns."
        }
        
    # Set queries (O(N) load, O(1) searches)
    master_codes = set(df_master[master_code_col].dropna().unique())
    history_codes = set(df_history[history_code_col].dropna().unique())
    
    missing_in_history = master_codes - history_codes
    extra_in_history = history_codes - master_codes
    
    summary_text = f"""
### AMFI Code Validation Results
- Unique codes in `01_fund_master.csv`: {len(master_codes)}
- Unique codes in `02_nav_history.csv`: {len(history_codes)}
- Codes in master but missing from history: {len(missing_in_history)}
"""
    if missing_in_history:
        summary_text += f"  - Sample missing codes: {sorted(list(missing_in_history))[:10]}\n"
    summary_text += f"- Codes in history but missing from master (extra): {len(extra_in_history)}\n"
    if extra_in_history:
        summary_text += f"  - Sample extra codes: {sorted(list(extra_in_history))[:10]}\n"
        
    return {
        "missing_in_history_count": len(missing_in_history),
        "extra_in_history_count": len(extra_in_history),
        "summary_text": summary_text
    }

def main():
    data_dir = Path("data/raw")
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    
    loaded_data, anomalies = load_and_inspect_datasets(data_dir)
    
    fund_master_df = loaded_data.get("01_fund_master.csv")
    nav_history_df = loaded_data.get("02_nav_history.csv")
    
    exploration_res = {}
    if fund_master_df is not None:
        exploration_res = explore_fund_master(fund_master_df)
        
    validation_res = None
    if fund_master_df is not None and nav_history_df is not None:
        validation_res = validate_amfi_codes(fund_master_df, nav_history_df)
        
    # Compile markdown quality report
    report_content = f"""# Data Quality & Ingestion Summary Report

**Date/Time Run**: 2026-06-23 (Local Time: 2:10 PM)

## 1. Dataset Shape & Load Summary
"""
    for file_name, df in loaded_data.items():
        report_content += f"- **{file_name}**: Shape={df.shape}, Columns={list(df.columns)}\n"
        
    report_content += "\n## 2. Anomalies Log\n"
    for a in anomalies:
        report_content += a + "\n\n"
        
    if fund_master_df is not None:
        report_content += "\n## 3. Fund Master Exploration\n"
        report_content += f"- **Unique Fund Houses**: {len(exploration_res.get('fund_houses', []))}\n"
        report_content += f"- **Unique Categories**: {len(exploration_res.get('categories', []))}\n"
        report_content += f"- **Unique Sub-Categories**: {len(exploration_res.get('sub_categories', []))}\n"
        report_content += f"- **Unique Risk Grades**: {len(exploration_res.get('risk_grades', []))}\n"
        report_content += f"- **AMFI Scheme Code Digits**: {exploration_res.get('scheme_code_lengths', [])}\n"
        
    if validation_res is not None:
        report_content += "\n## 4. AMFI Code Consistency Check\n"
        report_content += validation_res["summary_text"]
        
    report_content += """
## 5. API Fetch Scheme Name Mismatches
During Day 1 API integration, we noticed discrepancies between the scheme codes requested in the requirements and the actual scheme names returned by the `mfapi.in` API:
- **Code 125497**: Assigned as *HDFC Top 100 Direct* -> API returns **SBI Small Cap Fund - Direct Plan - Growth**
- **Code 119551**: Assigned as *SBI Bluechip* -> API returns **Aditya Birla Sun Life Banking & PSU Debt Fund - DIRECT - IDCW**
- **Code 120503**: Assigned as *ICICI Bluechip* -> API returns **Axis ELSS Tax Saver Fund - Direct Plan - Growth Option**
- **Code 118632**: Assigned as *Nippon Large Cap* -> API returns **Nippon India Large Cap Fund - Direct Plan Growth Plan - Growth Option** (Matches category)
- **Code 119092**: Assigned as *Axis Bluechip* -> API returns **HDFC Money Market Fund - Growth Option - Direct Plan**
- **Code 120841**: Assigned as *Kotak Bluechip* -> API returns **quant Mid Cap Fund - Growth Option - Direct Plan**

These discrepancies represent an upstream mapping mismatch. The API responses have been successfully downloaded and saved under their official code names in `data/raw/`.
"""
        
    report_path = reports_dir / "data_quality_report.md"
    with open(report_path, "w") as f:
        f.write(report_content)
        
    logger.info(f"Data Quality Report successfully written to {report_path}")

if __name__ == "__main__":
    main()
