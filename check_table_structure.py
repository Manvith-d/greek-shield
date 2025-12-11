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

# Check table structure
cursor.execute("DESCRIBE TABLE OPTIONS_SNAPSHOT")
columns = cursor.fetchall()

print("="*60)
print("ACTUAL TABLE STRUCTURE:")
print("="*60)
for col in columns:
    print(f"Column: {col[0]}, Type: {col[1]}")

print("\n" + "="*60)
print("Tell me what columns you see above!")
print("="*60)

cursor.close()
conn.close()