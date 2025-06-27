import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

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
st.subheader("IPO List with Filters")
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

# Function to fetch historical price data
def get_price_data(ticker, days=90):
    since = datetime.today() - timedelta(days=days)
    df = yf.download(ticker + ".NS", start=since.strftime("%Y-%m-%d"))
    return df if not df.empty else None

# Detect base price, lowest price, dip %, last close
def detect_u_curve_metrics(df):
    if len(df) < 30 or 'Open' not in df.columns or 'Low' not in df.columns or 'Close' not in df.columns:
        return None

    base_price = float(df['Open'].iloc[0])
    min_low = float(df['Low'].min())
    dip_pct = (base_price - min_low) / base_price * 100
    last_close = float(df['Close'].iloc[-1])

    return {
        "Base Price": base_price,
        "Lowest Price": min_low,
        "Max Dip %": dip_pct,
        "Last Close": last_close
    }

# Prepare results list
results = []

for symbol in filtered_df['Symbol'].unique():
    hist_df = get_price_data(symbol)
    if hist_df is None or len(hist_df) < 30:
        continue

    metrics = detect_u_curve_metrics(hist_df)
    if metrics is None:
        continue

    results.append({
        "Stock Name": symbol,
        "Base Price (IPO Listing Price)": metrics["Base Price"],
        "Lowest Price Since IPO": metrics["Lowest Price"],
        "Max Dip from Base Price (%)": metrics["Max Dip %"],
        "Last Close Price": metrics["Last Close"]
    })

# Show the table
if results:
    results_df = pd.DataFrame(results)
    st.dataframe(results_df)
else:
    st.write("No data available for the selected filters and symbols.")
