import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import pytz
import ta

st.set_page_config(page_title="Pro Quant Screener", page_icon="⚡", layout="wide")

WATCHLIST_PRESETS = {
    "Nifty 50 Core": ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "KOTAKBANK.NS", "LT.NS", "AXISBANK.NS", "TATAMOTORS.NS", "MARUTI.NS", "SUNPHARMA.NS", "TITAN.NS", "BAJFINANCE.NS", "TATASTEEL.NS", "HINDUNILVR.NS", "NTPC.NS", "POWERGRID.NS"],
    "High-Beta / F&O": ["TATAMOTORS.NS", "BAJFINANCE.NS", "ADANIENT.NS", "ADANIPORTS.NS", "HINDALCO.NS", "TATASTEEL.NS", "VEDL.NS", "DLF.NS", "INDUSINDBK.NS", "JINDALSTEL.NS"]
}

st.sidebar.header("Quantitative Controls")
selected_preset = st.sidebar.selectbox("Choose Universe", list(WATCHLIST_PRESETS.keys()))
symbols_to_scan = WATCHLIST_PRESETS[selected_preset]

rvol_mult = st.sidebar.slider("Min 5-Min RVOL (Intraday)", 1.0, 5.0, 1.5, 0.1)
min_alpha = st.sidebar.slider("Min Swing Alpha Score", 0.8, 2.0, 1.2, 0.1)

def analyze_intraday(ticker_symbol):
    try:
        stock = yf.Ticker(ticker_symbol)
        df = stock.history(period="14d", interval="5m")
        if df.empty or len(df) < 50: return None
        ist = pytz.timezone("Asia/Kolkata")
        df.index = df.index.tz_convert(ist) if df.index.tz else df.index.tz_localize("UTC").tz_convert(ist)
        first_candles = df.groupby(df.index.date).first()
        avg_opening_volume = first_candles['Volume'].iloc[:-1].mean()
        today_df = df[df.index.date == df.index[-1].date()].copy()
        if len(today_df) < 1: return None
        or_bar = today_df.iloc[0]
        rvol = float(or_bar["Volume"]) / avg_opening_volume if avg_opening_volume > 0 else 1.0
        today_df["TP"] = (today_df["High"] + today_df["Low"] + today_df["Close"]) / 3
        today_df["VWAP"] = (today_df["TP"] * today_df["Volume"]).cumsum() / today_df["Volume"].cumsum()
        latest = today_df.iloc[-1]
        return {"Symbol": ticker_symbol.replace(".NS", ""), "LTP": round(float(latest["Close"]), 2), "OR_High": float(or_bar["High"]), "OR_Low": float(or_bar["Low"]), "VWAP": round(float(latest["VWAP"]), 2), "RVOL": round(rvol, 2)}
    except: return None

def analyze_swing_quant(ticker_symbol):
    try:
        stock = yf.Ticker(ticker_symbol)
        df = stock.history(period="1y", interval="1d")
        if df.empty or len(df) < 200: return None
        
        # Factor Calculations
        closes = df["Close"]
        # 1. 60-day Volatility-Adjusted Momentum Score
        log_ret = np.log(closes / closes.shift(1))
        vol_60 = log_ret.rolling(window=60).std() * np.sqrt(252)
        mom_score = np.log(closes / closes.shift(60)) / vol_60
        
        # 2. Statistical Z-Score from 50-day SMA
        sma_50 = closes.rolling(window=50).mean()
        vol_50 = closes.rolling(window=50).std()
        z_price = (closes - sma_50) / vol_50
        
        # 3. Short-term Volume Accumulation (RVOL_20)
        vol_sma_20 = df["Volume"].rolling(window=20).mean()
        rvol_20 = ((df["Volume"].shift(1) + df["Volume"].shift(2) + df["Volume"].shift(3)) / 3) / vol_sma_20
        
        # 4. Composite Alpha Score Matrix
        alpha_score = 0.4 * mom_score + 0.3 * (z_price / 2.0) + 0.3 * rvol_20
        
        latest_idx = -1
        ltp = float(closes.iloc[latest_idx])
        alpha = float(alpha_score.iloc[latest_idx])
        z_val = float(z_price.iloc[latest_idx])
        rvol_val = float(rvol_20.iloc[latest_idx])
        
        atr = float(ta.volatility.average_true_range(df["High"], df["Low"], df["Close"], window=14).iloc[-1])
        
        # Filtering criteria: Positive alpha meeting threshold & healthy Z-score range
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

tab_intraday, tab_swing = st.tabs(["⚡ Intraday 5-Min ORB + RVOL", "📈 Quant Multi-Factor Swing"])

with tab_intraday:
    st.subheader("Intraday Live Scanner")
    if st.button("Run Intraday Scan", type="primary"):
        buy_signals, sell_signals = [], []
        for sym in symbols_to_scan:
            data = analyze_intraday(sym)
            if not data: continue
            if (data["LTP"] > data["OR_High"]) and (data["LTP"] > data["VWAP"]) and (data["RVOL"] >= rvol_mult):
                risk = round(data["LTP"] - data["OR_Low"], 2)
                buy_signals.append({"Stock": data["Symbol"], "LTP (₹)": data["LTP"], "Stop-Loss": data["OR_Low"], "Target": round(data["LTP"] + (1.5*risk), 2), "RVOL": f"{data['RVOL']}x"})
            elif (data["LTP"] < data["OR_Low"]) and (data["LTP"] < data["VWAP"]) and (data["RVOL"] >= rvol_mult):
                risk = round(data["OR_High"] - data["LTP"], 2)
                sell_signals.append({"Stock": data["Symbol"], "LTP (₹)": data["LTP"], "Stop-Loss": data["OR_High"], "Target": round(data["LTP"] - (1.5*risk), 2), "RVOL": f"{data['RVOL']}x"})
        col1, col2 = st.columns(2)
        with col1: st.dataframe(pd.DataFrame(buy_signals) if buy_signals else pd.DataFrame([{"Status": "No Longs"}]), use_container_width=True)
        with col2: st.dataframe(pd.DataFrame(sell_signals) if sell_signals else pd.DataFrame([{"Status": "No Shorts"}]), use_container_width=True)

with tab_swing:
    st.subheader("Quantitative Multi-Factor Swing Scanner")
    if st.button("Run Quant Swing Scan", type="primary"):
        swing_candidates = []
        for sym in symbols_to_scan:
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
        if swing_candidates:
            st.dataframe(pd.DataFrame(swing_candidates).sort_values(by="Alpha Score", ascending=False), use_container_width=True)
        else:
            st.write("No swing setups match current quantitative alpha criteria.")
