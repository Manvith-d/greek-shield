#!/usr/bin/env python3
import os
from dotenv import load_dotenv
import snowflake.connector

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

cursor = conn.cursor()

# Check total rows
cursor.execute("SELECT COUNT(*) FROM OPTIONS_SNAPSHOT")
total = cursor.fetchone()[0]
print(f"✅ Total contracts in Snowflake: {total}")

# Check dates
cursor.execute("SELECT MIN(SNAPSHOT_TS), MAX(SNAPSHOT_TS) FROM OPTIONS_SNAPSHOT")
date_range = cursor.fetchone()
print(f"✅ Date range: {date_range[0]} to {date_range[1]}")

# Check Greeks columns (should be NULL)
cursor.execute("SELECT COUNT(*) FROM OPTIONS_SNAPSHOT WHERE DELTA IS NOT NULL")
greeks_count = cursor.fetchone()[0]
print(f"ℹ️  Greeks calculated: {greeks_count} rows")
print(f"ℹ️  Greeks pending: {total - greeks_count} rows")

# Show sample
cursor.execute("""
    SELECT SYMBOL, STRIKE, OPTION_TYPE, LAST_PRICE, IMPLIED_VOL, DELTA
    FROM OPTIONS_SNAPSHOT 
    LIMIT 5
""")
print("\n📊 Sample data:")
for row in cursor.fetchall():
    print(f"   {row[0]} ${row[1]} {row[2]} price=${row[3]} IV={row[4]} Delta={row[5]}")

cursor.close()
conn.close()

print("\n✅ Verification complete!")