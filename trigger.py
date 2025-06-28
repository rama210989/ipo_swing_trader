import pandas as pd
def analyze_triggers(df):
    try:
        required_cols = ['Open', 'Close', 'Low']
        if not all(col in df.columns for col in required_cols):
            print(f"❌ Required columns missing: {df.columns}")
            return None

        if len(df) < 20:  # Need at least 50 for EMA 50 but we can adjust
            print("❌ Not enough data for analysis")
            return None

        base_price = df['Open'].iloc[0]  # Listing Price
        ltp = df['Close'].iloc[-1]  # Last traded price

        # Calculate EMA20 and EMA50
        df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
        df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()

        # Find the lowest price dip below base price by at least 5%
        dip_threshold = base_price * 0.95
        dips = df[df['Low'] < dip_threshold]

        # Check if U-curve formed:
        # 1) Price dipped at least 5% below base price
        # 2) Then price crossed back above base price (Close > base_price)
        u_curve_detected = False
        sessions_to_u_curve = None
        percent_dip = None

        if not dips.empty:
            min_low = dips['Low'].min()
            percent_dip = round((min_low - base_price) / base_price * 100, 2)

            # Find session of min dip and first session after dip crossing base price
            dip_idx = dips['Low'].idxmin()
            # Find first Close > base_price after dip_idx
            after_dip = df.loc[dip_idx:]
            cross_idx = after_dip[after_dip['Close'] > base_price].index.min()

            if pd.notna(cross_idx):
                u_curve_detected = True
                sessions_to_u_curve = (cross_idx - df.index[0]).days if isinstance(cross_idx, pd.Timestamp) else cross_idx - dip_idx

        buy_signal = u_curve_detected and (ltp > base_price)

        # SELL logic after buy:
        # If bought (buy_signal == True)
        # SELL 30% profit if price goes below EMA20 after buy
        # SELL all if price goes below EMA50
        sell_signal = False
        sell_all_signal = False
        if buy_signal:
            if ltp < df['EMA20'].iloc[-1]:
                sell_signal = True
            if ltp < df['EMA50'].iloc[-1]:
                sell_all_signal = True

        return {
            "Listing Price": round(base_price, 2),
            "LTP": round(ltp, 2),
            "U-Curve": "✅" if u_curve_detected else "❌",
            "# Sessions U-Curve": sessions_to_u_curve if sessions_to_u_curve is not None else "-",
            "% Dip": percent_dip if percent_dip is not None else "-",
            "BUY": "✅" if buy_signal else "❌",
            "EMA20": round(df['EMA20'].iloc[-1], 2),
            "EMA50": round(df['EMA50'].iloc[-1], 2),
            "SELL 30% Profit": "✅" if sell_signal else "❌",
            "SELL All": "✅" if sell_all_signal else "❌"
        }

    except Exception as e:
        print(f"⚠️ Trigger analysis failed: {e}")
        return None
