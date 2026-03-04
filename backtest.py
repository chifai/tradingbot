import pandas as pd
import pandas_ta as ta
import os
from exchange import ExchangeManager
from strategy import TradingStrategy
from dotenv import load_dotenv

load_dotenv()

def run_backtest(symbol='BTC/USDT', timeframe='4h', limit=1000):
    print(f"--- Starting Backtest for {symbol} ({timeframe}) ---")
    
    # 1. Fetch Historical Data
    exchange_mgr = ExchangeManager()
    ohlcv = exchange_mgr.fetch_ohlcv(symbol, timeframe, limit=limit)
    
    if not ohlcv:
        print("Failed to fetch historical data.")
        return

    # 2. Prepare DataFrame
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    
    # 3. Apply Strategy Indicators
    strategy = TradingStrategy(fast_ema=10, slow_ema=50)
    df['EMA_fast'] = ta.ema(df['close'], length=strategy.fast_ema)
    df['EMA_slow'] = ta.ema(df['close'], length=strategy.slow_ema)
    
    # 4. Simulate Trades
    balance = 1000.0  # Starting with $1000
    position = 0.0    # Amount of BTC held
    trades = []
    
    for i in range(1, len(df)):
        prev_row = df.iloc[i-1]
        curr_row = df.iloc[i]
        price = curr_row['close']
        
        if pd.isna(prev_row['EMA_slow']) or pd.isna(curr_row['EMA_slow']):
            continue

        # Buy Signal
        if prev_row['EMA_fast'] <= prev_row['EMA_slow'] and curr_row['EMA_fast'] > curr_row['EMA_slow']:
            if balance > 0:
                position = balance / price
                balance = 0
                trades.append({'type': 'BUY', 'price': price, 'time': str(curr_row['timestamp']), 'balance': 0, 'value': position * price})
                print(f"BUY  at {price:.2f} | {curr_row['timestamp']}")

        # Sell Signal
        elif prev_row['EMA_fast'] >= prev_row['EMA_slow'] and curr_row['EMA_fast'] < curr_row['EMA_slow']:
            if position > 0:
                balance = position * price
                position = 0
                trades.append({'type': 'SELL', 'price': price, 'time': str(curr_row['timestamp']), 'balance': balance, 'value': balance})
                print(f"SELL at {price:.2f} | {curr_row['timestamp']}")

    # 5. Final Results
    last_price = df.iloc[-1]['close']
    final_value = balance + (position * last_price)
    total_return = ((final_value - 1000.0) / 1000.0) * 100
    buy_hold_return = ((last_price - df.iloc[0]['close']) / df.iloc[0]['close']) * 100

    summary_text = f"""
==============================
BACKTEST RESULTS
Symbol:           {symbol}
Timeframe:        {timeframe}
Candles:          {len(df)}
Starting Balance: $1000.00
Final Balance:    ${final_value:.2f}
Strategy Return:  {total_return:.2f}%
Buy & Hold Return: {buy_hold_return:.2f}%
Total Trades:     {len(trades)}
==============================
"""
    print(summary_text)

    # 6. Save to Markdown File
    filename = f"backtest_{timeframe}_results.md"
    with open(filename, 'w') as f:
        f.write(f"# 📊 Backtest Results: {symbol} ({timeframe})\n\n")
        f.write("## 📈 Performance Summary\n")
        f.write("| Metric | Value |\n")
        f.write("| :--- | :--- |\n")
        f.write(f"| **Symbol** | {symbol} |\n")
        f.write(f"| **Timeframe** | {timeframe} |\n")
        f.write(f"| **Candles Tested** | {len(df)} |\n")
        f.write(f"| **Starting Balance** | $1,000.00 |\n")
        f.write(f"| **Final Balance** | ${final_value:,.2f} |\n")
        f.write(f"| **Strategy Return** | {total_return:.2f}% |\n")
        f.write(f"| **Buy & Hold Return** | {buy_hold_return:.2f}% |\n")
        f.write(f"| **Total Trades** | {len(trades)} |\n\n")
        
        f.write("## 📜 Detailed Trade Record\n")
        f.write("| Type | Price | Time | Account Value |\n")
        f.write("| :--- | :--- | :--- | :--- |\n")
        for trade in trades:
            f.write(f"| {trade['type']} | {trade['price']:,.2f} | {trade['time']} | ${trade['value']:,.2f} |\n")
    
    print(f"Results saved to {filename}")

if __name__ == "__main__":
    run_backtest()
