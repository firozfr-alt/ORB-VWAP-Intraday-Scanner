import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf
from xgboost import XGBClassifier

st.title("⚡ Institutional Multi-Strategy Platform")
st.sidebar.header("Configuration")

ticker = st.sidebar.text_input("Enter NSE Ticker", value="RELIANCE.NS")
strategy_type = st.sidebar.selectbox(
    "Select Strategy", ["Intraday 5m/15m ORB", "Swing Trading Daily"]
)

if st.sidebar.button("Run Analysis"):
  st.write(f"Running analysis for {ticker}...")

  if strategy_type == "Intraday 5m/15m ORB":
    df = yf.download(ticker, interval="5m", period="5d")
    st.subheader("Intraday Data Feed")
    st.dataframe(df.tail())
  else:
    df = yf.download(ticker, interval="1d", period="6mo")
    st.subheader("Swing Trading Daily Data Feed")
    st.dataframe(df.tail())
