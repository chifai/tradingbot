import pandas as pd
import pandas_ta as ta
import os
from pyxirr import xirr
from datetime import datetime
from exchange import ExchangeManager

def calculate_performance(initial_balance, final_balance, start_date, end_date):
    """Calculates XIRR for the given period."""
    try:
        # Cash flows: negative at start, positive at end
        dates = [start_date, end_date]
        flows = [-initial_balance, final_balance]
        return xirr(dates, flows) * 100 # Return as percentage
    except:
        return 0.0

def run_simulation(df, strategy_func, initial_balance=1000.0):
    """Runs a backtest loop for a given strategy function."""
    balance = initial_balance
    position = 0.0
    trades_count = 0
    highest_price = 0.0
    
    for i in range(1, len(df)):
        curr = df.iloc[i]
        prev = df.iloc[i-1]
        
        signal = strategy_func(curr, prev, position > 0)
        
        if signal == 'buy' and balance > 0:
            position = balance / curr['close']
            balance = 0
            trades_count += 1
        elif signal == 'sell' and position > 0:
            balance = position * curr['close']
            position = 0
            trades_count += 1
            
    final_val = balance + (position * df.iloc[-1]['close'])
    return final_val, trades_count

def main():
    ex = ExchangeManager()
    symbol = 'BTC/USDT'
    timeframe = '4h'
    # 5 years of 4h data is ~11,000 candles
    limit = 11000
    
    print(f"--- Fetching 5 Years of Data for {symbol} ({timeframe}) ---")
    ohlcv = ex.fetch_ohlcv(symbol, timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    
    start_date = df.iloc[0]['timestamp']
    end_date = df.iloc[-1]['timestamp']
    
    # Baseline: Buy & Hold
    bh_val = (1000.0 / df.iloc[0]['close']) * df.iloc[-1]['close']
    bh_xirr = calculate_performance(1000.0, bh_val, start_date, end_date)
    
    print(f"Baseline (Buy & Hold) XIRR: {bh_xirr:.2f}%")
    print("-" * 40)

    strategies = []

    # 1. EMA Crossovers
    for fast, slow in [(10, 50), (20, 50), (50, 200), (30, 70)]:
        df[f'ema_{fast}'] = ta.ema(df['close'], length=fast)
        df[f'ema_{slow}'] = ta.ema(df['close'], length=slow)
        
        def ema_strat(curr, prev, has_pos, f=fast, s=slow):
            if not has_pos and prev[f'ema_{f}'] <= prev[f'ema_{s}'] and curr[f'ema_{f}'] > curr[f'ema_{s}']:
                return 'buy'
            if has_pos and prev[f'ema_{f}'] >= prev[f'ema_{s}'] and curr[f'ema_{f}'] < curr[f'ema_{s}']:
                return 'sell'
            return 'hold'
        
        val, count = run_simulation(df, ema_strat)
        strat_xirr = calculate_performance(1000.0, val, start_date, end_date)
        strategies.append({'name': f'EMA {fast}/{slow}', 'xirr': strat_xirr, 'val': val, 'trades': count})

    # 2. MACD
    macd = ta.macd(df['close'])
    df = pd.concat([df, macd], axis=1)
    def macd_strat(curr, prev, has_pos):
        if not has_pos and prev['MACD_12_26_9'] <= prev['MACDs_12_26_9'] and curr['MACD_12_26_9'] > curr['MACDs_12_26_9']:
            return 'buy'
        if has_pos and prev['MACD_12_26_9'] >= prev['MACDs_12_26_9'] and curr['MACD_12_26_9'] < curr['MACDs_12_26_9']:
            return 'sell'
        return 'hold'
    
    val, count = run_simulation(df, macd_strat)
    strategies.append({'name': 'MACD (12,26,9)', 'xirr': calculate_performance(1000.0, val, start_date, end_date), 'val': val, 'trades': count})

    # 3. Bollinger Bands Mean Reversion
    bbands = ta.bbands(df['close'], length=20, std=2)
    df = pd.concat([df, bbands], axis=1)
    
    # Debug: Print columns to find correct names
    # print(df.columns) 
    # Usually: BBL_20_2.0, BBM_20_2.0, BBU_20_2.0
    # But sometimes periods/std are formatted differently.
    
    l_col = [c for c in df.columns if c.startswith('BBL')][0]
    u_col = [c for c in df.columns if c.startswith('BBU')][0]

    def bb_strat(curr, prev, has_pos, l=l_col, u=u_col):
        if not has_pos and curr['close'] < curr[l]: return 'buy'
        if has_pos and curr['close'] > curr[u]: return 'sell'
        return 'hold'
    
    val, count = run_simulation(df, bb_strat)
    strategies.append({'name': 'Bollinger Bands', 'xirr': calculate_performance(1000.0, val, start_date, end_date), 'val': val, 'trades': count})

    # Report Results
    print(f"{'Strategy':<20} | {'XIRR (%)':<10} | {'Final Value':<12} | {'Trades':<6}")
    print("-" * 60)
    
    for s in sorted(strategies, key=lambda x: x['xirr'], reverse=True):
        status = "🔥" if s['xirr'] > bh_xirr else "  "
        print(f"{status} {s['name']:<18} | {s['xirr']:<10.2f} | ${s['val']:<11.2f} | {s['trades']:<6}")
        
        # Export individual report if worth noting (XIRR > 10% or beats BH)
        if s['xirr'] > 10 or s['xirr'] > bh_xirr:
            filename = f"report_5yr_{s['name'].replace(' ', '_').replace('/', '_')}.md"
            with open(filename, 'w') as f:
                f.write(f"# 📊 5-Year Backtest: {s['name']}\n\n")
                f.write(f"| Metric | Value |\n| :--- | :--- |\n")
                f.write(f"| **XIRR (Annualized)** | **{s['xirr']:.2f}%** |\n")
                f.write(f"| **Final Balance** | ${s['val']:.2f} |\n")
                f.write(f"| **Total Trades** | {s['trades']} |\n")
                f.write(f"| **Buy & Hold XIRR** | {bh_xirr:.2f}% |\n")
            print(f"Generated report: {filename}")

if __name__ == "__main__":
    main()
