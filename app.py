import streamlit as st
import pandas as pd
from trigger import get_price_data, analyze_triggers

# --- Page setup ---
st.set_page_config(layout="wide", page_title="IPO Swing Trader & Simulator")
st.title("📈 IPO Tools: Triggers & Trade Simulator")

# --- Tab Layout ---
tab1, tab2 = st.tabs(["🚀 Trigger Analysis", "💰 Trade Simulator"])

# --- Trigger Tab ---
with tab1:
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

    st.subheader("📋 IPO List")
    st.dataframe(df[['Stock Name', 'Symbol', '% Chg', 'Price', 'Volume']])

    if st.button("🚀 Run Trigger Analysis"):
        results = []
        for symbol in df['Symbol']:
            ticker = symbol + ".NS"
            price_df = get_price_data(ticker)
            if price_df is None or len(price_df) < 20:
                continue
            triggers = analyze_triggers(price_df)
            if triggers:
                results.append({
                    "Stock": symbol,
                    **triggers
                })

        if results:
            st.subheader("📊 Trigger Summary Table")
            st.dataframe(pd.DataFrame(results))
        else:
            st.info("⚠️ No triggers identified.")

# --- Trade Simulator Tab ---
with tab2:
    st.subheader("💰 IPO Trade Simulator")

    ticker = st.selectbox("Choose a stock (NSE):", options=[
        "ACMESOLAR.NS", "AFCONS.NS", "RELIANCE.NS", "MOBIKWIK.NS", "ITCHOTELS.NS"
    ])

    investment = st.number_input("Enter investment amount (₹)", value=10000, step=500)

    df = get_price_data(ticker)

    if df is None:
        st.error("No data found.")
    else:
        listing_date = df.index.min()
        base_price = df.loc[listing_date, 'High']
        ltp = df['Close'].iloc[-1]

        df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
        df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()

        dip_threshold = base_price * 0.95
        dips = df[df['Low'] < dip_threshold]

        u_curve_detected = False
        cross_idx = None
        percent_dip = "-"
        sessions_to_u_curve = "-"
        buying_date = "-"
        buy_price = None

        if not dips.empty:
            min_low = dips['Low'].min()
            percent_dip = round((min_low - base_price) / base_price * 100, 2)
            dip_idx = dips['Low'].idxmin()
            after_dip = df.loc[dip_idx:]
            cross = after_dip[after_dip['Close'] > base_price]
            if not cross.empty:
                cross_idx = cross.index.min()
                buying_date = cross_idx.strftime('%Y-%m-%d')
                sessions_to_u_curve = df.index.get_loc(cross_idx) - df.index.get_loc(dip_idx)
                u_curve_detected = True
                buy_price = df.loc[cross_idx]['Close']

        buy_signal = u_curve_detected and ltp > base_price

        sell_30_price, sell_all_price = None, None
        sell_30_date, sell_all_date = "-", "-"
        shares_bought = investment / buy_price if buy_price else 0
        total_return = 0
        remaining_shares = shares_bought

        if buy_signal:
            post_buy_df = df.loc[cross_idx:]
            for i, row in post_buy_df.iterrows():
                if sell_30_price is None and row['Close'] < row['EMA20']:
                    sell_30_price = row['Close']
                    sell_30_date = i.strftime('%Y-%m-%d')
                if sell_all_price is None and row['Close'] < row['EMA50']:
                    sell_all_price = row['Close']
                    sell_all_date = i.strftime('%Y-%m-%d')
                if sell_30_price and sell_all_price:
                    break

        # Return Calculation
        if buy_price:
            if sell_30_price:
                qty = 0.3 * shares_bought
                total_return += qty * sell_30_price
                remaining_shares -= qty
            if sell_all_price:
                total_return += remaining_shares * sell_all_price
                remaining_shares = 0
            if remaining_shares > 0:
                total_return += remaining_shares * ltp

        final_upside = ((total_return - investment) / investment * 100) if buy_price else "-"

        # Summary Table
        st.markdown("### 💹 Trade Summary")
        summary = {
            "Listing Date": listing_date.strftime('%Y-%m-%d'),
            "Listing Price (High)": round(base_price, 2),
            "U-Curve": "✅" if u_curve_detected else "❌",
            "Dip %": percent_dip,
            "# Sessions to U-Curve": sessions_to_u_curve,
            "BUY": "✅" if buy_signal else "❌",
            "Buying Date": buying_date,
            "Buy Price": round(buy_price, 2) if buy_price else "-",
            "Sell 30% (EMA20)": "✅" if sell_30_price else "❌",
            "Selling Price (30%)": round(sell_30_price, 2) if sell_30_price else "-",
            "Selling Date (30%)": sell_30_date,
            "Sell All (EMA50)": "✅" if sell_all_price else "❌",
            "Selling Price (All)": round(sell_all_price, 2) if sell_all_price else "-",
            "Selling Date (All)": sell_all_date,
            "% Upside": round(final_upside, 2) if isinstance(final_upside, float) else "-"
        }

        st.dataframe(pd.DataFrame([summary]).T.rename(columns={0: "Value"}))
