import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

st.set_page_config(layout="wide")
st.title("📈 Recent IPOs - Swing Trade Monitor")
st.markdown("*Data from Chartink screener: [IPO 365 by @finallynitin](https://chartink.com/screener/ipo-365-atfinallynitin)*")

# CSV from GitHub
csv_url = "https://raw.githubusercontent.com/rama210989/ipo_swing_trader/refs/heads/main/IPO%20365%20finallynitin%2C%20Technical%20Analysis%20Scanner.csv"

@st.cache_data
def load_ipo_csv(url):
    df = pd.read_csv(url)
    df.columns = [col.strip().replace('"', '') for col in df.columns]
    df['% Chg'] = df['% Chg'].str.replace('%', '', regex=False).astype(float)
    df['Price'] = df['Price'].astype(float)
    df['Volume'] = df['Volume'].str.replace(',', '', regex=False).astype(int)
    return df

df = load_ipo_csv(csv_url)

# Filter UI
st.subheader("📋 IPO List with Filters")
chg_filter = st.slider(
    "% Change filter",
    float(df['% Chg'].min()), 
    float(df['% Chg'].max()), 
    (float(df['% Chg'].min()), float(df['% Chg'].max()))
)
price_filter = st.slider(
    "Price filter", 
    float(df['Price'].min()), 
    float(df['Price'].max()), 
    (float(df['Price'].min()), float(df['Price'].max()))
)

filtered_df = df[
    (df['% Chg'] >= chg_filter[0]) & (df['% Chg'] <= chg_filter[1]) & 
    (df['Price'] >= price_filter[0]) & (df['Price'] <= price_filter[1])
]

def get_price_data(ticker, days=90):
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
    u_curve_formed = dip_pct >= 5  # threshold is 5%

    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()

    buy_trigger = False
    buy_date = None

    if u_curve_formed:
        crossed = (df['Close'] > base_price) & (df['Close'].shift(1) <= base_price)
        crossed_series = crossed[crossed]
        if not crossed_series.empty:
            buy_trigger = True
            buy_date = crossed_series.index[0]

    sell_30_trigger = False
    sell_all_trigger = False

    if buy_trigger and buy_date in df.index:
        df_post_buy = df.loc[buy_date:]
        if len(df_post_buy) > 0:
            last_close_post_buy = float(df_post_buy['Close'].iloc[-1])
            ema20_latest = float(df_post_buy['EMA20'].iloc[-1])
            ema50_latest = float(df_post_buy['EMA50'].iloc[-1])

            sell_30_trigger = bool(last_close_post_buy < ema20_latest)
            sell_all_trigger = bool(last_close_post_buy < ema50_latest)

    return {
        "Base Price (IPO Listing Price)": round(base_price, 2),
        "Lowest Price Since IPO": round(min_low, 2),
        "Max Dip from Base Price (%)": round(dip_pct, 2),
        "Last Close Price": round(last_close, 2),
        "U-Curve Dip ≥5%": "✅" if u_curve_formed else "",
        "BUY Trigger": "✅" if buy_trigger else "",
        "BUY Date": buy_date.strftime("%Y-%m-%d") if buy_date else "",
        "SELL 30% Trigger": "🔁" if sell_30_trigger else "",
        "SELL ALL Trigger": "🚪" if sell_all_trigger else ""
    }

# Process each symbol
results = []

for symbol in filtered_df['Symbol'].unique():
    hist_df = get_price_data(symbol)
    if hist_df is None or len(hist_df) < 30:
        continue

    signals = analyze_triggers(hist_df)
    if signals is None:
        continue

    results.append({
        "Stock Name": symbol,
        **signals
    })

# Display table
if results:
    results_df = pd.DataFrame(results)
    st.subheader("📊 Trigger Table")
    st.dataframe(results_df)
else:
    st.write("⚠️ No data available for the selected filters and symbols.")
