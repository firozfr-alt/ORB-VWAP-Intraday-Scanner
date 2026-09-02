import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import pytz

# ==========================================
# 1. PAGE CONFIGURATION & STYLING
# ==========================================
st.set_page_config(
    page_title="Pro 5-Min ORB + RVOL Screener",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stDataFrame { border-radius: 8px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

st.title("⚡ Pro 5-Min ORB + VWAP + RVOL")
st.caption("Pure Price Action & Conviction: Scans for 5-Minute breakouts backed by massive Institutional Relative Volume (RVOL) and VWAP alignment.")

# ==========================================
# 2. WATCHLISTS & SIDEBAR CONTROLS
# ==========================================
WATCHLIST_PRESETS = {
    "Nifty 50 Core": [
        "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
        "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "KOTAKBANK.NS", "LT.NS",
        "AXISBANK.NS", "TATAMOTORS.NS", "MARUTI.NS", "SUNPHARMA.NS", "TITAN.NS",
        "BAJFINANCE.NS", "TATASTEEL.NS", "HINDUNILVR.NS", "NTPC.NS", "POWERGRID.NS"
    ],
    "High-Beta / F&O Momentum": [
        "TATAMOTORS.NS", "BAJFINANCE.NS", "ADANIENT.NS", "ADANIPORTS.NS",
        "HINDALCO.NS", "TATASTEEL.NS", "VEDL.NS", "DLF.NS", "INDUSINDBK.NS",
        "JINDALSTEL.NS", "CANBK.NS", "FEDERALBNK.NS", "MOTHERSON.NS", "ZEEL.NS"
    ],
    "Banking & Financials": [
        "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "KOTAKBANK.NS", "AXISBANK.NS",
        "INDUSINDBK.NS", "BANKBARODA.NS", "PNB.NS", "CANBK.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS"
    ]
}

st.sidebar.header("🎯 Strategy Settings")

selected_preset = st.sidebar.selectbox("Choose Universe", list(WATCHLIST_PRESETS.keys()) + ["Custom Symbols"])

if selected_preset == "Custom Symbols":
    custom_input = st.sidebar.text_area(
        "Enter NSE Symbols (comma-separated with .NS)",
        value="RELIANCE.NS, TCS.NS, HDFCBANK.NS, INFY.NS, TATAMOTORS.NS",
        height=100
    )
    symbols_to_scan = [s.strip().upper() for s in custom_input.split(",") if s.strip()]
else:
    symbols_to_scan = WATCHLIST_PRESETS[selected_preset]

st.sidebar.markdown("---")
st.sidebar.subheader("Filter Tuning")

# RVOL is typically higher than standard SMA volume. 1.5x means 150% of normal opening volume.
rvol_mult = st.sidebar.slider("Min RVOL (Relative Volume)", 1.0, 5.0, 1.5, 0.1)
st.sidebar.caption("Example: 2.0 means today's 9:15-9:20 volume is 200% higher than the 14-day average.")

auto_refresh = st.sidebar.checkbox("Enable Auto-Refresh (every 60s)", value=False)
if auto_refresh:
    st.sidebar.info("Auto-refresh active.")
    st.experimental_fragment(run_every=60)

# ==========================================
# 3. 5-MIN RVOL & VWAP ENGINE
# ==========================================
def analyze_stock(ticker_symbol: str):
    try:
        stock = yf.Ticker(ticker_symbol)
        # Pull 14 days of 5-minute data
        df = stock.history(period="14d", interval="5m")

        if df.empty or len(df) < 50:
            return None

        # Localize timezone to IST
        ist = pytz.timezone("Asia/Kolkata")
        if df.index.tz is None:
            df.index = df.index.tz_localize("UTC").tz_convert(ist)
        else:
            df.index = df.index.tz_convert(ist)

        # Extract the first 5-min candle (9:15-9:20) of EVERY day to find historical average
        first_candles = df.groupby(df.index.date).first()
        
        # Calculate the 14-day average volume for the 9:15 AM candle (excluding today)
        avg_opening_volume = first_candles['Volume'].iloc[:-1].mean()

        latest_date = df.index[-1].date()
        today_df = df[df.index.date == latest_date].copy()

        # Need at least the 9:15-9:20 candle to be completed (runs at 9:21 AM)
        if len(today_df) < 1:
            return {"error": "Waiting for 9:20 AM candle completion."}

        # 1. 5-Minute Opening Range (9:15-9:20)
        or_bar = today_df.iloc[0]
        or_high = float(or_bar["High"])
        or_low = float(or_bar["Low"])
        today_opening_vol = float(or_bar["Volume"])

        # 2. RVOL (Relative Volume) Calculation
        rvol = today_opening_vol / avg_opening_volume if avg_opening_volume > 0 else 1.0

        # 3. Daily Intraday VWAP
        today_df["TP"] = (today_df["High"] + today_df["Low"] + today_df["Close"]) / 3
        today_df["TPV"] = today_df["TP"] * today_df["Volume"]
        cum_tpv = today_df["TPV"].cumsum()
        cum_vol = today_df["Volume"].cumsum()
        today_df["VWAP"] = cum_tpv / cum_vol.replace(0, np.nan)

        latest_idx = today_df.index[-1]
        vwap_latest = float(today_df.loc[latest_idx, "VWAP"])
        latest = today_df.loc[latest_idx]

        ltp = float(latest["Close"])

        return {
            "Symbol": ticker_symbol.replace(".NS", ""),
            "LTP": round(ltp, 2),
            "OR_High": round(or_high, 2),
            "OR_Low": round(or_low, 2),
            "VWAP": round(vwap_latest, 2),
            "RVOL": round(rvol, 2)
        }
    except Exception:
        return None

# ==========================================
# 4. SCAN EXECUTION & RESULTS
# ==========================================
scan_col1, _ = st.columns([1, 4])
with scan_col1:
    trigger_scan = st.button("🚀 Run Live Scan Now", type="primary", use_container_width=True)

if trigger_scan or auto_refresh:
    buy_signals = []
    sell_signals = []
    neutral_list = []

    progress_bar = st.progress(0)
    status_msg = st.empty()

    for i, sym in enumerate(symbols_to_scan):
        status_msg.text(f"Scanning {sym} ({i+1}/{len(symbols_to_scan)})...")
        progress_bar.progress((i + 1) / len(symbols_to_scan))

        data = analyze_stock(sym)
        if not data or "error" in data:
            continue

        ltp = data["LTP"]
        or_h = data["OR_High"]
        or_l = data["OR_Low"]
        vwap = data["VWAP"]
        rvol = data["RVOL"]

        has_vol = rvol >= rvol_mult

        # --- OPTIMIZED 3-FILTER PURE PRICE ACTION LOGIC ---
        is_buy = (ltp > or_h) and (ltp > vwap) and has_vol
        is_sell = (ltp < or_l) and (ltp < vwap) and has_vol

        if is_buy:
            sl = or_l
            risk = round(ltp - sl, 2)
            buy_signals.append({
                "Stock": data["Symbol"],
                "LTP (₹)": ltp,
                "OR High": or_h,
                "Stop-Loss (₹)": sl,
                "Target (1.5R)": round(ltp + (1.5 * risk), 2),
                "VWAP": vwap,
                "RVOL": f"{rvol}x"
            })
        elif is_sell:
            sl = or_h
            risk = round(sl - ltp, 2)
            sell_signals.append({
                "Stock": data["Symbol"],
                "LTP (₹)": ltp,
                "OR Low": or_l,
                "Stop-Loss (₹)": sl,
                "Target (1.5R)": round(ltp - (1.5 * risk), 2),
                "VWAP": vwap,
                "RVOL": f"{rvol}x"
            })
        else:
            neutral_list.append({
                "Stock": data["Symbol"],
                "LTP": ltp,
                "OR High": or_h,
                "OR Low": or_l,
                "VWAP": vwap,
                "RVOL": f"{rvol}x"
            })

    status_msg.success(f"Scan finished at {datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%H:%M:%S')} IST")
    progress_bar.empty()

    # --- DISPLAY METRICS & TABLES ---
    m1, m2, m3 = st.columns(3)
    m1.metric("🟢 BUY Candidates", len(buy_signals))
    m2.metric("🔴 SELL Candidates", len(sell_signals))
    m3.metric("⚪ Neutral / In-Range", len(neutral_list))

    tab_buy, tab_sell, tab_all = st.tabs(["🟢 Long Breakouts (BUY)", "🔴 Short Breakdowns (SELL)", "📊 All Monitored Stocks"])

    with tab_buy:
        if buy_signals:
            # Sort by RVOL descending (highest volume conviction first)
            df_buy = pd.DataFrame(buy_signals).sort_values(by="RVOL", ascending=False)
            st.dataframe(df_buy, use_container_width=True)
            st.info("💡 **Execution:** Enter on pullback to VWAP. Stop loss at OR Low. Trail VWAP after 1R. Hard square-off by 3:15 PM.")
        else:
            st.write("No stocks currently satisfy bullish criteria.")

    with tab_sell:
        if sell_signals:
            df_sell = pd.DataFrame(sell_signals).sort_values(by="RVOL", ascending=False)
            st.dataframe(df_sell, use_container_width=True)
            st.info("💡 **Execution:** Enter on pullback to VWAP. Stop loss at OR High. Trail VWAP after 1R. Hard square-off by 3:15 PM.")
        else:
            st.write("No stocks currently satisfy bearish criteria.")

    with tab_all:
        if neutral_list:
            df_neutral = pd.DataFrame(neutral_list).sort_values(by="RVOL", ascending=False)
            st.dataframe(df_neutral, use_container_width=True)
