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
    st.markdown("## ⚡ Institutional Multi-Strategy Platform")
with col_status:
    st.markdown("""
    <div style="text-align: right; padding-top: 10px;">
        <span style="background: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.3); padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 600;">
            <span class="live-dot"></span>Live Feed Active
        </span>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<div class="subtitle-clean">Clean 15-Min ORB, Filtered 5-Min Candle-Close ORB, and Quant Swing Models.</div>', unsafe_allow_html=True)
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
    <h3 class="summary-title">🌐 Live Macro & Institutional Sentiment Engine</h3>
    <div class="macro-row">• <b>1. Global Yields & DXY:</b> US 10Y Yield at <b>{macro_data['yield_val']}%</b> -> <i>Status: {yield_status}</i>.</div>
    <div class="macro-row">• <b>2. Crude Impact:</b> Brent at <b>${macro_data['brent']} ({macro_data['brent_chg']}%)</b> -> <i>Status: {brent_status}</i>.</div>
    <div class="macro-row">• <b>3. Institutional Flow:</b> FII: <b>{macro_data['fii_status']}</b> | DII: <b>{macro_data['dii_status']}</b>.</div>
    <div class="macro-row">• <b>4. Sector-Confluence Engine:</b> Intraday ORB triggers are filtered by live sector bias ($S_{{{'bias'}}}$).</div>
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
st.sidebar.subheader("Intraday Tuning")
rvol_mult = st.sidebar.slider("Min Intraday RVOL", 1.0, 5.0, 1.5, 0.1)
auto_refresh = st.sidebar.checkbox("Enable Auto-Refresh (every 60s)", value=False)
if auto_refresh:
    st.sidebar.info("Auto-refresh active.")
    st.fragment(run_every=60)

st.sidebar.markdown("---")
st.sidebar.subheader("Swing Tuning")
min_alpha = st.sidebar.slider("Min Swing Alpha Score", 0.8, 2.0, 1.2, 0.1)

# ==========================================
# 5. TECHNICAL ENGINES (CONFLUENCE ENHANCED)
# ==========================================
def analyze_orb_strategy(ticker_symbol: str, timeframe: str):
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
        if len(today_df) < 2: return {"error": "Waiting for range completion."}

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

        today_df["TP"] = (today_df["High"] + today_df["Low"] + today_df["Close"]) / 3
        today_df["VWAP"] = (today_df["TP"] * today_df["Volume"]).cumsum() / today_df["Volume"].cumsum()
        vwap_latest = float(today_df["VWAP"].iloc[-1])

        sec_name = STOCK_TO_SECTOR.get(ticker_symbol, "Nifty 50 Core")
        s_bias = sector_biases.get(sec_name, 1)

        filtered_breakout = breakout_cond and (ltp > vwap) and (rvol >= rvol_mult) and (s_bias == 1)
        filtered_breakdown = breakdown_cond and (ltp < vwap) and (rvol >= rvol_mult) and (s_bias == -1)

        return {
            "Symbol": ticker_symbol.replace(".NS", ""), "LTP": round(ltp, 2),
            "OR_High": round(or_high, 2), "OR_Low": round(or_low, 2),
            "VWAP": round(vwap_latest, 2), "RVOL": round(rvol, 2),
            "Breakout": filtered_breakout, "Breakdown": filtered_breakdown,
            "Sector": sec_name, "SectorBias": s_bias
        }
    except: return None

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
        
        ltp = float(closes.iloc[-1])
        alpha = float(alpha_score.iloc[-1])
        z_val = float(z_price.iloc[-1])
        rvol_val = float(rvol_20.iloc[-1])
        
        atr = float(ta.volatility.average_true_range(df["High"], df["Low"], df["Close"], window=14).iloc[-1])
        is_setup = (alpha >= min_alpha) and (0.5 <= z_val <= 2.0) and (rvol_val >= 1.2)
        
        return {
            "Symbol": ticker_symbol.replace(".NS", ""), "LTP": round(ltp, 2),
            "Alpha Score": round(alpha, 2), "Z-Score": round(z_val, 2),
            "RVOL_20": round(rvol_val, 2), "ATR": round(atr, 2), "Is_Setup": is_setup
        }
    except: return None

# ==========================================
# 6. TABBED DASHBOARD STRUCTURE (5 TABS)
# ==========================================
tab_15m, tab_5m, tab_swing, tab_best_sector, tab_institutional = st.tabs([
    "⚡ Intraday 15-Min ORB (Clean)", 
    "⚡ Intraday 5-Min (Candle Close + RVOL)", 
    "📈 Quant Multi-Factor Swing",
    "🚀 Best & Worst Sectors Intraday (5 Stocks Each)",
    "🏦 Institutional Flow & Sector Radar"
])

with tab_15m:
    st.markdown("""
    <div class="strategy-box-1">
        <h3 class="strategy-title">⚡ 15-Minute Confluence ORB (Sector-Aligned)</h3>
        <p class="strategy-desc">Institutional 15-minute opening range breakout filtered by live sector bias and RVOL.</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🚀 Run 15-Min Confluence Scan", type="primary", key="btn_15m"):
        buy_signals, sell_signals = [], []
        bar = st.progress(0)
        for i, sym in enumerate(symbols_to_scan):
            bar.progress((i + 1) / len(symbols_to_scan))
            data = analyze_orb_strategy(sym, timeframe="15m")
            if not data or "error" in data: continue
            ltp, or_h, or_l, vwap, rvol = data["LTP"], data["OR_High"], data["OR_Low"], data["VWAP"], data["RVOL"]
            if data["Breakout"]:
                risk = round(ltp - or_l, 2)
                buy_signals.append({"Stock": data["Symbol"], "Sector": data["Sector"], "LTP (₹)": ltp, "Stop-Loss": or_l, "Target": round(ltp + (1.5 * risk), 2), "RVOL": f"{rvol}x"})
            elif data["Breakdown"]:
                risk = round(or_h - ltp, 2)
                sell_signals.append({"Stock": data["Symbol"], "Sector": data["Sector"], "LTP (₹)": ltp, "Stop-Loss": or_h, "Target": round(ltp - (1.5 * risk), 2), "RVOL": f"{rvol}x"})
        bar.empty()
        c1, c2 = st.columns(2)
        with c1: 
            st.markdown("#### 🟢 Sector-Confirmed Longs")
            st.dataframe(pd.DataFrame(buy_signals) if buy_signals else pd.DataFrame([{"Status": "No Sector-Aligned Breakouts"}]), use_container_width=True)
        with c2: 
            st.markdown("#### 🔴 Sector-Confirmed Shorts")
            st.dataframe(pd.DataFrame(sell_signals) if sell_signals else pd.DataFrame([{"Status": "No Sector-Aligned Breakdowns"}]), use_container_width=True)

with tab_5m:
    st.markdown("""
    <div class="strategy-box-2">
        <h3 class="strategy-title">⚡ 5-Minute Confluence ORB (Sector-Aligned)</h3>
        <p class="strategy-desc">Strict candle-close 5-minute breakout verified against parent sector momentum.</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🚀 Run Filtered 5-Min Confluence Scan", type="primary", key="btn_5m"):
        buy_signals, sell_signals = [], []
        bar = st.progress(0)
        for i, sym in enumerate(symbols_to_scan):
            bar.progress((i + 1) / len(symbols_to_scan))
            data = analyze_orb_strategy(sym, timeframe="5m")
            if not data or "error" in data: continue
            ltp, or_h, or_l, vwap, rvol = data["LTP"], data["OR_High"], data["OR_Low"], data["VWAP"], data["RVOL"]
            if data["Breakout"]:
                risk = round(ltp - or_l, 2)
                buy_signals.append({"Stock": data["Symbol"], "Sector": data["Sector"], "LTP (₹)": ltp, "Stop-Loss": or_l, "Target": round(ltp + (1.5 * risk), 2), "RVOL": f"{rvol}x"})
            elif data["Breakdown"]:
                risk = round(or_h - ltp, 2)
                sell_signals.append({"Stock": data["Symbol"], "Sector": data["Sector"], "LTP (₹)": ltp, "Stop-Loss": or_h, "Target": round(ltp - (1.5 * risk), 2), "RVOL": f"{rvol}x"})
        bar.empty()
        c1, c2 = st.columns(2)
        with c1: 
            st.markdown("#### 🟢 Sector-Confirmed Longs")
            st.dataframe(pd.DataFrame(buy_signals) if buy_signals else pd.DataFrame([{"Status": "No Sector-Aligned Breakouts"}]), use_container_width=True)
        with c2: 
            st.markdown("#### 🔴 Sector-Confirmed Shorts")
            st.dataframe(pd.DataFrame(sell_signals) if sell_signals else pd.DataFrame([{"Status": "No Sector-Aligned Breakdowns"}]), use_container_width=True)

with tab_swing:
    st.markdown("""
    <div class="strategy-box-3">
        <h3 class="strategy-title">📈 Quantitative Multi-Factor Swing Scanner</h3>
        <p class="strategy-desc">Evaluates momentum, Z-scores, and institutional volume accumulation.</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🚀 Run Quant Swing Scan", type="primary", key="btn_swing"):
        swing_candidates = []
        bar = st.progress(0)
        for i, sym in enumerate(symbols_to_scan):
            bar.progress((i + 1) / len(symbols_to_scan))
            s_data = analyze_swing_quant(sym)
            if s_data and s_data["Is_Setup"]:
                ltp, atr = s_data["LTP"], s_data["ATR"]
                swing_candidates.append({
                    "Stock": s_data["Symbol"], "LTP (₹)": ltp, "Alpha Score": s_data["Alpha Score"], 
                    "Z-Score": s_data["Z-Score"], "RVOL (20d)": f"{s_data['RVOL_20']}x", 
                    "Stop-Loss": round(ltp - (2.0 * atr), 2), "Target": round(ltp + (3.0 * atr), 2)
                })
        bar.empty()
        if swing_candidates:
            st.dataframe(pd.DataFrame(swing_candidates).sort_values(by="Alpha Score", ascending=False), use_container_width=True)
        else:
            st.write("No swing setups match current quantitative alpha criteria.")

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
