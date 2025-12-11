#!/usr/bin/env python3
"""
Analyze Greeks to find high-risk positions
"""

import os
from dotenv import load_dotenv
import snowflake.connector
import pandas as pd

load_dotenv()

conn = snowflake.connector.connect(
    user=os.getenv('SNOWFLAKE_USER'),
    password=os.getenv('SNOWFLAKE_PASSWORD'),
    account=os.getenv('SNOWFLAKE_ACCOUNT'),
    warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
    database=os.getenv('SNOWFLAKE_DATABASE'),
    schema=os.getenv('SNOWFLAKE_SCHEMA'),
    role=os.getenv('SNOWFLAKE_ROLE')
)

print("="*70)
print("OPTIONS RISK ANALYSIS")
print("="*70)

# Analysis 1: High Gamma (risky positions)
print("\n🔴 HIGH GAMMA RISK (Position moves fast):")
query1 = """
SELECT SYMBOL, STRIKE, OPTION_TYPE, GAMMA, DELTA, DTE
FROM OPTIONS_SNAPSHOT
WHERE GAMMA > 0.05 AND DELTA IS NOT NULL
ORDER BY GAMMA DESC
LIMIT 10
"""
df1 = pd.read_sql(query1, conn)
print(df1.to_string(index=False))

# Analysis 2: High Theta (rapid decay)
print("\n⏰ HIGH THETA DECAY (Losing value fast):")
query2 = """
SELECT SYMBOL, STRIKE, OPTION_TYPE, THETA, LAST_PRICE, DTE
FROM OPTIONS_SNAPSHOT
WHERE THETA < -0.10 AND DELTA IS NOT NULL
ORDER BY THETA
LIMIT 10
"""
df2 = pd.read_sql(query2, conn)
print(df2.to_string(index=False))

# Analysis 3: Deep ITM vs OTM
print("\n📊 DELTA DISTRIBUTION:")
query3 = """
SELECT 
    CASE 
        WHEN ABS(DELTA) > 0.7 THEN 'Deep ITM'
        WHEN ABS(DELTA) BETWEEN 0.3 AND 0.7 THEN 'ATM'
        ELSE 'OTM'
    END as moneyness,
    COUNT(*) as contracts,
    AVG(IMPLIED_VOL) as avg_iv,
    AVG(THETA) as avg_theta
FROM OPTIONS_SNAPSHOT
WHERE DELTA IS NOT NULL
GROUP BY moneyness
"""
df3 = pd.read_sql(query3, conn)
print(df3.to_string(index=False))

# Analysis 4: Volatility Smile
print("\n📈 IMPLIED VOLATILITY BY STRIKE:")
query4 = """
SELECT 
    STRIKE,
    AVG(IMPLIED_VOL) as avg_iv,
    AVG(VEGA) as avg_vega,
    COUNT(*) as contracts
FROM OPTIONS_SNAPSHOT
WHERE DELTA IS NOT NULL AND EXPIRY = (SELECT MIN(EXPIRY) FROM OPTIONS_SNAPSHOT)
GROUP BY STRIKE
ORDER BY STRIKE
"""
df4 = pd.read_sql(query4, conn)
print(df4.to_string(index=False))

conn.close()

print("\n" + "="*70)
print("✅ ANALYSIS COMPLETE")
print("="*70)