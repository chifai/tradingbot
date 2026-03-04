import pandas as pd
import pandas_ta as ta
import os
from exchange import ExchangeManager
from strategy import TradingStrategy
from dotenv import load_dotenv

load_dotenv()

def run_backtest(symbol='BTC/USDT', timeframe='4h', limit=4500):
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
    strategy = TradingStrategy(fast_ema=10, slow_ema=100, trailing_stop=0.05)
    df['EMA_fast'] = ta.ema(df['close'], length=strategy.fast_ema)
    df['EMA_slow'] = ta.ema(df['close'], length=strategy.slow_ema)
    df['RSI'] = ta.rsi(df['close'], length=strategy.rsi_period)
    
    # 4. Simulate Trades
    balance = 1000.0
    position = 0.0
    highest_price = 0.0
    trades = []
    
    # Filter to start exactly on July 1, 2024
    start_date = pd.Timestamp('2024-07-01')
    
    for i in range(1, len(df)):
        prev_row = df.iloc[i-1]
        curr_row = df.iloc[i]
        price = curr_row['close']
        
        if curr_row['timestamp'] < start_date:
            continue
            
        # SELL LOGIC (Check this first if we have a position)
        if position > 0:
            highest_price = max(highest_price, price)
            stop_loss_price = highest_price * (1 - strategy.trailing_stop)
            
            # EXIT: Trailing Stop OR EMA Crossunder
            if price < stop_loss_price or (prev_row['EMA_fast'] >= prev_row['EMA_slow'] and curr_row['EMA_fast'] < curr_row['EMA_slow']):
                balance = position * price
                position = 0
                trades.append({'type': 'SELL', 'price': price, 'time': str(curr_row['timestamp']), 'value': balance})
                print(f"SELL at {price:.2f} | {curr_row['timestamp']} | Value: ${balance:.2f}")
                continue

        # BUY LOGIC
        if position == 0 and balance > 0:
            # Entry: Golden Cross + RSI Filter
            if prev_row['EMA_fast'] <= prev_row['EMA_slow'] and curr_row['EMA_fast'] > curr_row['EMA_slow']:
                if curr_row['RSI'] < strategy.rsi_overbought:
                    position = balance / price
                    balance = 0
                    highest_price = price
                    trades.append({'type': 'BUY', 'price': price, 'time': str(curr_row['timestamp']), 'value': position * price})
                    print(f"BUY  at {price:.2f} | {curr_row['timestamp']} | RSI: {curr_row['RSI']:.2f}")

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
Strategy:         EMA ({strategy.fast_ema}/{strategy.slow_ema}) + RSI (<{strategy.rsi_overbought})
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
        
        f.write("## 🛠 Strategy Configuration\n")
        f.write(f"- **Strategy:** EMA Crossover + RSI Filter\n")
        f.write(f"- **EMA Fast:** {strategy.fast_ema} | **EMA Slow:** {strategy.slow_ema}\n")
        f.write(f"- **RSI Period:** {strategy.rsi_period} | **Buy Threshold:** < {strategy.rsi_overbought}\n\n")

        f.write("## 📈 Performance Summary\n")
        f.write("| Metric | Value |\n")
        f.write("| :--- | :--- |\n")
        f.write(f"| **Symbol** | {symbol} |\n")
        f.write(f"| **Timeframe** | {timeframe} |\n")
        f.write(f"| **Strategy Return** | **{total_return:.2f}%** |\n")
        f.write(f"| **Buy & Hold Return** | {buy_hold_return:.2f}% |\n")
        f.write(f"| **Final Balance** | ${final_value:,.2f} |\n")
        f.write(f"| **Total Trades** | {len(trades)} |\n\n")
        
        f.write("## 📜 Detailed Trade Record\n")
        f.write("| Type | Price | Time | Account Value |\n")
        f.write("| :--- | :--- | :--- | :--- |\n")
        for trade in trades:
            f.write(f"| {trade['type']} | {trade['price']:,.2f} | {trade['time']} | ${trade['value']:,.2f} |\n")
    
    print(f"Results saved to {filename}")

if __name__ == "__main__":
    run_backtest()
