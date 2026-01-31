import requests
import os
import json
import time
import boto3
import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine
from dagster import asset, Output

# --- CONFIGURATION ---
# My own alpha watchlist
TARGET_TICKERS = [
    # Banks & Blue Chips
    "BBCA.JK", "BBNI.JK", "BBRI.JK", "BMRI.JK", "ASII.JK", "INDF.JK", "TLKM.JK",
    
    # Energy, Mining & Minerals
    "ADRO.JK", "AADI.JK", "ADMR.JK", "AMMN.JK", "ANTM.JK", "MDKA.JK", "CDIA.JK",  
    "PGAS.JK", "INDY.JK", "BUMI.JK", "BRMS.JK", "DEWA.JK", "ENRG.JK", "RATU.JK", "RAJA.JK",
    
    # Barito & Prajogo Pangestu Group (High Volatility)
    "BREN.JK", "BRPT.JK", "CUAN.JK", "PTRO.JK",
    
    # Property & Industrial
    "PANI.JK", "SSIA.JK", "BKSL.JK", "IMPC.JK", "INPC.JK", "CBDK.JK",
    
    # Retail & Others
    "ERAA.JK", "CMRY.JK",
]

# --- HELPERS ---
def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=f"http://{os.getenv('MINIO_ENDPOINT', 'minio:9000')}",
        aws_access_key_id=os.getenv("MINIO_ROOT_USER"),
        aws_secret_access_key=os.getenv("MINIO_ROOT_PASSWORD"),
    )

def get_db_engine():
    user = os.getenv("DAGSTER_POSTGRES_USER")
    password = os.getenv("DAGSTER_POSTGRES_PASSWORD")
    db = os.getenv("DAGSTER_POSTGRES_DB")
    return create_engine(f"postgresql://{user}:{password}@timescaledb:5432/{db}")

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_macd(series, fast=12, slow=26, signal=9):
    exp1 = series.ewm(span=fast, adjust=False).mean()
    exp2 = series.ewm(span=slow, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    return macd, signal_line

# --- ASSETS ---
@asset(group_name="ingestion")
def raw_idx_data():
    """
    BRONZE LAYER: Loops through TARGET_TICKERS, fetches data, 
    combines them, and saves a single Master JSON to MinIO.
    """
    all_data = []
    
    print(f"Starting ingestion for {len(TARGET_TICKERS)} tickers...")

    for ticker in TARGET_TICKERS:
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period="1mo")
            
            if df.empty:
                print(f"Warning: No data for {ticker}")
                continue

            df.reset_index(inplace=True)
            df['Date'] = df['Date'].astype(str)
            df['Symbol'] = ticker
            
            all_data.extend(df.to_dict(orient="records"))
            
            time.sleep(0.5)
            
        except Exception as e:
            print(f"Failed to fetch {ticker}: {str(e)}")
            continue

    if not all_data:
        raise ValueError("Ingestion failed: No data fetched for any ticker.")

    # Save to MinIO
    s3 = get_s3_client()
    bucket_name = "idx-market-data"
    file_name = "raw/combined_market_data.json"

    try:
        s3.head_bucket(Bucket=bucket_name)
    except:
        s3.create_bucket(Bucket=bucket_name)

    s3.put_object(
        Bucket=bucket_name,
        Key=file_name,
        Body=json.dumps(all_data),
        ContentType="application/json"
    )

    return Output(
        value=file_name,
        metadata={
            "Storage Path": f"s3://{bucket_name}/{file_name}",
            "Total Records": len(all_data),
            "Tickers Scanned": len(TARGET_TICKERS)
        }
    )

@asset(group_name="transformation", deps=[raw_idx_data])
def stock_indicators(raw_idx_data):
    """
    SILVER LAYER: Reads Master JSON, Groups by Symbol, 
    Calculates Indicators safely, Loads to Postgres.
    """
    # 1. READ (Extract)
    s3 = get_s3_client()
    bucket_name = "idx-market-data"
    
    response = s3.get_object(Bucket=bucket_name, Key=raw_idx_data)
    data = json.loads(response['Body'].read().decode('utf-8'))
    df = pd.DataFrame(data)

    # 2. TRANSFORM (Group-aware Calculation)
    df['Close'] = df['Close'].astype(float)
    df['Date'] = pd.to_datetime(df['Date'])
    processed_dfs = []

    for symbol, group_df in df.groupby('Symbol'):
        group_df = group_df.copy()
        group_df = group_df.sort_values('Date')

        group_df['RSI'] = calculate_rsi(group_df['Close'])
        macd_val, macd_sig = calculate_macd(group_df['Close'])
        group_df['MACD'] = macd_val
        group_df['MACD_Signal'] = macd_sig
        
        processed_dfs.append(group_df)

    # Recombine
    df_final = pd.concat(processed_dfs)

    # Clean up columns
    cols = ['Date', 'Symbol', 'Open', 'High', 'Low', 'Close', 'Volume', 'RSI', 'MACD', 'MACD_Signal']
    df_final = df_final[cols]

    # 3. LOAD (To Postgres)
    engine = get_db_engine()
    
    df_final.to_sql('market_data_silver', engine, if_exists='replace', index=False)

    return Output(
        value="market_data_silver",
        metadata={
            "Database Table": "market_data_silver",
            "Tickers Processed": df_final['Symbol'].nunique(),
            "Total Rows": len(df_final)
        }
    )

@asset(group_name="alerting", deps=[stock_indicators])
def telegram_alerts():
    """
    GOLD LAYER: Reads Silver data, filters for RSI < 35, 
    and sends a Telegram alert if opportunities exist.
    """
    # 1. Load Data from DB
    engine = get_db_engine()
    
    # Query: Get latest available date first
    latest_date_query = 'SELECT MAX("Date") FROM market_data_silver'
    latest_date = pd.read_sql(latest_date_query, engine).iloc[0, 0]
    
    # Query: Select stocks with low RSI on that specific date
    query = f"""
    SELECT "Symbol", "Close", "RSI"
    FROM market_data_silver
    WHERE "RSI" < 35
    AND "Date" = '{latest_date}'
    ORDER BY "RSI" ASC;
    """
    df = pd.read_sql(query, engine)
    
    if df.empty:
        print("No opportunities today. Silence is golden.")
        return Output(value="No Alerts", metadata={"Status": "No Signals"})

    # 2. Format the Message
    message = f"🚨 *OVERSOLD ALERT* ({latest_date}) 🚨\n\n"
    for _, row in df.iterrows():
        symbol = row['Symbol']
        rsi = row['RSI']
        price = row['Close']
        message += f"💎 *{symbol}*\n"
        message += f"RSI: {rsi:.2f} | Price: {price:,.0f}\n\n"
    
    message += "👉 [Check Dashboard](https://bi.earthen.my.id)"

    # 3. Send via Telegram API
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        raise ValueError("Telegram credentials missing in environment variables.")

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status() # Check for HTTP errors
        status = "Sent"
    except Exception as e:
        print(f"Failed to send alert: {e}")
        status = "Failed"

    return Output(
        value=status,
        metadata={
            "Signals Found": len(df),
            "Top Pick": df.iloc[0]['Symbol'] if not df.empty else "None",
            "Status": status
        }
    )
