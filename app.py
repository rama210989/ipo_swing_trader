import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objs as go
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
st.dataframe(filtered_df)

# Analysis section
st.markdown("---")
st.header("📊 U-Shape Recovery & EMA Signals (Steps 2–4)")

def get_price_data(ticker, days=90):
    since = datetime.today() - timedelta(days=days)
    df = yf.download(ticker + ".NS", start=since.strftime("%Y-%m-%d"))
    return df if not df.empty else None

def detect_u_curve_and_signals(df):
    # Check for minimum data length and columns
    if len(df) < 30 or 'Open' not in df.columns or 'Low' not in df.columns or 'Close' not in df.columns:
        return None  # Not enough data or required columns

    # Base price = Opening price on first available day (convert to float)
    base_price = float(df['Open'].iloc[0])

    # Minimum low price after IPO day (float)
    min_low = float(df['Low'].min())

    # % dip from base price
    dip_pct = (base_price - min_low) / base_price * 100

    # Did U-curve dip >= 10% happen?
    u_curve_formed = dip_pct >= 10

    # Last close price (float)
    last_close = float(df['Close'].iloc[-1])

    # Calculate EMAs
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()

    # Buy trigger: price crosses above base price after dip
    buy_signal = u_curve_formed and (last_close > base_price)

    # Sell signals
    sell_30 = last_close < df['EMA20'].iloc[-1]  # below EMA20
    sell_all = last_close < df['EMA50'].iloc[-1]  # below EMA50

    return {
        "base_price": base_price,
        "min_low": min_low,
        "dip_pct": dip_pct,
        "u_curve_formed": u_curve_formed,
        "last_close": last_close,
        "buy_signal": buy_signal,
        "sell_30": sell_30,
        "sell_all": sell_all,
        "df": df  # return df with EMAs for plotting
    }

for symbol in filtered_df['Symbol'].unique():
    st.markdown(f"#### {symbol}")
    hist_df = get_price_data(symbol)

    if hist_df is None or len(hist_df) < 30:
        st.write("⚠️ Not enough historical data.")
        continue

    signals = detect_u_curve_and_signals(hist_df)
    if signals is None:
        st.write("⚠️ Data insufficient for analysis.")
        continue

    st.write(f"Base Price (IPO Open): ₹{signals['base_price']:.2f}")
    st.write(f"Lowest Price since IPO: ₹{signals['min_low']:.2f}")
    st.write(f"Max Dip from Base Price: {signals['dip_pct']:.2f}%")

    if not signals['u_curve_formed']:
        st.write("⏳ No U-curve dip of at least 10% detected yet.")
        continue

    st.write(f"Last Close Price: ₹{signals['last_close']:.2f}")

    # Buy condition
    if signals['buy_signal']:
        st.success("✅ BUY signal: Price crossed above IPO listing price after U-curve dip.")
    else:
        st.info("ℹ️ Waiting for price to cross back above IPO listing price for BUY trigger.")

    # Sell conditions
    if signals['sell_all']:
        st.warning("🚪 SELL ALL signal: Price below EMA50.")
    elif signals['sell_30']:
        st.warning("🔁 SELL 30% signal: Price below EMA20.")
    else:
        st.info("📈 Hold: Price above EMA20 and EMA50.")

    # Plot price chart with EMAs and base price line
    df = signals['df']
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name='Close Price'))
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA20'], name='EMA20'))
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA50'], name='EMA50'))
    fig.add_trace(go.Scatter(
        x=df.index, 
        y=[signals['base_price']] * len(df), 
        name='Base Price (IPO Open)', 
        line=dict(dash='dash')
    ))
    fig.update_layout(
        title=f"{symbol} Price Chart with EMA & Base Price", 
        xaxis_title="Date", 
        yaxis_title="Price (₹)"
    )
    st.plotly_chart(fig)
