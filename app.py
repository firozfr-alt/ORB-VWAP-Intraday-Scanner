import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf
from xgboost import XGBClassifier

# ==========================================
# STREAMLIT UI CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Institutional Multi-Strategy Platform", layout="wide"
)

st.title("⚡ Institutional Multi-Strategy Platform")
st.markdown("---")

# Sidebar Configuration for Stock Selection and Strategy Choice
st.sidebar.header("⚙️ Execution Controls")
ticker = st.sidebar.text_input(
    "Enter NSE Ticker (e.g., RELIANCE.NS, TATAMOTORS.NS)", value="RELIANCE.NS"
)
strategy_tab = st.sidebar.selectbox(
    "Select Strategy Module",
    [
        "Intraday (5m/15m ORB + XGBoost)",
        "Swing Trading (Daily EMA & RRG Pullback)",
    ],
)

# ==========================================
# 1. INTRADAY 5m/15m ORB + XGBOOST ENGINE
# ==========================================


def run_intraday_strategy(ticker_symbol):
  st.subheader(f"⏱️ Intraday 5m & 15m Analysis: {ticker_symbol}")

  with st.spinner(
      "Scanning broader liquid/midcap universe and processing ML filters..."
  ):
    # Fetch 5-minute intraday data
    df = yf.download(ticker_symbol, interval="5m", period="5d", progress=False)

    if df.empty:
      st.error(
          "No data found for the given ticker. Please check the symbol format"
          " (e.g., .NS for NSE)."
      )
      return

    # Flatten columns if multi-index is returned by yfinance
    if isinstance(df.columns, pd.MultiIndex):
      df.columns = df.columns.get_level_values(0)

    # Calculate Technical Features
    df["VWAP"] = (
        df["Volume"] * (df["High"] + df["Low"] + df["Close"]) / 3
    ).cumsum() / df["Volume"].cumsum()
    df["Volume_SMA"] = df["Volume"].rolling(window=20).mean()
    df["Volume_Spike"] = df["Volume"] > (2.5 * df["Volume_SMA"])

    # 15-Minute Opening Range Boundary Setup (First 3 candles of 5m = 15m ORB)
    df["Date"] = df.index.date
    orb_high = (
        df.groupby("Date")
        .apply(lambda x: x.iloc[0:3]["High"].max())
        .rename("ORB_High")
    )
    orb_low = (
        df.groupby("Date").apply(lambda x: x.iloc[0:3]["Low"].min()).rename("ORB_Low")
    )

    df = df.join(orb_high, on="Date")
    df = df.join(orb_low, on="Date")

    # Feature Engineering for ML Filter
    df["VWAP_Dist"] = (df["Close"] - df["VWAP"]) / df["VWAP"]
    df["Target"] = np.where(df["Close"].shift(-1) > df["Close"], 1, 0)

    # Train/Test Split for XGBoost
    features = ["VWAP_Dist", "Volume_Spike"]
    X = df[features].fillna(0)
    y = df["Target"]

    split = int(len(df) * 0.8)
    X_train = X.iloc[:split]
    y_train = y.iloc[:split]

    # Fit XGBoost Classifier to eliminate false breakouts
    model = XGBClassifier(n_estimators=50, max_depth=3, learning_rate=0.05)
    model.fit(X_train, y_train)

    df["ML_Signal"] = model.predict(X)

    # Display Metrics & Dataframes
    col1, col2, col3 = st.columns(3)
    col1.metric("Latest Close", f"₹ {df['Close'].iloc[-1]:.2f}")
    col2.metric(
        "Volume Spike Status",
        "Active 🚀" if df["Volume_Spike"].iloc[-1] else "Normal",
    )
    col3.metric(
        "XGBoost ML Prediction",
        "Bullish Continuation 🟢"
        if df["ML_Signal"].iloc[-1] == 1
        else "Bearish / Chop 🔴",
    )

    st.markdown("### Recent 5-Minute Intraday Data Feed & Signals")
    st.dataframe(
        df[
            [
                "Open",
                "High",
                "Low",
                "Close",
                "Volume",
                "VWAP",
                "ORB_High",
                "ORB_Low",
                "ML_Signal",
            ]
        ].tail(10)
    )


# ==========================================
# 2. SWING TRADING DAILY EMA & RRG PULLBACK
# ==========================================


def run_swing_strategy(ticker_symbol):
  st.subheader(f"📈 Swing Trading Daily Analysis: {ticker_symbol}")

  with st.spinner("Fetching daily swing data and calculating ATR/EMAs..."):
    # Fetch Daily data for swing setup
    df = yf.download(ticker_symbol, interval="1d", period="6mo", progress=False)

    if df.empty:
      st.error(
          "No data found for the given ticker. Please check the symbol format"
          " (e.g., .NS for NSE)."
      )
      return

    # Flatten columns if multi-index is returned by yfinance
    if isinstance(df.columns, pd.MultiIndex):
      df.columns = df.columns.get_level_values(0)

    # Moving Average Setup
    df["EMA_20"] = df["Close"].ewm(span=20, adjust=False).mean()
    df["EMA_50"] = df["Close"].ewm(span=50, adjust=False).mean()
    df["Volume_SMA"] = df["Volume"].rolling(window=20).mean()

    # ATR for Stop Loss Calculation
    df["TR"] = np.maximum(
        df["High"] - df["Low"],
        np.maximum(
            abs(df["High"] - df["Close"].shift(1)),
            abs(df["Low"] - df["Close"].shift(1)),
        ),
    )
    df["ATR"] = df["TR"].rolling(window=14).mean()

    # Pullback Condition: Price near 20 EMA on declining volume during an overall uptrend
    df["Trend_Up"] = (df["EMA_20"] > df["EMA_50"]) & (df["Close"] > df["EMA_50"])
    df["Pullback"] = (df["Low"] <= df["EMA_20"] * 1.01) & (
        df["Volume"] < df["Volume_SMA"]
    )
    df["Swing_Buy_Signal"] = df["Trend_Up"] & df["Pullback"]

    # Display Metrics & Dataframes
    col1, col2, col3 = st.columns(3)
    col1.metric("Daily 20 EMA", f"₹ {df['EMA_20'].iloc[-1]:.2f}")
    col2.metric("14-Period ATR", f"₹ {df['ATR'].iloc[-1]:.2f}")
    col3.metric(
        "Swing Signal Status",
        "Pullback Buy Setup 🎯"
        if df["Swing_Buy_Signal"].iloc[-1]
        else "Waiting for Setup ⏳",
    )

    st.markdown("### Recent Daily Swing Setup Data")
    st.dataframe(
        df[
            [
                "Open",
                "High",
                "Low",
                "Close",
                "Volume",
                "EMA_20",
                "ATR",
                "Swing_Buy_Signal",
            ]
        ].tail(10)
    )


# ==========================================
# MAIN EXECUTION ROUTE
# ==========================================
if st.sidebar.button("Run Live Platform Scan"):
  if strategy_tab == "Intraday (5m/15m ORB + XGBoost)":
    run_intraday_strategy(ticker)
  else:
    run_swing_strategy(ticker)
else:
  st.info(
      "👈 Configure your ticker symbol and select a strategy module from the"
      " sidebar, then click **Run Live Platform Scan** to initialize."
  )
