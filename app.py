import numpy as np
import pandas as pd

def calculate_vwap(df: pd.DataFrame) -> pd.Series:
    typical_price = (df['high'] + df['low'] + df['close']) / 3
    return (typical_price * df['volume']).cumsum() / df['volume'].cumsum()

def scan_options_rvol_blast(df_5m: pd.DataFrame, min_rvol: float = 1.50) -> dict:
    """
    Evaluates high-delta option buying setup on 5-minute candles.
    Requires columns: ['open', 'high', 'low', 'close', 'volume']
    """
    if len(df_5m) < 25:
        return {"trigger": False}

    df = df_5m.copy()
    df['vwap'] = calculate_vwap(df)
    df['ema9'] = df['close'].ewm(span=9, adjust=False).mean()
    df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['vol_sma20'] = df['volume'].rolling(window=20).mean()
    df['rvol'] = df['volume'] / df['vol_sma20']

    current = df.iloc[-1]
    prior_3_high = df['high'].iloc[-4:-1].max()

    # Strategy Conditions
    trend_ok = (current['close'] > current['vwap']) and (current['ema9'] > current['ema20'])
    volume_surge = current['rvol'] >= min_rvol
    box_breakout = current['close'] > prior_3_high

    if trend_ok and volume_surge and box_breakout:
        spot_price = current['close']
        return {
            "trigger": True,
            "signal": "BUY_CALL_OPTION",
            "spot_price": spot_price,
            "target_delta_range": (0.65, 0.80),
            "suggested_moneyness": "1_STRIKE_ITM",
            "rvol": round(current['rvol'], 2),
            "stop_loss_spot": round(current['vwap'], 2)
        }
    return {"trigger": False}

def scan_stock_rs_pullback(df_15m: pd.DataFrame, benchmark_15m: pd.DataFrame) -> dict:
    """
    Evaluates equity relative strength pullback setup on 15-minute candles.
    """
    if len(df_15m) < 25 or len(benchmark_15m) < 25:
        return {"trigger": False}

    df = df_15m.copy()
    df['vwap'] = calculate_vwap(df)
    df['ema9'] = df['close'].ewm(span=9, adjust=False).mean()
    df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['vol_sma20'] = df['volume'].rolling(window=20).mean()
    df['rvol'] = df['volume'] / df['vol_sma20']

    # Relative Strength calculation over 10 periods
    stock_perf = df['close'].iloc[-1] / df['close'].iloc[-10]
    bench_perf = benchmark_15m['close'].iloc[-1] / benchmark_15m['close'].iloc[-10]
    relative_strength = stock_perf / bench_perf

    current = df.iloc[-1]
    prev = df.iloc[-2]

    # Setup conditions
    rs_strong = relative_strength > 1.015
    above_structure = (current['close'] > current['vwap']) and (current['close'] > current['ema20'])
    pullback_zone = min(prev['low'], current['low']) <= current['ema9'] * 1.002
    volume_dry_on_pullback = prev['rvol'] < 1.10
    reversal_trigger = current['close'] > prev['high']

    if rs_strong and above_structure and pullback_zone and volume_dry_on_pullback and reversal_trigger:
        stop_level = min(current['low'], prev['low'])
        risk = current['close'] - stop_level
        return {
            "trigger": True,
            "signal": "BUY_EQUITY_CASH",
            "entry_price": round(current['close'], 2),
            "stop_loss": round(stop_level, 2),
            "target_1_to_2": round(current['close'] + (2 * risk), 2),
            "relative_strength": round(relative_strength, 3)
        }
    return {"trigger": False}
