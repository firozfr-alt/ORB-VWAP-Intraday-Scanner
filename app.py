import numpy as np
import pandas as pd
import yfinance as yf
from xgboost import XGBClassifier

# ==========================================
# 1. INTRADAY 5m/15m ORB + XGBOOST FILTER
# ==========================================


def run_intraday_strategy(ticker_symbol):
  # Fetch 5-minute intraday data for the target stock
  df = yf.download(ticker_symbol, interval="5m", period="5d")

  # Calculate Technical Features
  df["VWAP"] = (df["Volume"] * (df["High"] + df["Low"] + df["Close"]) / 3).cumsum() / df[
      "Volume"
  ].cumsum()
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
  df["Target"] = np.where(
      df["Close"].shift(-1) > df["Close"], 1, 0
  )  # Next candle direction

  # Train/Test Split for XGBoost
  features = ["VWAP_Dist", "Volume_Spike"]
  X = df[features].fillna(0)
  y = df["Target"]

  split = int(len(df) * 0.8)
  X_train, X_test = X.iloc[:split], X.iloc[split:]
  y_train, y_test = y.iloc[:split], y.iloc[split:]

  # Fit XGBoost Classifier to eliminate false breakouts
  model = XGBClassifier(n_estimators=50, max_depth=3, learning_rate=0.05)
  model.fit(X_train, y_train)

  df["ML_Signal"] = model.predict(X)
  return df


# ==========================================
# 2. SWING TRADING DAILY EMA & RRG PULLBACK
# ==========================================


def run_swing_strategy(ticker_symbol):
  # Fetch Daily data for swing setup
  df = yf.download(ticker_symbol, interval="1d", period="6mo")

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

  return df.tail(10)


# Example execution for an NSE Stock (e.g., Reliance or Tata Motors)
# intraday_results = run_intraday_strategy("RELIANCE.NS")
# swing_results = run_swing_strategy("TATAMOTORS.NS")
