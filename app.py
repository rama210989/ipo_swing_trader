import streamlit as st
import pandas as pd
from trigger import get_price_data, analyze_triggers
from extract_data import get_combined_ipo_data

# --- Page setup ---
st.set_page_config(layout="wide", page_title="IPO Swing Trader & Simulator")
st.title("📈 IPO Tools: Triggers & Trade Simulator")

# --- Tab Layout ---
tab1, tab2 = st.tabs(["🚀 Trigger Analysis", "💰 Trade Simulator"])

# --- Trigger Tab ---
with tab1:
    st.markdown("*Data from Chittorgarh*")

    # Cache IPO data and support manual refresh
    @st.cache_data(ttl=3600, show_spinner="Fetching IPO data...")
    def load_ipo_data():
        return get_combined_ipo_data()

    if st.button("🔁 Refresh IPO List (Manually)"):
        st.cache_data.clear()
        st.success("IPO list refreshed. Click 'Run Trigger Analysis' again.")

    ipo_df = load_ipo_data()

    st.subheader("📋 IPO List (Chittorgarh)")
    st.markdown(f"Total IPOs shown: **{len(ipo_df)}**")
    if not ipo_df.empty:
        latest_date = ipo_df['Opening Date'].max()
        if pd.notnull(latest_date):
            st.markdown(f"Latest IPO Opening Date: **{latest_date.strftime('%Y-%m-%d')}**")
    st.dataframe(ipo_df[[
        "Company Name", "Opening Date", "Listing Date", "Issue Price (Rs.)",
        "Issue Amount (Rs.cr.)", "Listing at", "FY"
    ]])

    if st.button("🚀 Run Trigger Analysis"):
        results = []
        for idx, row in ipo_df.iterrows():
            symbol = row["Company Name"].split()[0].upper().replace("&", "").replace(".", "")
            ticker = symbol + ".NS"
            price_df = get_price_data(ticker)
            if price_df is None or len(price_df) < 20:
                continue
            triggers = analyze_triggers(price_df)
            if triggers:
                triggers["Stock Name"] = row["Company Name"]
                results.append(triggers)

        if results:
            st.subheader("📊 Trigger Summary Table")
            res_df = pd.DataFrame(results)

            # Put "Stock Name" as first column
            cols = res_df.columns.tolist()
            if "Stock Name" in cols:
                cols.insert(0, cols.pop(cols.index("Stock Name")))
                res_df = res_df[cols]

            res_df = res_df.rename(columns={
                "% Dip": "% Dip from Base Price",
                "Max Upside (%)": "Max Upside (%)",
                "Sessions to Max Upside": "Sessions to Max Upside",
                "# Sessions U-Curve": "Sessions in U-Curve",
                "Price at Sold 30%": "Price at Sold 30%",
                "Price at Sold All": "Price at Sold All",
                "% Upside Selling 30%": "% Upside Selling 30%",
                "% Upside Selling All": "% Upside Selling All"
            })

            st.dataframe(res_df)

            st.markdown("""
            ### 📖 Explanation of Columns:
            - **Stock Name:** Company name of the IPO stock
            - **Listing Price:** IPO day 1 high price (base)
            - **Listing Date:** Date of IPO listing (first trading day)
            - **LTP:** Last traded price
            - **U-curve:** Price dipped 5% below base and then recovered above base
            - **Sessions in U-Curve:** Number of sessions to complete U-curve
            - **% Dip from Base Price:** Max % dip below listing price
            - **BUY:** Signal when price crossed above base after dip
            - **Buying Date:** Date when buy signal triggered
            - **EMA 20 / EMA 50:** Exponential moving averages
            - **Max Upside (%):** Max % increase from base price
            - **Sessions to Max Upside:** Sessions taken to reach max price
            - **Sell 30 %:** Signal triggered when price drops below EMA20 after buy
            - **Price at Sold 30%:** Price when selling 30%
            - **Sell all:** Signal triggered when price drops below EMA50 after buy
            - **Price at Sold All:** Price when selling all shares
            - **% Upside Selling 30% / All:** % returns at sell points
            """)
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
