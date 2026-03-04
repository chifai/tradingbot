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

    # 6. Save to File
    filename = f"backtest_{timeframe}_results.txt"
    with open(filename, 'w') as f:
        f.write(summary_text)
        f.write("\nDETAILED TRADE RECORD:\n")
        f.write(f"{'Type':<10} | {'Price':<12} | {'Time':<25} | {'Account Value':<15}\n")
        f.write("-" * 70 + "\n")
        for trade in trades:
            f.write(f"{trade['type']:<10} | {trade['price']:<12.2f} | {trade['time']:<25} | ${trade['value']:<15.2f}\n")
    
    print(f"Results saved to {filename}")

if __name__ == "__main__":
    run_backtest()
