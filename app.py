import streamlit as st
import pandas as pd
from trigger import get_price_data, analyze_triggers

st.set_page_config(layout="wide")
st.title("📈 Recent IPOs - Swing Trade Monitor")
st.markdown("*Data from Chartink screener: [IPO 365 by @finallynitin](https://chartink.com/screener/ipo-365-atfinallynitin)*")

# Load IPO CSV
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

# IPO Table Display
st.subheader("📋 IPO List")
st.dataframe(df[['Stock Name', 'Symbol', '% Chg', 'Price', 'Volume']])

# Trigger Button
if st.button("🚀 Run Trigger Analysis"):
    st.subheader("🔎 Trigger Debug Output")
    results = []

    for symbol in df['Symbol']:
        ticker = symbol + ".NS"
        st.write(f"🔍 Testing {ticker}")

        price_df = get_price_data(ticker)
        if price_df is None or len(price_df) < 5:
            st.warning(f"❌ Skipping {ticker} – No or insufficient data.")
            continue

        triggers = analyze_triggers(price_df)
        if triggers:
            st.success(f"✅ {symbol}: {triggers['Trigger']}")
            results.append({
                "Stock": symbol,
                **triggers
            })
        else:
            st.warning(f"⚠️ Could not analyze triggers for {symbol}")

    if results:
        st.subheader("📊 Trigger Summary Table")
        st.dataframe(pd.DataFrame(results))
    else:
        st.info("⚠️ No triggers identified.")
