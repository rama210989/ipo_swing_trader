import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

def get_price_data(ticker, days=180):
    since = datetime.today() - timedelta(days=days)
    df = yf.download(ticker + ".NS", start=since.strftime("%Y-%m-%d"))
    return df if not df.empty else None

def analyze_triggers(df):
    if len(df) < 30 or 'Open' not in df.columns or 'Low' not in df.columns or 'Close' not in df.columns:
        return None

    if isinstance(df['Close'], pd.DataFrame):
        df['Close'] = df['Close'].iloc[:, 0]

    base_price = float(df['Open'].iloc[0])
    min_low = float(df['Low'].min())
    dip_pct = (base_price - min_low) / base_price * 100
    last_close = float(df['Close'].iloc[-1])

    u_curve_formed = dip_pct >= 5

    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()

    buy_trigger = False
    buy_date = None

    if u_curve_formed:
        crossed = (df['Close'] > base_price) & (df['Close'].shift(1) <= base_price)

        if isinstance(crossed, pd.DataFrame):
            crossed = crossed.iloc[:, 0]

        crossed = crossed.fillna(False).astype(bool)

        if crossed.any():
            buy_trigger = True
            buy_date = df.index[crossed.idxmax()]
        else:
            buy_trigger = False
            buy_date = None

    # rest of code unchanged...
