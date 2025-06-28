import streamlit as st
import pandas as pd
from trigger import get_price_data, analyze_triggers

st.set_page_config(layout="wide")
st.title("📈 Recent IPOs - Swing Trade Monitor")
st.markdown("*Data from Chartink screener: [IPO 365 by @finallynitin](https://chartink.com/screener/ipo-365-atfinallynitin)*")

# CSV URL
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

st.subheader("📋 IPO List")
st.dataframe(df[['Stock Name', 'Symbol', '% Chg', 'Price', 'Volume']])

if st.button("Run Trigger Analysis"):
    st.subheader("🔎 Debug Output")
    results = []
    for symbol in df['Symbol']:
        ticker = symbol + ".NS"  # append suffix here
        st.write(f"🔄 Checking {ticker}")

        hist_df = get_price_data(ticker)
        if hist_df is None or len(hist_df) < 30:
            st.warning(f"❌ Skipping {ticker} – No or insufficient data.")
            continue

        triggers = analyze_triggers(hist_df)
        if triggers is None:
            st.warning(f"⚠️ Could not analyze triggers for {ticker}")
            continue

        st.success(f"✅ Data found and triggers analyzed for {ticker}")
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
