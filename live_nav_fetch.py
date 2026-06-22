import os
import requests
import pandas as pd
import time

def fetch_scheme_data(scheme_code, retries=3, delay=5):
    url = f"https://api.mfapi.in/mf/{scheme_code}"
    for attempt in range(retries):
        print(f"Fetching data for scheme code: {scheme_code} from {url} (Attempt {attempt+1}/{retries})...")
        try:
            timeout_val = 20 + attempt * 10
            response = requests.get(url, timeout=timeout_val)
            response.raise_for_status()
            data = response.json()
            
            meta = data.get("meta", {})
            nav_data = data.get("data", [])
            
            if not nav_data:
                print(f"No NAV data found for scheme code: {scheme_code}")
                return None, None
                
            print(f"Successfully fetched {len(nav_data)} records for {meta.get('scheme_name', 'Unknown')}.")
            
            # Create DataFrame
            df = pd.DataFrame(nav_data)
            # The API returns date as 'dd-mm-yyyy' and nav as string.
            # Let's add metadata fields to the raw output for completeness.
            df['scheme_code'] = scheme_code
            df['scheme_name'] = meta.get('scheme_name', '')
            
            # Reorder columns to put metadata first
            cols = ['scheme_code', 'scheme_name', 'date', 'nav']
            df = df[cols]
            
            return df, meta
        except Exception as e:
            print(f"Attempt {attempt+1} failed for scheme code {scheme_code}: {e}")
            if attempt < retries - 1:
                print(f"Waiting {delay} seconds before next attempt...")
                time.sleep(delay)
            else:
                print(f"All attempts failed for scheme code {scheme_code}.")
                return None, None

def main():
    schemes = {
        "125497": "HDFC Top 100 Direct",
        "119551": "SBI Bluechip",
        "120503": "ICICI Bluechip",
        "118632": "Nippon Large Cap",
        "119092": "Axis Bluechip",
        "120841": "Kotak Bluechip"
    }
    
    os.makedirs("data/raw", exist_ok=True)
    all_dfs = []
    
    for code, name in schemes.items():
        df, meta = fetch_scheme_data(code)
        if df is not None:
            # Save individual raw CSV
            filename = f"data/raw/{code}_nav.csv"
            df.to_csv(filename, index=False)
            print(f"Saved {name} data to {filename}")
            all_dfs.append(df)
            
    if all_dfs:
        combined_df = pd.concat(all_dfs, ignore_index=True)
        combined_filename = "data/raw/live_nav_fetched_all.csv"
        combined_df.to_csv(combined_filename, index=False)
        print(f"Saved combined fetched NAV data to {combined_filename}")
        
if __name__ == "__main__":
    main()
