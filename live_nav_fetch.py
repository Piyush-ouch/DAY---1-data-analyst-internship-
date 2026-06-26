import os
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Tuple, Optional
import requests
import pandas as pd

# Configure professional logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def fetch_scheme_data(
    session: requests.Session,
    scheme_code: str,
    retries: int = 3,
    delay: int = 5
) -> Tuple[Optional[pd.DataFrame], Optional[dict]]:
    """
    Fetches historical NAV data for a given scheme code from mfapi.in.
    Uses Session pooling for speed and handles retries with progressive timeouts.
    """
    url = f"https://api.mfapi.in/mf/{scheme_code}"
    
    for attempt in range(retries):
        logger.info(f"Fetching scheme {scheme_code} (Attempt {attempt+1}/{retries})...")
        try:
            # progressive timeout to handle latency spike
            timeout_val = 20 + attempt * 10
            response = session.get(url, timeout=timeout_val)
            response.raise_for_status()
            data = response.json()
            
            meta = data.get("meta", {})
            nav_data = data.get("data", [])
            
            if not nav_data:
                logger.warning(f"No NAV data found for scheme {scheme_code}")
                return None, None
                
            logger.info(f"Successfully fetched {len(nav_data)} records for {meta.get('scheme_name', 'Unknown')}.")
            
            # Structuring data efficiently
            df = pd.DataFrame(nav_data)
            
            # Cast types early to minimize memory footprint
            df['scheme_code'] = int(scheme_code)
            df['scheme_name'] = meta.get('scheme_name', '').strip()
            df['nav'] = pd.to_numeric(df['nav'], errors='coerce').astype('float32')
            
            # Reorder columns
            cols = ['scheme_code', 'scheme_name', 'date', 'nav']
            df = df[cols]
            
            return df, meta
            
        except Exception as e:
            logger.error(f"Attempt {attempt+1} failed for scheme {scheme_code}: {e}")
            if attempt < retries - 1:
                import time
                time.sleep(delay)
                
    logger.error(f"All attempts failed for scheme {scheme_code}.")
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
    
    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    all_dfs = []
    
    # Session reuse for socket pooling (speed optimization)
    with requests.Session() as session:
        # Concurrent fetching using thread pool (multithreading optimization)
        with ThreadPoolExecutor(max_workers=len(schemes)) as executor:
            future_to_scheme = {
                executor.submit(fetch_scheme_data, session, code): (code, name)
                for code, name in schemes.items()
            }
            
            for future in as_completed(future_to_scheme):
                code, name = future_to_scheme[future]
                try:
                    df, meta = future.result()
                    if df is not None:
                        # Save individual raw CSV
                        filename = output_dir / f"{code}_nav.csv"
                        df.to_csv(filename, index=False)
                        logger.info(f"Saved {name} data to {filename}")
                        all_dfs.append(df)
                except Exception as exc:
                    logger.error(f"Scheme {code} generated an exception: {exc}")
                    
    if all_dfs:
        combined_df = pd.concat(all_dfs, ignore_index=True)
        combined_filename = output_dir / "live_nav_fetched_all.csv"
        
        # Optimize memory usage
        combined_df['scheme_code'] = combined_df['scheme_code'].astype('int32')
        combined_df['nav'] = combined_df['nav'].astype('float32')
        
        combined_df.to_csv(combined_filename, index=False)
        logger.info(f"Saved combined fetched NAV data to {combined_filename}")

if __name__ == "__main__":
    main()
