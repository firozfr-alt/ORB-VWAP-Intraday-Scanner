import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import pytz
import ta

st.set_page_config(page_title="Pro Trading Screener", page_icon="⚡", layout="wide")

WATCHLIST_PRESETS = {
    "Nifty 50 Core": ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "KOTAKBANK.NS", "LT.NS", "AXISBANK.NS", "TATAMOTORS.NS", "MARUTI.NS", "SUNPHARMA.NS", "TITAN.NS", "BAJFINANCE.NS", "TATASTEEL.NS", "HINDUNILVR.NS", "NTPC.NS", "POWERGRID.NS"],
    "High-Beta / F&O": ["TATAMOTORS.NS", "BAJFINANCE.NS", "ADANIENT.NS", "ADANIPORTS.NS", "HINDALCO.NS", "TATASTEEL.NS", "VEDL.NS", "DLF.NS", "INDUSINDBK.NS", "JINDALSTEL.NS"]
}

st.sidebar.header("Master Settings")
selected_preset = st.sidebar.selectbox("Choose Universe", list(WATCHLIST_PRESETS.keys()))
symbols_to_scan = WATCHLIST_PRESETS[selected_preset]

rvol_mult = st.sidebar.slider("Min 5-Min RVOL (Intraday)", 1.0, 5.0, 1.5, 0.1)
swing_vol_mult = st.sidebar.slider("Min Daily Volume Surge (Swing)", 1.0, 3.0, 1.3, 0.1)

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

def analyze_swing(ticker_symbol):
    try:
        stock = yf.Ticker(ticker_symbol)
        df = stock.history(period="1y", interval="1d")
        if df.empty or len(df) < 200: return None
        df["SMA_50"] = df["Close"].rolling(window=50).mean()
        df["SMA_200"] = df["Close"].rolling(window=200).mean()
        df["VOL_SMA_20"] = df["Volume"].rolling(window=20).mean()
        df["RSI_14"] = ta.momentum.rsi(df["Close"], window=14)
        df["ATR_14"] = ta.volatility.average_true_range(df["High"], df["Low"], df["Close"], window=14)
        latest = df.iloc[-1]
        ltp, sma50, sma200, rsi, vol, vol_avg, atr = float(latest["Close"]), float(latest["SMA_50"]), float(latest["SMA_200"]), float(latest["RSI_14"]), float(latest["Volume"]), float(latest["VOL_SMA_20"]), float(latest["ATR_14"])
        vol_ratio = vol / vol_avg if vol_avg > 0 else 1.0
        is_setup = (ltp > sma50) and (sma50 > sma200) and (55 <= rsi <= 75) and (vol_ratio >= swing_vol_mult)
        return {"Symbol": ticker_symbol.replace(".NS", ""), "LTP": round(ltp, 2), "RSI": round(rsi, 1), "Vol Ratio": round(vol_ratio, 2), "ATR": round(atr, 2), "Is_Setup": is_setup, "SMA_50": round(sma50, 2), "SMA_200": round(sma200, 2)}
    except: return None

tab_intraday, tab_swing = st.tabs(["⚡ Intraday 5-Min ORB + RVOL", "📈 Daily Swing Trend Momentum"])

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
    st.subheader("Daily Swing Momentum Scanner")
    if st.button("Run Swing Scan", type="primary"):
        swing_candidates = []
        for sym in symbols_to_scan:
            s_data = analyze_swing(sym)
            if s_data and s_data["Is_Setup"]:
                ltp, atr = s_data["LTP"], s_data["ATR"]
                swing_candidates.append({"Stock": s_data["Symbol"], "LTP (₹)": ltp, "RSI": s_data["RSI"], "Vol Surge": f"{s_data['Vol Ratio']}x", "Stop-Loss": round(ltp - (2.0 * atr), 2), "Target": round(ltp + (3.0 * atr), 2)})
        if swing_candidates:
            st.dataframe(pd.DataFrame(swing_candidates).sort_values(by="RSI", ascending=False), use_container_width=True)
        else:
            st.write("No swing setups match current criteria.")
