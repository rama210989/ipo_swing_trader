import streamlit as st
import pandas as pd
from trigger import get_price_data, analyze_trigger

st.set_page_config(layout="wide")
st.title("📈 Recent IPOs - Swing Trade Monitor")
st.markdown("*Data from Chartink screener: [IPO 365 by @finallynitin](https://chartink.com/screener/ipo-365-atfinallynitin)*")

# CSV Source
csv_url = "https://raw.githubusercontent.com/rama210989/ipo_swing_trader/refs/heads/main/IPO%20365%20finallynitin%2C%20Technical%20Analysis%20Scanner.csv"

@st.cache_data
def load_csv(url):
    df = pd.read_csv(url)
    df.columns = [col.strip().replace('"', '') for col in df.columns]
    df['% Chg'] = df['% Chg'].str.replace('%', '', regex=False).astype(float)
    df['Price'] = df['Price'].astype(float)
    df['Volume'] = df['Volume'].str.replace(',', '', regex=False).astype(int)
    return df

df = load_csv(csv_url)

st.subheader("📋 IPO List")
st.dataframe(df[['Stock Name', 'Symbol', '% Chg', 'Price', 'Volume']], use_container_width=True)

if st.button("Run Trigger Analysis"):
    st.subheader("🔎 Trigger Debug Output")

    results = []
    for symbol in df['Symbol']:
        ticker = symbol + ".NS"
        st.write(f"🔄 Checking {ticker}")
        price_df = get_price_data(ticker)

        if price_df is None or len(price_df) < 2:
            st.warning(f"❌ Skipping {ticker} – No or insufficient data.")
            continue

        trigger_info = analyze_trigger(price_df)
        if trigger_info:
            results.append({
                "Symbol": symbol,
                **trigger_info
            })
            st.success(f"✅ {symbol} → Trigger: {trigger_info['Trigger']}")
        else:
            st.warning(f"⚠️ Could not analyze triggers for {symbol}")

    if results:
        st.subheader("📊 Trigger Summary Table")
        st.dataframe(pd.DataFrame(results), use_container_width=True)
    else:
        st.info("No triggers identified.")
