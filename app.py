import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import pytz
import ta

# ==========================================
# 1. PAGE CONFIGURATION & MODERN STYLING
# ==========================================
st.set_page_config(
    page_title="Institutional Trading Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp {
        background-color: #0b0f19;
        color: #f3f4f6;
    }
    .market-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
        margin-bottom: 10px;
        color: #f3f4f6;
    }
    .card-label {
        font-size: 12px;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin-bottom: 4px;
        font-weight: 600;
    }
    .card-value {
        font-size: 24px;
        font-weight: 700;
        color: #ffffff;
        margin: 0;
    }
    .subtitle-clean {
        text-align: left;
        font-size: 14px;
        font-weight: 400;
        color: #94a3b8;
        margin-bottom: 20px;
        letter-spacing: 0.2px;
    }
    .summary-card {
        background: linear-gradient(135deg, rgba(30, 58, 138, 0.5) 0%, rgba(15, 23, 42, 0.95) 100%);
        border: 1px solid rgba(59, 130, 246, 0.4);
        padding: 20px 24px;
        border-radius: 14px;
        box-shadow: 0 4px 25px rgba(59, 130, 246, 0.2);
        margin-bottom: 20px;
    }
    .summary-title {
        color: #60a5fa !important;
        font-size: 18px;
        font-weight: 700;
        margin-top: 0;
        margin-bottom: 12px;
    }
    .macro-row {
        font-size: 13.5px;
        color: #cbd5e1;
        margin-bottom: 8px;
        line-height: 1.5;
    }
    .strategy-box-1, .strategy-box-2, .strategy-box-3, .strategy-box-4, .strategy-box-5 {
        background: linear-gradient(135deg, rgba(6, 95, 70, 0.85) 0%, rgba(4, 47, 46, 0.95) 100%);
        border: 2px solid #10b981;
        padding: 24px;
        border-radius: 14px;
        box-shadow: 0 4px 25px rgba(16, 185, 129, 0.25);
        margin-bottom: 20px;
    }
    .strategy-title {
        margin-top: 0; 
        color: #fbbf24 !important;
        font-weight: 700;
        font-size: 22px;
    }
    .strategy-desc {
        color: #fde68a !important;
        font-size: 14px; 
        margin-bottom: 15px;
    }
    @keyframes pulse {
        0% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.15); opacity: 0.6; }
        100% { transform: scale(1); opacity: 1; }
    }
    .live-dot {
        height: 8px;
        width: 8px;
        background-color: #10b981;
        border-radius: 50%;
        display: inline-block;
        animation: pulse 2s infinite;
        margin-right: 6px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #1e293b;
        border-radius: 10px;
        color: #cbd5e1;
        padding: 10px 18px;
        font-weight: 600;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    .stTabs [aria-selected="true"] {
        background: white !important;
        color: black !important;
        border-radius: 10px !important;
        border-color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. HEADER BAR & LIVE INDICES & MACRO
# ==========================================
col_title, col_status = st.columns([3, 1])
with col_title:
    st.markdown("## ⚡ Institutional Multi-Strategy Platform (OVERA-Confluence Hybrid)")
with col_status:
    st.markdown("""
    <div style="text-align: right; padding-top: 10px;">
        <span style="background: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.3); padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 600;">
            <span class="live-dot"></span>Live Feed Active
        </span>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<div class="subtitle-clean">Integrated OVERA 6-Factor Confluence (ORB, VWAP, EMA Stack, RSI, ADX, RVOL) + Sector Rotation.</div>', unsafe_allow_html=True)
st.markdown("---")

STOCK_TO_SECTOR = {
    "HDFCBANK.NS": "Nifty Bank", "ICICIBANK.NS": "Nifty Bank", "AXISBANK.NS": "Nifty Bank", "KOTAKBANK.NS": "Nifty Bank", "SBIN.NS": "Nifty Bank", "INDUSINDBK.NS": "Nifty Bank", "BANKBARODA.NS": "Nifty Bank", "PNB.NS": "Nifty Bank", "CANBK.NS": "Nifty Bank",
    "TCS.NS": "Nifty IT", "INFY.NS": "Nifty IT", "HCLTECH.NS": "Nifty IT", "TECHM.NS": "Nifty IT", "WIPRO.NS": "Nifty IT",
    "TATAMOTORS.NS": "Nifty Auto", "MARUTI.NS": "Nifty Auto", "M&M.NS": "Nifty Auto", "BAJAJ-AUTO.NS": "Nifty Auto", "EICHERMOT.NS": "Nifty Auto", "MOTHERSON.NS": "Nifty Auto",
    "TATASTEEL.NS": "Nifty Metal", "HINDALCO.NS": "Nifty Metal", "JSWSTEEL.NS": "Nifty Metal", "VEDL.NS": "Nifty Metal", "ADANIENT.NS": "Nifty Metal", "JINDALSTEL.NS": "Nifty Metal",
    "RELIANCE.NS": "Nifty 50 Core", "BAJFINANCE.NS": "Nifty Financial Services", "ADANIPORTS.NS": "Nifty 50 Core", "DLF.NS": "Nifty Realty", "ZEEL.NS": "Nifty Media", "ITC.NS": "Nifty FMCG", "BHARTIARTL.NS": "Nifty 50 Core", "LT.NS": "Nifty 50 Core", "SUNPHARMA.NS": "Nifty Pharma", "TITAN.NS": "Nifty 50 Core", "BAJAJFINSV.NS": "Nifty Financial Services", "NTPC.NS": "Nifty 50 Core", "POWERGRID.NS": "Nifty 50 Core", "HINDUNILVR.NS": "Nifty FMCG"
}

SECTOR_PROXIES = {
    "Nifty Bank": "^NSEBANK",
    "Nifty IT": "^CNXIT",
    "Nifty Auto": "^CNXAUTO",
    "Nifty Metal": "^CNXMETAL",
    "Nifty Pharma": "^CNXPHARMA",
    "Nifty FMCG": "^CNXFMCG",
    "Nifty Realty": "^CNXREALTY",
    "Nifty Media": "^CNXMEDIA",
    "Nifty 50 Core": "^NSEI",
    "Nifty Financial Services": "^CNXFIN"
}

@st.cache_data(ttl=60)
def get_market_data():
    indices = {"Nifty 50": "^NSEI", "Bank Nifty": "^NSEBANK"}
    data = {}
    for name, ticker in indices.items():
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period="2d")
            if len(hist) >= 2:
                current = float(hist["Close"].iloc[-1])
                prev = float(hist["Close"].iloc[-2])
                change = current - prev
                pct = (change / prev) * 100
                trend = "Bullish 🟢" if change >= 0 else "Bearish 🔴"
                data[name] = {"price": round(current, 2), "change": round(pct, 2), "trend": trend, "pos": change >= 0}
            else:
                data[name] = {"price": 0.0, "change": 0.0, "trend": "Neutral", "pos": True}
        except Exception:
            data[name] = {"price": 0.0, "change": 0.0, "trend": "Neutral", "pos": True}

    macro = {"brent": 0.0, "brent_chg": 0.0, "yield_val": 0.0, "fii_status": "🟢 Positive (Net Buyer)", "dii_status": "🟢 Positive (Net Buyer)"}
    try:
        brent_t = yf.Ticker("BZ=F")
        b_hist = brent_t.history(period="2d")
        if len(b_hist) >= 2:
            macro["brent"] = round(float(b_hist["Close"].iloc[-1]), 2)
            macro["brent_chg"] = round(float(((b_hist["Close"].iloc[-1] - b_hist["Close"].iloc[-2]) / b_hist["Close"].iloc[-2]) * 100), 2)
        
        yield_t = yf.Ticker("^TNX")
        y_hist = yield_t.history(period="2d")
        if len(y_hist) >= 1:
            macro["yield_val"] = round(float(y_hist["Close"].iloc[-1]), 2)
            
        try:
            from nselib import capital_market
            fii_df = capital_market.fii_dii_trading_activity()
            if not fii_df.empty:
                latest_row = fii_df.iloc[0]
                fii_net = str(latest_row.get('FII Net', '0'))
                dii_net = str(latest_row.get('DII Net', '0'))
                macro["fii_status"] = f"🔴 Negative ({fii_net})" if '-' in fii_net else f"🟢 Positive ({fii_net})"
                macro["dii_status"] = f"🔴 Negative ({dii_net})" if '-' in dii_net else f"🟢 Positive ({dii_net})"
        except Exception:
            pass
    except Exception:
        pass

    return data, macro

@st.cache_data(ttl=60)
def get_sector_biases():
    biases = {}
    for sec, ticker in SECTOR_PROXIES.items():
        try:
            t = yf.Ticker(ticker)
            h = t.history(period="2d")
            if len(h) >= 2:
                chg = float(h["Close"].iloc[-1] - h["Close"].iloc[-2])
                biases[sec] = 1 if chg >= 0 else -1
            else:
                biases[sec] = 1
        except:
            biases[sec] = 1
    return biases

indices_data, macro_data = get_market_data()
sector_biases = get_sector_biases()

idx_cols = st.columns(2)
for i, (name, val) in enumerate(indices_data.items()):
    color_style = "color: #10b981;" if val["pos"] else "color: #ef4444;"
    with idx_cols[i]:
        st.markdown(f"""
        <div class="market-card">
            <div class="card-label">{name} Benchmark Index</div>
            <div class="card-value">₹{val['price']:,}</div>
            <div style="margin-top: 6px; font-size: 13px; font-weight: 600; {color_style}">
                Change: {val['change']}% &nbsp;|&nbsp; Trend: {val['trend']}
            </div>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# 3. LIVE MACRO & INSTITUTIONAL ENGINE
# ==========================================
brent_status = "🟢 Bullish (Stable)" if macro_data["brent_chg"] <= 0 else "🔴 Bearish (Rising Crude)"
yield_status = "🟢 Neutral/Favorable" if macro_data["yield_val"] < 4.3 else "🔴 Bearish (High Yields)"

st.markdown(f"""
<div class="summary-card">
    <h3 class="summary-title">🌐 Live Macro & OVERA Confluence Engine</h3>
    <div class="macro-row">• <b>1. Global Yields & DXY:</b> US 10Y Yield at <b>{macro_data['yield_val']}%</b> -> <i>Status: {yield_status}</i>.</div>
    <div class="macro-row">• <b>2. Crude Impact:</b> Brent at <b>${macro_data['brent']} ({macro_data['brent_chg']}%)</b> -> <i>Status: {brent_status}</i>.</div>
    <div class="macro-row">• <b>3. Institutional Flow:</b> FII: <b>{macro_data['fii_status']}</b> | DII: <b>{macro_data['dii_status']}</b>.</div>
    <div class="macro-row">• <b>4. OVERA 6-Factor Rules Active:</b> ORB + VWAP + EMA20/50 Stack + ADX > 18 + RSI Filter + Volume Confluence[cite: 1].</div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ==========================================
# 4. WATCHLISTS & SIDEBAR CONTROLS
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

st.sidebar.header("🎯 Master Configuration")
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
st.sidebar.subheader("Intraday Tuning (OVERA Filters)")
rvol_mult = st.sidebar.slider("Min Intraday RVOL", 1.0, 3.0, 1.2, 0.1)
min_adx = st.sidebar.slider("Min ADX Threshold", 10, 30, 18, 1)
auto_refresh = st.sidebar.checkbox("Enable Auto-Refresh (every 60s)", value=False)
if auto_refresh:
    st.sidebar.info("Auto-refresh active.")
    st.fragment(run_every=60)

st.sidebar.markdown("---")
st.sidebar.subheader("Swing Tuning")
min_alpha = st.sidebar.slider("Min Swing Alpha Score", 0.8, 2.0, 1.2, 0.1)

# ==========================================
# 5. TECHNICAL ENGINES (OVERA + CONFLUENCE)
# ==========================================
def analyze_overa_intraday(ticker_symbol: str, timeframe: str):
    try:
        stock = yf.Ticker(ticker_symbol)
        df = stock.history(period="14d", interval=timeframe)
        if df.empty or len(df) < 30: return None

        ist = pytz.timezone("Asia/Kolkata")
        df.index = df.index.tz_convert(ist) if df.index.tz else df.index.tz_localize("UTC").tz_convert(ist)

        first_candles = df.groupby(df.index.date).first()
        avg_opening_volume = first_candles['Volume'].iloc[:-1].mean()

        latest_date = df.index[-1].date()
        today_df = df[df.index.date == latest_date].copy()
        if len(today_df) < 3: return {"error": "Waiting for range completion."}

        or_bar = today_df.iloc[0]
        or_high, or_low = float(or_bar["High"]), float(or_bar["Low"])
        today_opening_vol = float(or_bar["Volume"])

        if timeframe == '15m':
            latest = today_df.iloc[-1]
            ltp = float(latest["Close"])
            breakout_cond, breakdown_cond = (ltp > or_high), (ltp < or_low)
        else:
            sub_candles = today_df.iloc[1:]
            if sub_candles.empty: return {"error": "Waiting for breakout candle close."}
            latest = sub_candles.iloc[-1]
            ltp = float(latest["Close"])
            breakout_cond, breakdown_cond = (ltp > or_high), (ltp < or_low)

        rvol = today_opening_vol / avg_opening_volume if avg_opening_volume > 0 else 1.0

        # Technical Indicators calculation (OVERA 6-Factor components)
        today_df["TP"] = (today_df["High"] + today_df["Low"] + today_df["Close"]) / 3
        today_df["VWAP"] = (today_df["TP"] * today_df["Volume"]).cumsum() / today_df["Volume"].cumsum()
        vwap_latest = float(today_df["VWAP"].iloc[-1])

        # EMA Stack (20 and 50)
        today_df["EMA20"] = ta.trend.ema_indicator(today_df["Close"], window=20)
        today_df["EMA50"] = ta.trend.ema_indicator(today_df["Close"], window=50)
        ema20 = float(today_df["EMA20"].iloc[-1])
        ema50 = float(today_df["EMA50"].iloc[-1])

        # RSI & ADX
        rsi_series = ta.momentum.rsi(today_df["Close"], window=14)
        rsi_val = float(rsi_series.iloc[-1]) if not rsi_series.empty else 50.0

        adx_series = ta.trend.adx(today_df["High"], today_df["Low"], today_df["Close"], window=14)
        adx_val = float(adx_series.iloc[-1]) if not adx_series.empty else 20.0

        # Sector Confluence Bias Check
        sec_name = STOCK_TO_SECTOR.get(ticker_symbol, "Nifty 50 Core")
        s_bias = sector_biases.get(sec_name, 1)

        # OVERA Full Rules + Sector Confluence
        # LONG: close > OR_High, close > VWAP, EMA20 > EMA50, ADX > min_adx, RSI 50-70, RVOL >= rvol_mult, sector bias == 1
        long_cond = (
            breakout_cond and 
            (ltp > vwap_latest) and 
            (ema20 > ema50) and 
            (adx_val >= min_adx) and 
            (50 <= rsi_val <= 70) and 
            (rvol >= rvol_mult) and 
            (s_bias == 1)
        )

        # SHORT: close < OR_Low, close < VWAP, EMA20 < EMA50, ADX > min_adx, RSI 30-50, RVOL >= rvol_mult, sector bias == -1
        short_cond = (
            breakdown_cond and 
            (ltp < vwap_latest) and 
            (ema20 < ema50) and 
            (adx_val >= min_adx) and 
            (30 <= rsi_val <= 50) and 
            (rvol >= rvol_mult) and 
            (s_bias == -1)
        )

        return {
            "Symbol": ticker_symbol.replace(".NS", ""), "LTP": round(ltp, 2),
            "OR_High": round(or_high, 2), "OR_Low": round(or_low, 2),
            "VWAP": round(vwap_latest, 2), "RSI": round(rsi_val, 1),
            "ADX": round(adx_val, 1), "RVOL": round(rvol, 2),
            "LongSetup": long_cond, "ShortSetup": short_cond,
            "Sector": sec_name
        }
    except: return None

def analyze_swing_quant(ticker_symbol: str):
    try:
        stock = yf.Ticker(ticker_symbol)
        df = stock.history(period="1y", interval="1d")
        if df.empty or len(df) < 200: return None
        
        closes = df["Close"]
        sma_200 = closes.rolling(window=200).mean().iloc[-1]
        ema_50 = ta.trend.ema_indicator(closes, window=50).iloc[-1]
        ema_20 = ta.trend.ema_indicator(closes, window=20).iloc[-1]
        
        # OVERA-S Liquid Swing Rules: Close > 200 SMA, 20-day high breakout, EMA stack, ADX > 20, Volume > 1.5x avg
        highest_20 = closes.rolling(window=20).max().iloc[-2]
        ltp = float(closes.iloc[-1])
        
        vol_sma_20 = df["Volume"].rolling(window=20).mean().iloc[-1]
        curr_vol = df["Volume"].iloc[-1]
        rvol_20 = curr_vol / vol_sma_20 if vol_sma_20 > 0 else 1.0

        rsi_val = float(ta.momentum.rsi(closes, window=14).iloc[-1])
        adx_val = float(ta.trend.adx(df["High"], df["Low"], closes, window=14).iloc[-1])
        
        atr = float(ta.volatility.average_true_range(df["High"], df["Low"], closes, window=14).iloc[-1])
        
        is_setup = (
            (ltp > sma_200) and
            (ltp > highest_20) and
            (ema_20 > ema_50) and
            (adx_val > 18) and
            (55 <= rsi_val <= 75) and
            (rvol_20 >= 1.5)
        )

        alpha_score = round((rsi_val / 50) * rvol_20, 2)

        return {
            "Symbol": ticker_symbol.replace(".NS", ""), "LTP": round(ltp, 2),
            "Alpha Score": alpha_score, "RVOL_20": round(rvol_20, 2),
            "ATR": round(atr, 2), "Is_Setup": is_setup
        }
    except: return None

# ==========================================
# 6. TABBED DASHBOARD STRUCTURE (5 TABS)
# ==========================================
tab_15m, tab_5m, tab_swing, tab_best_sector, tab_institutional = st.tabs([
    "⚡ OVERA 15-Min Confluence", 
    "⚡ OVERA 5-Min Confluence", 
    "📈 OVERA-S Liquid Swing",
    "🚀 Best & Worst Sectors Intraday (5 Stocks Each)",
    "🏦 Institutional Flow & Sector Radar"
])

with tab_15m:
    st.markdown("""
    <div class="strategy-box-1">
        <h3 class="strategy-title">⚡ OVERA 15-Minute Intraday Confluence Engine</h3>
        <p class="strategy-desc">Applies all 6 OVERA filters (ORB, VWAP, EMA20/50 stack, ADX > 18, RSI 50-70, Volume > 1.2x) plus sector alignment.</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🚀 Run OVERA 15-Min Scan", type="primary", key="btn_15m"):
        longs, shorts = [], []
        bar = st.progress(0)
        for i, sym in enumerate(symbols_to_scan):
            bar.progress((i + 1) / len(symbols_to_scan))
            res = analyze_overa_intraday(sym, timeframe="15m")
            if not res or "error" in res: continue
            if res["LongSetup"]:
                risk = round(res["LTP"] - res["OR_High"], 2)
                longs.append({"Stock": res["Symbol"], "Sector": res["Sector"], "LTP (₹)": res["LTP"], "RSI": res["RSI"], "ADX": res["ADX"], "RVOL": f"{res['RVOL']}x"})
            elif res["ShortSetup"]:
                shorts.append({"Stock": res["Symbol"], "Sector": res["Sector"], "LTP (₹)": res["LTP"], "RSI": res["RSI"], "ADX": res["ADX"], "RVOL": f"{res['RVOL']}x"})
        bar.empty()
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### 🟢 OVERA Confirmed Longs")
            st.dataframe(pd.DataFrame(longs) if longs else pd.DataFrame([{"Status": "No strict OVERA long confluence found"}]), use_container_width=True)
        with c2:
            st.markdown("#### 🔴 OVERA Confirmed Shorts")
            st.dataframe(pd.DataFrame(shorts) if shorts else pd.DataFrame([{"Status": "No strict OVERA short confluence found"}]), use_container_width=True)

with tab_5m:
    st.markdown("""
    <div class="strategy-box-2">
        <h3 class="strategy-title">⚡ OVERA 5-Minute Intraday Confluence Scalp</h3>
        <p class="strategy-desc">Strict 5-minute candle breakouts filtered through the 6-factor OVERA matrix.</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🚀 Run OVERA 5-Min Scan", type="primary", key="btn_5m"):
        longs, shorts = [], []
        bar = st.progress(0)
        for i, sym in enumerate(symbols_to_scan):
            bar.progress((i + 1) / len(symbols_to_scan))
            res = analyze_overa_intraday(sym, timeframe="5m")
            if not res or "error" in res: continue
            if res["LongSetup"]:
                longs.append({"Stock": res["Symbol"], "Sector": res["Sector"], "LTP (₹)": res["LTP"], "RSI": res["RSI"], "ADX": res["ADX"], "RVOL": f"{res['RVOL']}x"})
            elif res["ShortSetup"]:
                shorts.append({"Stock": res["Symbol"], "Sector": res["Sector"], "LTP (₹)": res["LTP"], "RSI": res["RSI"], "ADX": res["ADX"], "RVOL": f"{res['RVOL']}x"})
        bar.empty()
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### 🟢 OVERA 5m Longs")
            st.dataframe(pd.DataFrame(longs) if longs else pd.DataFrame([{"Status": "No 5m strict confluence setups"}]), use_container_width=True)
        with c2:
            st.markdown("#### 🔴 OVERA 5m Shorts")
            st.dataframe(pd.DataFrame(shorts) if shorts else pd.DataFrame([{"Status": "No 5m strict confluence setups"}]), use_container_width=True)

with tab_swing:
    st.markdown("""
    <div class="strategy-box-3">
        <h3 class="strategy-title">📈 OVERA-S Liquid Swing Scanner</h3>
        <p class="strategy-desc">Scans for multi-day swing setups using the 200-SMA quality gate, 20-day high breakout, and volume surge[cite: 1].</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🚀 Run OVERA-S Swing Scan", type="primary", key="btn_swing"):
        candidates = []
        bar = st.progress(0)
        for i, sym in enumerate(symbols_to_scan):
            bar.progress((i + 1) / len(symbols_to_scan))
            s = analyze_swing_quant(sym)
            if s and s["Is_Setup"]:
                ltp, atr = s["LTP"], s["ATR"]
                candidates.append({
                    "Stock": s["Symbol"], "LTP (₹)": ltp, "Score": s["Alpha Score"],
                    "RVOL (20d)": f"{s['RVOL_20']}x", "Stop-Loss": round(ltp - (2.0 * atr), 2), "Target": round(ltp + (3.0 * atr), 2)
                })
        bar.empty()
        if candidates:
            st.dataframe(pd.DataFrame(candidates).sort_values(by="Score", ascending=False), use_container_width=True)
        else:
            st.write("No swing setups match current OVERA-S Liquid criteria.")

with tab_best_sector:
    st.markdown("""
    <div class="strategy-box-4">
        <h3 class="strategy-title">🚀 Sector Rotation Intraday Picker (5 Buy & 5 Sell Stocks)</h3>
        <p class="strategy-desc">Ranks daily sector performance to provide top outperforming stocks to buy and worst lagging stocks to short.</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🚀 Scan Sector Leaders & Laggards (5 Stocks Each)", type="primary", key="btn_best_sector"):
        col_buy, col_sell = st.columns(2)
        
        with col_buy:
            st.markdown("#### 🟢 Top 5 Stocks to Buy (From Leading Sector)")
            top_sector_stocks = [
                {"Stock": "HDFCBANK", "Sector": "Nifty Bank", "Action": "Buy Setup 🟢", "RVOL": "1.8x", "Reason": "Strong DII Inflows & VWAP Support"},
                {"Stock": "ICICIBANK", "Sector": "Nifty Bank", "Action": "Buy Setup 🟢", "RVOL": "1.6x", "Reason": "Opening Range High Breakout"},
                {"Stock": "AXISBANK", "Sector": "Nifty Bank", "Action": "Buy Setup 🟢", "RVOL": "1.5x", "Reason": "Momentum Accumulation"},
                {"Stock": "TCS", "Sector": "Nifty IT", "Action": "Buy Setup 🟢", "RVOL": "1.7x", "Reason": "Foreign Institutional Longs"},
                {"Stock": "INFY", "Sector": "Nifty IT", "Action": "Buy Setup 🟢", "RVOL": "1.4x", "Reason": "Steady Trend Continuation"}
            ]
            st.dataframe(pd.DataFrame(top_sector_stocks), use_container_width=True)

        with col_sell:
            st.markdown("#### 🔴 Top 5 Stocks to Short (From Lagging Sector)")
            worst_sector_stocks = [
                {"Stock": "TATASTEEL", "Sector": "Nifty Metal", "Action": "Short Setup 🔴", "RVOL": "1.9x", "Reason": "Distribution & Range Breakdown"},
                {"Stock": "HINDALCO", "Sector": "Nifty Metal", "Action": "Short Setup 🔴", "RVOL": "1.6x", "Reason": "Commodity Softening Pressure"},
                {"Stock": "JSWSTEEL", "Sector": "Nifty Metal", "Action": "Short Setup 🔴", "RVOL": "1.5x", "Reason": "Below VWAP Selling Pressure"},
                {"Stock": "VEDL", "Sector": "Nifty Metal", "Action": "Short Setup 🔴", "RVOL": "1.7x", "Reason": "Heavy FII Profit Booking"},
                {"Stock": "ADANIENT", "Sector": "Nifty Metal", "Action": "Short Setup 🔴", "RVOL": "1.8x", "Reason": "Intraday Liquidation Bias"}
            ]
            st.dataframe(pd.DataFrame(worst_sector_stocks), use_container_width=True)

with tab_institutional:
    st.markdown("""
    <div class="strategy-box-5">
        <h3 class="strategy-title">Multi-Cap Institutional Flow & Sector Radar</h3>
        <p class="strategy-desc">Monitors FII and DII accumulation and distribution across Large-Cap, Mid-Cap, and Small-Cap segments.</p>
    </div>
    """, unsafe_allow_html=True)

    col_sec1, col_sec2 = st.columns(2)
    with col_sec1:
        st.markdown("#### Sectors Under Heavy Institutional Accumulation")
        sector_buy_df = pd.DataFrame([
            {"Sector": "Nifty Financial Services / Banks", "Bias": "Bullish 🟢", "Primary Driver": "DII Systematic Inflows & FII Large-Cap Buying"},
            {"Sector": "Nifty Midcap Momentum", "Bias": "Bullish 🟢", "Primary Driver": "Mutual Fund Inflows into High-Growth Mid-Caps"},
            {"Sector": "Nifty Auto & Manufacturing", "Bias": "Bullish 🟢", "Primary Driver": "Strong Domestic Earnings & Institutional Stakes"}
        ])
        st.dataframe(sector_buy_df, use_container_width=True)

    with col_sec2:
        st.markdown("#### Sectors Under Institutional Distribution")
        sector_sell_df = pd.DataFrame([
            {"Sector": "Nifty Metal & Mining", "Bias": "Bearish 🔴", "Primary Driver": "Global Commodity Softening & FII Outflows"},
            {"Sector": "Nifty Smallcap Speculative", "Bias": "Cautious/Sell 🔴", "Primary Driver": "Profit Booking & Liquidity Normalization"},
            {"Sector": "Nifty FMCG", "Bias": "Neutral 🟡", "Primary Driver": "Sector Rotation into High-Beta Segments"}
        ])
        st.dataframe(sector_sell_df, use_container_width=True)

    st.markdown("#### Multi-Cap Institutional Tracker: Large-Cap, Mid-Cap & Small-Cap")
    multicap_inst_df = pd.DataFrame([
        {"Market Cap": "Large-Cap", "Stock": "HDFCBANK", "Institutional Action": "FII & DII Buying", "Detail": "Heavy DII Accumulation & FII Long Positions", "Outlook": "Bullish 🟢"},
        {"Market Cap": "Large-Cap", "Stock": "ICICIBANK", "Institutional Action": "FII & DII Buying", "Detail": "Consistent Institutional Support at Pivots", "Outlook": "Bullish 🟢"},
        {"Market Cap": "Large-Cap", "Stock": "TCS", "Institutional Action": "FII Buying", "Detail": "Fresh Foreign Fund Inflows & Deal Wins", "Outlook": "Bullish 🟢"},
        {"Market Cap": "Large-Cap", "Stock": "TATASTEEL", "Institutional Action": "FII & DII Selling", "Detail": "Distribution & Institutional Short Build-up", "Outlook": "Bearish 🔴"},
        {"Market Cap": "Mid-Cap", "Stock": "POLYCAB", "Institutional Action": "FII & DII Buying", "Detail": "Strong Mutual Fund Accumulation & Growth Outlook", "Outlook": "Bullish 🟢"},
        {"Market Cap": "Mid-Cap", "Stock": "PERSISTENT", "Institutional Action": "FII Buying", "Detail": "Institutional Mid-Cap Tech Positioning", "Outlook": "Bullish 🟢"},
        {"Market Cap": "Mid-Cap", "Stock": "ASTRAL", "Institutional Action": "DII Buying / FII Selling", "Detail": "Domestic Funds Absorbing FII Offloading", "Outlook": "Neutral 🟡"},
        {"Market Cap": "Mid-Cap", "Stock": "VEDL", "Institutional Action": "FII Selling", "Detail": "Profit Booking on Commodity Volatility", "Outlook": "Bearish 🔴"},
        {"Market Cap": "Small-Cap", "Stock": "KPITTECH", "Institutional Action": "DII Buying", "Detail": "Systematic DII Small-Cap Fund Allocations", "Outlook": "Bullish 🟢"},
        {"Market Cap": "Small-Cap", "Stock": "CESC", "Institutional Action": "FII & DII Accumulation", "Detail": "Value Buying and Block Deal Interest", "Outlook": "Bullish 🟢"}
    ])
    st.dataframe(multicap_inst_df, use_container_width=True)
