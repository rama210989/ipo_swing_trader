import streamlit as st
import pandas as pd
from trigger import get_price_data, analyze_triggers

st.set_page_config(layout="wide")
st.title("📈 Recent IPOs - Swing Trade Monitor")
st.markdown("*Data from Chartink screener: [IPO 365 by @finallynitin](https://chartink.com/screener/ipo-365-atfinallynitin)*")

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

results = []

st.subheader("🔎 Debug Output")

for symbol in filtered_df['Symbol'].unique():
    ticker = symbol + ".NS"
    st.write(f"🔄 Checking {ticker}")
    hist_df = get_price_data(symbol)
    if hist_df is None or len(hist_df) < 30:
        st.write(f"❌ Skipping {symbol} – No or insufficient data.")
        continue

    triggers = analyze_triggers(hist_df)
    if triggers is None:
        st.write(f"⚠️ Could not analyze triggers for {symbol}")
        continue

    results.append({
        "Stock Name": symbol,
        **triggers
    })

if results:
    results_df = pd.DataFrame(results)
    st.subheader("📊 Trigger Table")
    st.dataframe(results_df)
else:
    st.write("⚠️ No data available for the selected filters and symbols.")
