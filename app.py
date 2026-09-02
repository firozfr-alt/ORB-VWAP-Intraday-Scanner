import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import pytz
import ta

# ==========================================
# 1. PAGE CONFIGURATION & STYLING
# ==========================================
st.set_page_config(
    page_title="Pro Trading Screener (Intraday & Swing)",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stDataFrame { border-radius: 8px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

st.title("⚡ Pro Indian Equity Screener: Intraday & Swing")
st.caption("Multi-strategy institutional scanner featuring 5-Min Intraday ORB/RVOL and Daily Quantitative Multi-Factor Swing setups.")

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

st.sidebar.header("🎯 Master Settings")

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
st.sidebar.subheader("Intraday Tuning")
rvol_mult = st.sidebar.slider("Min 5-Min RVOL", 1.0, 5.0, 1.5, 0.1)
auto_refresh = st.sidebar.checkbox("Enable Auto-Refresh (every 60s)", value=False)
if auto_refresh:
    st.sidebar.info("Auto-refresh active.")
    st.fragment(run_every=60)

st.sidebar.markdown("---")
st.sidebar.subheader("Swing Tuning")
min_alpha = st.sidebar.slider("Min Swing Alpha Score", 0.8, 2.0, 1.2, 0.1)

# ==========================================
# 3. TECHNICAL ENGINES
# ==========================================
def analyze_intraday(ticker_symbol: str):
    try:
        stock = yf.Ticker(ticker_symbol)
        df = stock.history(period="14d", interval="5m")

        if df.empty or len(df) < 50:
            return None

        ist = pytz.timezone("Asia/Kolkata")
        if df.index.tz is None:
            df.index = df.index.tz_localize("UTC").tz_convert(ist)
        else:
            df.index = df.index.tz_convert(ist)

        first_candles = df.groupby(df.index.date).first()
        avg_opening_volume = first_candles['Volume'].iloc[:-1].mean()

        latest_date = df.index[-1].date()
        today_df = df[df.index.date == latest_date].copy()

        if len(today_df) < 1:
            return {"error": "Waiting for 9:20 AM candle completion."}

        or_bar = today_df.iloc[0]
        or_high = float(or_bar["High"])
        or_low = float(or_bar["Low"])
        today_opening_vol = float(or_bar["Volume"])

        rvol = today_opening_vol / avg_opening_volume if avg_opening_volume > 0 else 1.0

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

def analyze_swing_quant(ticker_symbol: str):
    try:
        stock = yf.Ticker(ticker_symbol)
        df = stock.history(period="1y", interval="1d")
        if df.empty or len(df) < 200: return None
        
        closes = df["Close"]
        log_ret = np.log(closes / closes.shift(1))
        vol_60 = log_ret.rolling(window=60).std() * np.sqrt(252)
        mom_score = np.log(closes / closes.shift(60)) / vol_60
        
        sma_50 = closes.rolling(window=50).mean()
        vol_50 = closes.rolling(window=50).std()
        z_price = (closes - sma_50) / vol_50
        
        vol_sma_20 = df["Volume"].rolling(window=20).mean()
        rvol_20 = ((df["Volume"].shift(1) + df["Volume"].shift(2) + df["Volume"].shift(3)) / 3) / vol_sma_20
        
        alpha_score = 0.4 * mom_score + 0.3 * (z_price / 2.0) + 0.3 * rvol_20
        
        latest_idx = -1
        ltp = float(closes.iloc[latest_idx])
        alpha = float(alpha_score.iloc[latest_idx])
        z_val = float(z_price.iloc[latest_idx])
        rvol_val = float(rvol_20.iloc[latest_idx])
        
        atr = float(ta.volatility.average_true_range(df["High"], df["Low"], df["Close"], window=14).iloc[-1])
        is_setup = (alpha >= min_alpha) and (0.5 <= z_val <= 2.0) and (rvol_val >= 1.2)
        
        return {
            "Symbol": ticker_symbol.replace(".NS", ""),
            "LTP": round(ltp, 2),
            "Alpha Score": round(alpha, 2),
            "Z-Score": round(z_val, 2),
            "RVOL_20": round(rvol_val, 2),
            "ATR": round(atr, 2),
            "Is_Setup": is_setup
        }
    except: return None

# ==========================================
# 4. TABBED LAYOUT STRUCTURE
# ==========================================
tab_intraday, tab_swing = st.tabs(["⚡ Intraday 5-Min ORB + RVOL", "📈 Quant Multi-Factor Swing"])

# --- TAB 1: ORIGINAL INTRADAY DASHBOARD ---
with tab_intraday:
    st.subheader("⚡ Intraday 5-Min ORB + VWAP + RVOL")
    st.caption("Pure Price Action & Conviction: Scans for 5-Minute breakouts backed by massive Institutional Relative Volume (RVOL) and VWAP alignment.")

    scan_col1, _ = st.columns([1, 4])
    with scan_col1:
        trigger_scan = st.button("🚀 Run Live Intraday Scan", type="primary", use_container_width=True)

    if trigger_scan or auto_refresh:
        buy_signals = []
        sell_signals = []
        neutral_list = []

        progress_bar = st.progress(0)
        status_msg = st.empty()

        for i, sym in enumerate(symbols_to_scan):
            status_msg.text(f"Scanning {sym} ({i+1}/{len(symbols_to_scan)})...")
            progress_bar.progress((i + 1) / len(symbols_to_scan))

            data = analyze_intraday(sym)
            if not data or "error" in data:
                continue

            ltp = data["LTP"]
            or_h = data["OR_High"]
            or_l = data["OR_Low"]
            vwap = data["VWAP"]
            rvol = data["RVOL"]

            has_vol = rvol >= rvol_mult

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

        m1, m2, m3 = st.columns(3)
        m1.metric("🟢 BUY Candidates", len(buy_signals))
        m2.metric("🔴 SELL Candidates", len(sell_signals))
        m3.metric("⚪ Neutral / In-Range", len(neutral_list))

        tab_b, tab_s, tab_a = st.tabs(["🟢 Long Breakouts (BUY)", "🔴 Short Breakdowns (SELL)", "📊 All Monitored Stocks"])

        with tab_b:
            if buy_signals:
                df_buy = pd.DataFrame(buy_signals).sort_values(by="RVOL", ascending=False)
                st.dataframe(df_buy, use_container_width=True)
                st.info("💡 **Execution:** Enter on pullback to VWAP. Stop loss at OR Low. Trail VWAP after 1R. Hard square-off by 3:15 PM.")
            else:
                st.write("No stocks currently satisfy bullish criteria.")

        with tab_s:
            if sell_signals:
                df_sell = pd.DataFrame(sell_signals).sort_values(by="RVOL", ascending=False)
                st.dataframe(df_sell, use_container_width=True)
                st.info("💡 **Execution:** Enter on pullback to VWAP. Stop loss at OR High. Trail VWAP after 1R. Hard square-off by 3:15 PM.")
            else:
                st.write("No stocks currently satisfy bearish criteria.")

        with tab_a:
            if neutral_list:
                df_neutral = pd.DataFrame(neutral_list).sort_values(by="RVOL", ascending=False)
                st.dataframe(df_neutral, use_container_width=True)

# --- TAB 2: NEW QUANTITATIVE SWING DASHBOARD ---
with tab_swing:
    st.subheader("📈 Quantitative Multi-Factor Swing Scanner")
    st.caption("Advanced quant model evaluating 60-day volatility-adjusted momentum, 50-day statistical Z-scores, and 20-day institutional RVOL accumulation.")
    
    if st.button("🚀 Run Quant Swing Scan", type="primary"):
        swing_candidates = []
        bar_s = st.progress(0)

        for i, sym in enumerate(symbols_to_scan):
            bar_s.progress((i + 1) / len(symbols_to_scan))
            s_data = analyze_swing_quant(sym)
            if s_data and s_data["Is_Setup"]:
                ltp, atr = s_data["LTP"], s_data["ATR"]
                swing_candidates.append({
                    "Stock": s_data["Symbol"], 
                    "LTP (₹)": ltp, 
                    "Alpha Score": s_data["Alpha Score"], 
                    "Z-Score": s_data["Z-Score"],
                    "RVOL (20d)": f"{s_data['RVOL_20']}x", 
                    "Stop-Loss": round(ltp - (2.0 * atr), 2), 
                    "Target": round(ltp + (3.0 * atr), 2)
                })
        bar_s.empty()

        if swing_candidates:
            df_swing = pd.DataFrame(swing_candidates).sort_values(by="Alpha Score", ascending=False)
            st.dataframe(df_swing, use_container_width=True)
            st.info("💡 **Swing Execution Rule:** Hold positions for 3 to 15 days. Trail your stop-loss along the rising 20-day or 50-day moving average once the trade moves in your favor.")
        else:
            st.write("No swing setups match current quantitative alpha criteria.")
