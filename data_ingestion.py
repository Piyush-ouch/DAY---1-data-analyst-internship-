import os
import pandas as pd
import numpy as np

def load_and_inspect_datasets():
    data_dir = "data/raw"
    csv_files = [
        "01_fund_master.csv",
        "02_nav_history.csv",
        "03_aum_by_fund_house.csv",
        "04_monthly_sip_inflows.csv",
        "05_category_inflows.csv",
        "06_industry_folio_count.csv",
        "07_scheme_performance.csv",
        "08_investor_transactions.csv",
        "09_portfolio_holdings.csv",
        "10_benchmark_indices.csv"
    ]
    
    loaded_data = {}
    print("="*60)
    print("LOADING AND INSPECTING DATASETS")
    print("="*60)
    
    anomalies_log = []
    
    for file_name in csv_files:
        file_path = os.path.join(data_dir, file_name)
        if not os.path.exists(file_path):
            print(f"Warning: {file_name} does not exist in {data_dir}!")
            continue
            
        try:
            df = pd.read_csv(file_path)
            loaded_data[file_name] = df
            
            print(f"\n--- Dataset: {file_name} ---")
            print(f"Shape: {df.shape}")
            print("\nDtypes:")
            print(df.dtypes)
            print("\nFirst 3 rows:")
            print(df.head(3))
            print("-" * 40)
            
            # Check for anomalies
            missing_count = df.isnull().sum().sum()
            missing_cols = df.isnull().sum()
            missing_cols = missing_cols[missing_cols > 0]
            
            dup_count = df.duplicated().sum()
            
            # Record basic anomalies
            file_anomalies = []
            if missing_count > 0:
                file_anomalies.append(f"Missing values: {missing_count} total. Columns: {dict(missing_cols)}")
            if dup_count > 0:
                file_anomalies.append(f"Duplicate rows: {dup_count}")
                
            # Range checks or type checks based on specific files
            if file_name == "01_fund_master.csv":
                if "scheme_code" in df.columns:
                    non_numeric_codes = pd.to_numeric(df['scheme_code'], errors='coerce').isnull().sum()
                    if non_numeric_codes > 0:
                        file_anomalies.append(f"Non-numeric scheme codes found: {non_numeric_codes}")
            
            if file_anomalies:
                anomalies_log.append(f"**{file_name}**:\n" + "\n".join([f"- {a}" for a in file_anomalies]))
            else:
                anomalies_log.append(f"**{file_name}**: No obvious basic anomalies found.")
                
        except Exception as e:
            print(f"Error loading {file_name}: {e}")
            anomalies_log.append(f"**{file_name}**: Failed to load due to error: {e}")
            
    return loaded_data, anomalies_log

def explore_fund_master(df):
    print("\n" + "="*60)
    print("EXPLORING FUND MASTER")
    print("="*60)
    
    cols = df.columns
    print(f"Columns in Fund Master: {list(cols)}")
    
    fund_house_col = next((c for c in cols if 'fund_house' in c.lower() or 'amc' in c.lower()), None)
    category_col = next((c for c in cols if 'category' in c.lower() and 'sub' not in c.lower()), None)
    sub_category_col = next((c for c in cols if 'sub_category' in c.lower() or 'subcategory' in c.lower()), None)
    risk_col = next((c for c in cols if 'risk' in c.lower()), None)
    code_col = next((c for c in cols if 'code' in c.lower()), None)
    
    exploration_results = {}
    
    if fund_house_col:
        unique_fh = df[fund_house_col].dropna().unique()
        print(f"\nUnique Fund Houses ({len(unique_fh)}):")
        print(unique_fh[:10], "... and more" if len(unique_fh) > 10 else "")
        exploration_results['fund_houses'] = list(unique_fh)
        
    if category_col:
        unique_cat = df[category_col].dropna().unique()
        print(f"\nUnique Categories ({len(unique_cat)}):")
        print(unique_cat)
        exploration_results['categories'] = list(unique_cat)
        
    if sub_category_col:
        unique_subcat = df[sub_category_col].dropna().unique()
        print(f"\nUnique Sub-Categories ({len(unique_subcat)}):")
        print(unique_subcat[:10], "... and more" if len(unique_subcat) > 10 else "")
        exploration_results['sub_categories'] = list(unique_subcat)
        
    if risk_col:
        unique_risk = df[risk_col].dropna().unique()
        print(f"\nUnique Risk Grades ({len(unique_risk)}):")
        print(unique_risk)
        exploration_results['risk_grades'] = list(unique_risk)
        
    if code_col:
        scheme_codes = df[code_col].dropna()
        min_code = scheme_codes.min()
        max_code = scheme_codes.max()
        digits = scheme_codes.astype(str).str.len().unique()
        print(f"\nScheme Code Analysis (AMFI Codes):")
        print(f"Count: {len(scheme_codes)}")
        print(f"Range: {min_code} to {max_code}")
        print(f"Unique digit lengths found: {digits}")
        exploration_results['scheme_code_lengths'] = [int(d) for d in digits]
        
    return exploration_results

def validate_amfi_codes(df_master, df_history):
    print("\n" + "="*60)
    print("VALIDATING AMFI CODES")
    print("="*60)
    
    master_cols = df_master.columns
    history_cols = df_history.columns
    
    master_code_col = next((c for c in master_cols if 'code' in c.lower()), None)
    history_code_col = next((c for c in history_cols if 'code' in c.lower()), None)
    
    if not master_code_col or not history_code_col:
        print("Error: Could not locate scheme code columns in master or history datasets.")
        return {
            "missing_in_history_count": 0,
            "extra_in_history_count": 0,
            "missing_in_history_samples": [],
            "summary_text": "Could not run validation: code columns missing."
        }
        
    master_codes = set(df_master[master_code_col].dropna().unique())
    history_codes = set(df_history[history_code_col].dropna().unique())
    
    print(f"Unique scheme codes in Fund Master: {len(master_codes)}")
    print(f"Unique scheme codes in NAV History: {len(history_codes)}")
    
    missing_in_history = master_codes - history_codes
    extra_in_history = history_codes - master_codes
    
    print(f"Codes in Fund Master but MISSING in NAV History: {len(missing_in_history)}")
    print(f"Codes in NAV History but NOT in Fund Master: {len(extra_in_history)}")
    
    validation_summary = f"""
### AMFI Code Validation Results
- Unique codes in `01_fund_master.csv`: {len(master_codes)}
- Unique codes in `02_nav_history.csv`: {len(history_codes)}
- Codes in master but missing from history: {len(missing_in_history)}
"""
    if len(missing_in_history) > 0:
        validation_summary += f"  - Sample missing codes: {sorted(list(missing_in_history))[:10]}\n"
    
    validation_summary += f"- Codes in history but missing from master (extra): {len(extra_in_history)}\n"
    if len(extra_in_history) > 0:
        validation_summary += f"  - Sample extra codes: {sorted(list(extra_in_history))[:10]}\n"
        
    return {
        "missing_in_history_count": len(missing_in_history),
        "extra_in_history_count": len(extra_in_history),
        "missing_in_history_samples": sorted(list(missing_in_history))[:10],
        "summary_text": validation_summary
    }

def main():
    loaded_data, anomalies = load_and_inspect_datasets()
    
    fund_master_df = loaded_data.get("01_fund_master.csv")
    nav_history_df = loaded_data.get("02_nav_history.csv")
    
    exploration_res = {}
    if fund_master_df is not None:
        exploration_res = explore_fund_master(fund_master_df)
        
    validation_res = None
    if fund_master_df is not None and nav_history_df is not None:
        validation_res = validate_amfi_codes(fund_master_df, nav_history_df)
        
    # Generate data quality report
    report_content = f"""# Data Quality & Ingestion Summary Report

**Date/Time Run**: 2026-06-22 (Local Time: 11:15 AM)
**Generated By**: Antigravity AI Coding Assistant

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
        
    # Document the mismatch between assigned scheme codes and API-returned names
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
        
    os.makedirs("reports", exist_ok=True)
    report_path = "reports/data_quality_report.md"
    with open(report_path, "w") as f:
        f.write(report_content)
        
    print(f"\nData Quality Report written to {report_path}")

if __name__ == "__main__":
    main()
