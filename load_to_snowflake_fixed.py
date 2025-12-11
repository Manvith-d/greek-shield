#!/usr/bin/env python3
"""
Load S3 data to Snowflake
MATCHES THE ACTUAL TABLE STRUCTURE YOUR TA CREATED
"""

import os
from dotenv import load_dotenv
import boto3
import snowflake.connector
import json
import logging
from datetime import date
import hashlib

load_dotenv()

logging.basicConfig(level=logging.INFO)

def get_snowflake_connection():
    """Connect using PAT"""
    return snowflake.connector.connect(
        user=os.getenv('SNOWFLAKE_USER'),
        password=os.getenv('SNOWFLAKE_PASSWORD'),  # PAT as password
        account=os.getenv('SNOWFLAKE_ACCOUNT'),
        warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
        database=os.getenv('SNOWFLAKE_DATABASE'),
        schema=os.getenv('SNOWFLAKE_SCHEMA'),
        role=os.getenv('SNOWFLAKE_ROLE')
    )

def get_data_from_s3(ticker='AAPL'):
    """Download from S3"""
    
    logging.info(f"📥 Downloading from S3...")
    
    s3 = boto3.client(
        's3',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_REGION')
    )
    
    bucket = os.getenv('S3_BUCKET_NAME')
    today = date.today()
    s3_key = f"options-data/{ticker}/{today.year}/{today.month:02d}/{today.day:02d}/options_{ticker}_{today}.json"
    
    logging.info(f"   Reading: s3://{bucket}/{s3_key}")
    
    try:
        response = s3.get_object(Bucket=bucket, Key=s3_key)
        data = json.loads(response['Body'].read())
        logging.info(f"✅ Downloaded {len(data)} contracts")
        return data
    except Exception as e:
        logging.error(f"❌ S3 error: {e}")
        return None

def load_to_snowflake(data):
    """Load to Snowflake using ACTUAL column names"""
    
    if not data:
        return False
    
    logging.info(f"📤 Loading {len(data)} rows to Snowflake...")
    
    try:
        conn = get_snowflake_connection()
        logging.info("✅ Connected to Snowflake")
        
        cursor = conn.cursor()
        loaded = 0
        
        for option in data:
            try:
                # Generate MD5 hash for ID
                id_string = f"{option['contract_symbol']}_{option['collection_timestamp']}"
                id_md5 = hashlib.md5(id_string.encode()).hexdigest()
                
                # INSERT using ACTUAL column names from the table
                cursor.execute("""
                    INSERT INTO OPTIONS_SNAPSHOT 
                    (SNAPSHOT_TS, SYMBOL, CONTRACT_SYMBOL, OPTION_TYPE,
                     STRIKE, EXPIRY, BID, ASK, LAST_PRICE, 
                     VOLUME, OPEN_INTEREST, IMPLIED_VOL, UNDERLYING_PRICE,
                     DTE, ID_MD5)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    option['collection_timestamp'],
                    option['ticker'],
                    option['contract_symbol'],
                    option['option_type'],
                    option['strike_price'],
                    option['expiration_date'],
                    option['bid'],
                    option['ask'],
                    option['last_price'],
                    option['volume'],
                    option['open_interest'],
                    option['implied_volatility'],
                    option['underlying_price'],
                    option['days_to_expiry'],
                    id_md5
                ))
                loaded += 1
                
                if loaded % 50 == 0:
                    logging.info(f"   {loaded} rows loaded...")
                    
            except Exception as e:
                logging.error(f"Error: {e}")
                continue
        
        conn.commit()
        logging.info(f"✅ Successfully loaded {loaded} rows!")
        
        # Verify
        cursor.execute("SELECT COUNT(*) FROM OPTIONS_SNAPSHOT")
        total = cursor.fetchone()[0]
        logging.info(f"✅ Total in Snowflake: {total} rows")
        
        # Show sample
        logging.info("\n📊 Sample data:")
        cursor.execute("""
            SELECT SYMBOL, STRIKE, OPTION_TYPE, LAST_PRICE, EXPIRY 
            FROM OPTIONS_SNAPSHOT 
            ORDER BY SNAPSHOT_TS DESC
            LIMIT 5
        """)
        for row in cursor.fetchall():
            logging.info(f"   {row[0]} ${row[1]} {row[2]} @ ${row[3]} exp:{row[4]}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logging.error(f"❌ Error: {e}")
        return False

def main():
    logging.info("="*60)
    logging.info("S3 → SNOWFLAKE LOADER (FIXED)")
    logging.info("="*60)
    
    ticker = 'AAPL'
    
    # Get from S3
    data = get_data_from_s3(ticker)
    
    if not data:
        logging.error("No data in S3")
        return
    
    # Load to Snowflake
    success = load_to_snowflake(data)
    
    if success:
        logging.info("\n" + "="*60)
        logging.info("✅ PIPELINE COMPLETED!")
        logging.info("="*60)

if __name__ == "__main__":
    main()