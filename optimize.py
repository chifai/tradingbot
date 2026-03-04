import pandas as pd
import pandas_ta as ta
import os
from exchange import ExchangeManager

def backtest_with_trailing_stop(df_raw, fast, slow, start_date, trail_percent=0.05):
    # Calculate indicators on FULL data first (Warmup)
    df = df_raw.copy()
    df['fast'] = ta.ema(df['close'], length=fast)
    df['slow'] = ta.ema(df['close'], length=slow)
    
    # Filter for simulation period
    sim_df = df[df['timestamp'] >= start_date].copy()
    
    balance = 1000.0
    position = 0.0
    highest_price = 0
    trades_count = 0
    
    for i in range(1, len(sim_df)):
        curr = sim_df.iloc[i]
        prev = sim_df.iloc[i-1]
        price = curr['close']
        
        # BUY: EMA Crossover
        if position == 0 and prev['fast'] <= prev['slow'] and curr['fast'] > curr['slow']:
            position = balance / price
            balance = 0
            highest_price = price
            trades_count += 1
            
        # SELL: Trailing Stop OR EMA Crossunder
        elif position > 0:
            highest_price = max(highest_price, price)
            stop_loss_price = highest_price * (1 - trail_percent)
            
            # Exit if price drops X% from the peak OR trend reverses
            if price < stop_loss_price or (prev['fast'] >= prev['slow'] and curr['fast'] < curr['slow']):
                balance = position * price
                position = 0
                trades_count += 1
                
    final_val = balance + (position * sim_df.iloc[-1]['close'])
    return final_val, trades_count

def main():
    ex = ExchangeManager()
    start_date = pd.Timestamp('2024-07-01')
    
    # Fetch 5000 candles to ensure deep history for warmup
    ohlcv = ex.fetch_ohlcv('BTC/USDT', '4h', limit=5000)
    df_raw = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df_raw['timestamp'] = pd.to_datetime(df_raw['timestamp'], unit='ms')

    # Calculate Buy & Hold baseline accurately
    sim_period = df_raw[df_raw['timestamp'] >= start_date]
    bh_start = sim_period.iloc[0]['close']
    bh_end = sim_period.iloc[-1]['close']
    bh_ret = ((bh_end - bh_start) / bh_start) * 100
    
    print(f"BASELINE TO BEAT (Buy & Hold): {bh_ret:.2f}%\n")
    
    best_overall = {'val': 0}

    # Search for the best combination of EMA and Trailing Stop
    for fast in [10, 20]:
        for slow in [30, 50, 100]:
            for trail in [0.03, 0.05, 0.07, 0.10]: # 3% to 10% trailing stop
                val, count = backtest_with_trailing_stop(df_raw, fast, slow, start_date, trail)
                ret = ((val - 1000) / 1000) * 100
                
                if val > best_overall.get('val', 0):
                    best_overall = {'val': val, 'ret': ret, 'fast': fast, 'slow': slow, 'trail': trail, 'trades': count}
                
                if ret > bh_ret:
                    print(f"🔥 BEAT THE MARKET! EMA {fast}/{slow} | Trail {trail*100}% | Return: {ret:.2f}%")

    print("\n" + "="*40)
    print("FINAL OPTIMIZED STRATEGY")
    print(f"EMA Fast/Slow: {best_overall['fast']}/{best_overall['slow']}")
    print(f"Trailing Stop: {best_overall['trail']*100}%")
    print(f"Strategy Ret:  {best_overall['ret']:.2f}%")
    print(f"Buy & Hold Ret: {bh_ret:.2f}%")
    print(f"Total Trades:  {best_overall['trades']}")
    print("="*40)

if __name__ == "__main__":
    main()
