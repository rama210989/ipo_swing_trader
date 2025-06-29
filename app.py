# app.py

import streamlit as st
import pandas as pd
from trigger import get_price_data, run_trigger_analysis
from extract_data import get_combined_ipo_data

# --- Page setup ---
st.set_page_config(layout="wide", page_title="IPO Swing Trader")
st.title("📈 IPO Tools: Trigger Monitor")

# --- Tab Layout ---
tab1, tab2 = st.tabs(["🚀 IPO LTP Summary", "💰 Trade Simulator (Coming Soon)"])

# --- Trigger Tab ---
with tab1:
    st.markdown("*Data Source: Chittorgarh + Yahoo Finance*")

    @st.cache_data(ttl=3600, show_spinner="Fetching IPO data...")
    def load_ipo_data():
        return get_combined_ipo_data()

    if st.button("🔁 Refresh IPO List"):
        st.cache_data.clear()
        st.success("IPO list refreshed. Click 'Run Trigger Analysis' again.")

    ipo_df = load_ipo_data()

    st.subheader("📋 IPO List (from Chittorgarh)")
    st.markdown(f"Total IPOs: **{len(ipo_df)}**")

    if not ipo_df.empty:
        latest_date = ipo_df['Opening Date'].max()
        if pd.notnull(latest_date):
            st.markdown(f"Latest IPO Opening Date: **{latest_date.strftime('%Y-%m-%d')}**")

    # Show enriched IPO data
    st.dataframe(ipo_df[[
        "Company Name", "Symbol", "Opening Date", "Listing Date", "Issue Price (Rs.)"
    ]].sort_values("Opening Date", ascending=False), use_container_width=True)

    # Trigger analysis
    if st.button("🚀 Run Trigger Analysis"):
        with st.spinner("Getting LTPs, please wait..."):
            trigger_results = run_trigger_analysis(ipo_df)

        if not trigger_results.empty:
            display_cols = [
                "Stock Name", "Listing Date", "Listing Price", "LTP",
                "U-curve", "# sessions in u-curve", "% dip from LTP",
                "BUY", "Buying Date", "EMA 20", "EMA 50",
                "Max upside (%)", "# sessions to max",
                "Sell 30 %", "Price"
            ]

            trigger_results = trigger_results[display_cols]

            st.subheader("📊 IPO LTP Summary Table")
            st.dataframe(trigger_results, use_container_width=True)

            st.markdown("""
            ### 🧾 Column Descriptions:
            - **Stock Name:** Company name from IPO list  
            - **Listing Date:** Date the stock listed  
            - **Listing Price:** Issue price from IPO  
            - **LTP:** Current/Last traded price from Yahoo Finance  
            - **U-curve:** Whether the price has formed a U-curve  
            - **% dip from LTP:** Dip from peak before recovery  
            - **EMA 20/50:** Technical indicators for trend  
            - **Max upside (%):** % increase from listing price  
            - **Sell 30 % Price:** Ideal target for 30% gains  
            """)
        else:
            st.info("⚠️ No IPOs with valid listing date or stock data found.")

# --- Trade Simulator Tab (Placeholder) ---
with tab2:
    st.subheader("💰 Trade Simulator")
    st.info("🚧 Coming soon: Simulate swing trades after trigger confirmation.")
