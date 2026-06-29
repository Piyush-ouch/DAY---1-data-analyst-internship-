-- queries.sql
-- 10 Analytical SQL Queries for Bluestock Mutual Fund SQLite Database

-- 1. Top 5 funds by AUM (Assets Under Management)
SELECT 
    f.amfi_code,
    f.scheme_name, 
    f.fund_house, 
    p.aum_crore
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
ORDER BY p.aum_crore DESC
LIMIT 5;

-- 2. Average NAV per month for each scheme (ordered by scheme and month)
SELECT 
    f.amfi_code,
    f.scheme_name, 
    strftime('%Y-%m', n.date) AS nav_month, 
    ROUND(AVG(n.nav), 4) AS avg_nav
FROM fact_nav n
JOIN dim_fund f ON n.amfi_code = f.amfi_code
GROUP BY f.amfi_code, f.scheme_name, nav_month
ORDER BY f.scheme_name, nav_month;

-- 3. Monthly SIP Inflow YoY Growth using Window Functions
SELECT 
    month,
    sip_inflow_crore,
    LAG(sip_inflow_crore, 12) OVER (ORDER BY month) AS prev_year_inflow_crore,
    ROUND(((sip_inflow_crore - LAG(sip_inflow_crore, 12) OVER (ORDER BY month)) * 100.0) / LAG(sip_inflow_crore, 12) OVER (ORDER BY month), 2) AS calculated_yoy_growth_pct,
    yoy_growth_pct AS source_yoy_growth_pct
FROM monthly_sip_inflows
ORDER BY month;

-- 4. Transaction volume and count grouped by state (ordered by total investment amount)
SELECT 
    state,
    COUNT(*) AS total_transactions,
    ROUND(SUM(amount_inr), 2) AS total_amount_inr,
    ROUND(AVG(amount_inr), 2) AS avg_amount_inr
FROM fact_transactions
GROUP BY state
ORDER BY total_amount_inr DESC;

-- 5. Funds with an expense ratio < 1.0% (ordered from lowest to highest expense ratio)
SELECT 
    amfi_code, 
    scheme_name, 
    fund_house, 
    expense_ratio_pct
FROM dim_fund
WHERE expense_ratio_pct < 1.0
ORDER BY expense_ratio_pct ASC;

-- 6. Top 5 investors by total transaction amount (and their geographic and demographics details)
SELECT 
    investor_id,
    COUNT(*) AS transaction_count,
    ROUND(SUM(amount_inr), 2) AS total_invested_inr,
    state,
    city,
    age_group,
    gender
FROM fact_transactions
GROUP BY investor_id
ORDER BY total_invested_inr DESC
LIMIT 5;

-- 7. Average transaction amount and count for SIP vs Lumpsum vs Redemption
SELECT 
    transaction_type,
    COUNT(*) AS total_transactions,
    ROUND(SUM(amount_inr), 2) AS total_amount_inr,
    ROUND(AVG(amount_inr), 2) AS avg_amount_inr
FROM fact_transactions
GROUP BY transaction_type
ORDER BY avg_amount_inr DESC;

-- 8. Portfolio stock holdings: Unique stocks, total market value, and average weight grouped by Sector
SELECT 
    sector,
    COUNT(DISTINCT stock_symbol) AS unique_stocks_count,
    COUNT(*) AS total_holdings_entries,
    ROUND(AVG(weight_pct), 2) AS avg_weight_pct,
    ROUND(SUM(market_value_cr), 2) AS total_market_value_cr
FROM portfolio_holdings
GROUP BY sector
ORDER BY total_market_value_cr DESC;

-- 9. Transaction metrics grouped by investor demographics (Age Group & Gender)
SELECT 
    age_group,
    gender,
    COUNT(*) AS txn_count,
    ROUND(SUM(amount_inr), 2) AS total_amount_inr,
    ROUND(AVG(amount_inr), 2) AS avg_amount_inr
FROM fact_transactions
GROUP BY age_group, gender
ORDER BY age_group, gender;

-- 10. High-performing funds defined as Alpha > 1.0 and Beta < 1.0 (Higher returns with lower risk than benchmark)
SELECT 
    f.amfi_code,
    f.scheme_name,
    p.alpha,
    p.beta,
    p.sharpe_ratio,
    p.return_3yr_pct,
    p.return_5yr_pct
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
WHERE p.alpha > 1.0 AND p.beta < 1.0
ORDER BY p.alpha DESC;
