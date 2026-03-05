import pandas as pd
import pandas_ta as ta
import os
import argparse
from exchange import ExchangeManager
from strategy import TradingStrategy
from dotenv import load_dotenv

load_dotenv()

def strategy_ema_trailing(df, i, position, highest_price, strategy_obj):
    """Strategy 1: EMA Crossover with 5% Trailing Stop."""
    curr = df.iloc[i]
    prev = df.iloc[i-1]
    price = curr['close']
    
    # Sell Logic
    if position > 0:
        highest_price = max(highest_price, price)
        stop_loss_price = highest_price * (1 - strategy_obj.trailing_stop)
        
        if price < stop_loss_price or (prev['EMA_fast'] >= prev['EMA_slow'] and curr['EMA_fast'] < curr['EMA_slow']):
            return 'sell', highest_price
            
    # Buy Logic
    elif position == 0:
        if prev['EMA_fast'] <= prev['EMA_slow'] and curr['EMA_fast'] > curr['EMA_slow']:
            if curr['RSI'] < strategy_obj.rsi_overbought:
                return 'buy', price
                
    return 'hold', highest_price

def strategy_bollinger_bands(df, i, position, highest_price, strategy_obj):
    """Strategy 2: Bollinger Bands Mean Reversion."""
    curr = df.iloc[i]
    price = curr['close']
    
    # Get BB column names
    l_col = [c for c in df.columns if c.startswith('BBL')][0]
    u_col = [c for c in df.columns if c.startswith('BBU')][0]
    
    if position == 0 and price < curr[l_col]:
        return 'buy', price
    elif position > 0 and price > curr[u_col]:
        return 'sell', 0
        
    return 'hold', highest_price

def save_markdown_report(filename, symbol, timeframe, strategy_name, config_lines, summary, trades):
    """Standardized function to write backtest results to Markdown."""
    with open(filename, 'w') as f:
        f.write(f"# 📊 Backtest Results: {symbol} ({timeframe})\n\n")
        
        f.write("## 🛠 Strategy Configuration\n")
        f.write(f"- **Strategy:** {strategy_name}\n")
        for line in config_lines:
            f.write(f"- {line}\n")
        f.write("\n")

        f.write("## 📈 Performance Summary\n")
        f.write("| Metric | Value |\n| :--- | :--- |\n")
        for key, val in summary.items():
            f.write(f"| **{key}** | {val} |\n")
        f.write("\n")
        
        f.write("## 📜 Detailed Trade Record\n")
        f.write("| Type | Price | Time | Account Value |\n")
        f.write("| :--- | :--- | :--- | :--- |\n")
        for t in trades:
            f.write(f"| {t['type']} | {t['price']:,.2f} | {t['time']} | ${t['value']:,.2f} |\n")
    print(f"Results saved to {filename}")

def run_backtest(strategy_id=1, symbol='BTC/USDT', timeframe='4h', limit=4500):
    print(f"--- Starting Backtest (Strategy {strategy_id}) for {symbol} ({timeframe}) ---")
    
    ex = ExchangeManager()
    ohlcv = ex.fetch_ohlcv(symbol, timeframe, limit=limit)
    if not ohlcv: return

    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    
    # Prepare Indicators
    strategy_obj = TradingStrategy() # Default 10/100/5%
    df['EMA_fast'] = ta.ema(df['close'], length=strategy_obj.fast_ema)
    df['EMA_slow'] = ta.ema(df['close'], length=strategy_obj.slow_ema)
    df['RSI'] = ta.rsi(df['close'], length=strategy_obj.rsi_period)
    bb = ta.bbands(df['close'], length=20, std=1.5)
    df = pd.concat([df, bb], axis=1)
    
    # Simulation Vars
    balance, position, highest_price = 1000.0, 0.0, 0.0
    trades = []
    start_date = pd.Timestamp('2024-07-01')
    
    # Select Strategy Function
    strat_func = strategy_ema_trailing if strategy_id == 1 else strategy_bollinger_bands
    strat_name = "EMA 10/100 + 5% Trailing Stop" if strategy_id == 1 else "Bollinger Bands Mean Reversion"
    config = [f"EMA Fast: {strategy_obj.fast_ema}", f"EMA Slow: {strategy_obj.slow_ema}", "Trail: 5%"] if strategy_id == 1 else ["Length: 20", "StdDev: 1.5"]

    for i in range(1, len(df)):
        if df.iloc[i]['timestamp'] < start_date or pd.isna(df.iloc[i]['EMA_slow']): continue
        
        signal, highest_price = strat_func(df, i, position, highest_price, strategy_obj)
        price = df.iloc[i]['close']
        
        if signal == 'buy' and balance > 0:
            position = balance / price
            balance = 0
            trades.append({'type': 'BUY', 'price': price, 'time': str(df.iloc[i]['timestamp']), 'value': position * price})
        elif signal == 'sell' and position > 0:
            balance = position * price
            position = 0
            trades.append({'type': 'SELL', 'price': price, 'time': str(df.iloc[i]['timestamp']), 'value': balance})

    # Results
    last_price = df.iloc[-1]['close']
    final_val = balance + (position * last_price)
    ret = ((final_val - 1000.0) / 1000.0) * 100
    bh_ret = ((last_price - df[df['timestamp'] >= start_date].iloc[0]['close']) / df[df['timestamp'] >= start_date].iloc[0]['close']) * 100
    
    summary = {
        "Strategy Return": f"**{ret:.2f}%**",
        "Buy & Hold Return": f"{bh_ret:.2f}%",
        "Final Balance": f"${final_val:,.2f}",
        "Total Trades": len(trades)
    }
    
    filename = f"backtest_strat{strategy_id}_{timeframe}.md"
    save_markdown_report(filename, symbol, timeframe, strat_name, config, summary, trades)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--strategy', type=int, default=1, choices=[1, 2], help='1: EMA Trailing, 2: Bollinger Bands')
    args = parser.parse_args()
    run_backtest(strategy_id=args.strategy)
