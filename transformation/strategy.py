import pandas as pd

def apply_swing_strategy(df: pd.DataFrame) -> pd.DataFrame:
    """
    GOLD LAYER LOGIC
    Input: DataFrame with 'RSI' and 'Close'.
    Output: Filtered DataFrame with 'Signal' (Buy/Sell).
    """
    # 1. Clean & Sort
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values(by='Date')

    # 2. The Strategy (Swing Setup)
    # Rule: RSI < 30 (Oversold) AND Close > 200-day Trend (Context)
    # (Since we don't have EMA-200 yet, we will just use RSI < 30 for this test)
    
    is_oversold = df['RSI'] < 30
    
    # Create the filter
    signals = df[is_oversold].copy()
    
    if signals.empty:
        return pd.DataFrame()

    # 3. Add Metadata
    signals['Signal'] = 'BUY'
    signals['Created_At'] = pd.Timestamp.now()
    
    # Return only actionable columns
    return signals[['Date', 'Symbol', 'Close', 'RSI', 'Signal', 'Created_At']]
