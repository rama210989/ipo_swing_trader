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

    base_price = float(df['Open'].iloc[0])
    min_low = float(df['Low'].min())
    dip_pct = (base_price - min_low) / base_price * 100
    last_close = float(df['Close'].iloc[-1])

    u_curve_formed = dip_pct >= 5  # Threshold for dip

    # Calculate EMAs
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()

    buy_trigger = False
    buy_date = None

    if u_curve_formed:
        crossed = (df['Close'] > base_price) & (df['Close'].shift(1) <= base_price)
        if crossed.any():
            buy_trigger = True
            buy_date = df.index[crossed.idxmax()]  # first crossover date

    sell_30_trigger = False
    sell_all_trigger = False

    if buy_trigger and buy_date in df.index:
        df_post_buy = df.loc[buy_date:]
        if len(df_post_buy) > 0:
            last_close_post_buy = df_post_buy['Close'].iloc[-1]
            ema20_latest = df_post_buy['EMA20'].iloc[-1]
            ema50_latest = df_post_buy['EMA50'].iloc[-1]

            sell_30_trigger = last_close_post_buy < ema20_latest
            sell_all_trigger = last_close_post_buy < ema50_latest

    return {
        "Base Price": round(base_price, 2),
        "Lowest Price": round(min_low, 2),
        "Max Dip %": round(dip_pct, 2),
        "Last Close": round(last_close, 2),
        "U-Curve Dip ≥5%": u_curve_formed,
        "BUY Trigger": "✅" if buy_trigger else "",
        "BUY Date": buy_date.strftime("%Y-%m-%d") if buy_date else "",
        "SELL 30% Trigger": "🔁" if sell_30_trigger else "",
        "SELL ALL Trigger": "🚪" if sell_all_trigger else ""
    }
