import pandas as pd
from dagster import asset, Output, AssetIn
from sqlalchemy import create_engine
from .strategy import apply_swing_strategy

# Database Connection (Adjust if your credentials differ)
DB_CONNECTION = "postgresql://terraNova:Starl1ght!2026@timescaledb:5432/trading_lake"

def get_db_engine():
    return create_engine(DB_CONNECTION)

@asset(
    group_name="transformation",
    ins={
        "stock_indicators": AssetIn(key="stock_indicators")
    }
)
def trade_signals(context, stock_indicators):
    """
    GOLD LAYER: Reads Silver data, applies strategy.
    """
    table_name = stock_indicators 
    engine = get_db_engine()
    query = f"SELECT * FROM {table_name}"
    df_silver = pd.read_sql(query, engine)
    context.log.info(f"Loaded {len(df_silver)} rows from {table_name}")
    df_gold = apply_swing_strategy(df_silver)
    if df_gold.empty:
        context.log.info("No buy signals found today.")
        return Output(value="No Signals", metadata={"Status": "Empty"})
    gold_table = "market_data_gold"
    df_gold.to_sql(gold_table, engine, if_exists='append', index=False)
    return Output(
        value=gold_table,
        metadata={
            "New Signals": len(df_gold),
            "Tickers": list(df_gold['Symbol'].unique())
        }
    )
