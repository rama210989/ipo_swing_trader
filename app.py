import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objs as go
from datetime import datetime, timedelta

st.title("📈 Recent IPOs")
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
chg_filter = st.slider("% Change filter", float(df['% Chg'].min()), float(df['% Chg'].max()), (float(df['% Chg'].min()), float(df['% Chg'].max())))
price_filter = st.slider("Price filter", float(df['Price'].min()), float(df['Price'].max()), (float(df['Price'].min()), float(df['Price'].max())))
filtered_df = df[(df['% Chg'] >= chg_filter[0]) & (df['% Chg'] <= chg_filter[1]) & 
                 (df['Price'] >= price_filter[0]) & (df['Price'] <= price_filter[1])]
st.dataframe(filtered_df)

# Analysis section
st.markdown("---")
st.header("📊 U-Shape Recovery & EMA Signals (Steps 2–4)")

# Get Yahoo Finance data
def get_price_data(ticker, days=90):
    since = datetime.today() - timedelta(days=days)
    df = yf.download(ticker + ".NS", start=since.strftime("%Y-%m-%d"))
    return df if not df.empty else None

# Detect U-shape recovery
def detect_u_shape(df):
    if len(df) < 30:
        return False

    min_pos = df['Close'].argmin()
    base_price = df['Close'].iloc[min_pos]
    recovery = df['Close'].iloc[min_pos:].max()

    return (
        df['Close'].iloc[-1] > base_price and 
        (recovery - base_price) / base_price > 0.1
    )

# Apply EMA indicators
def apply_ema_signals(df):
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    return df

# Trade signal logic
def trade_signals(df, base_price):
    latest_close = df['Close'].iloc[-1]
    stop_loss = base_price * 0.95
    return {
        "📥 Entry Trigger": latest_close > base_price,
        "⚠️ Stop Loss Hit": latest_close < stop_loss,
        "🔁 Exit 30% (below EMA20)": latest_close < df['EMA20'].iloc[-1],
        "🚪 Exit All (below EMA50)": latest_close < df['EMA50'].iloc[-1]
    }

# Analyze and display for each symbol
for symbol in filtered_df['Symbol'].unique():
    st.markdown(f"#### {symbol}")
    hist_df = get_price_data(symbol)

    if hist_df is None or len(hist_df) < 30:
        st.write("⚠️ Not enough historical data.")
        continue

    if detect_u_shape(hist_df):
        base_price = hist_df['Close'].iloc[hist_df['Close'].argmin()]
        hist_df = apply_ema_signals(hist_df)
        signals = trade_signals(hist_df, base_price)

        # Plot
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=hist_df.index, y=hist_df['Close'], name='Close'))
        fig.add_trace(go.Scatter(x=hist_df.index, y=hist_df['EMA20'], name='EMA20'))
        fig.add_trace(go.Scatter(x=hist_df.index, y=hist_df['EMA50'], name='EMA50'))
        fig.update_layout(title=f"{symbol} - Price & EMA Chart", xaxis_title="Date", yaxis_title="Price")
        st.plotly_chart(fig)

        st.write("**📊 Trade Signals:**")
        st.json(signals)
    else:
        st.write("⏳ No U-shaped recovery detected.")
