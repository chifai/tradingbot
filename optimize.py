import pandas as pd
import pandas_ta as ta
import os
from exchange import ExchangeManager
from strategy import TradingStrategy

def test_strategy(df, fast, slow, rsi_filter=70):
    balance = 1000.0
    position = 0.0
    trades = []
    
    # Calculate indicators
    df['fast'] = ta.ema(df['close'], length=fast)
    df['slow'] = ta.ema(df['close'], length=slow)
    df['rsi'] = ta.rsi(df['close'], length=14)
    
    for i in range(1, len(df)):
        prev = df.iloc[i-1]
        curr = df.iloc[i]
        
        if pd.isna(curr['slow']): continue
        
        # BUY Logic: Crossover + RSI filter
        if prev['fast'] <= prev['slow'] and curr['fast'] > curr['slow']:
            if curr['rsi'] < rsi_filter and balance > 0:
                position = balance / curr['close']
                balance = 0
                trades.append(curr['close'])
        
        # SELL Logic: Crossunder
        elif prev['fast'] >= prev['slow'] and curr['fast'] < curr['slow']:
            if position > 0:
                balance = position * curr['close']
                position = 0
                trades.append(curr['close'])
                
    final_value = balance + (position * df.iloc[-1]['close'])
    return final_value, len(trades)

def main():
    exchange_mgr = ExchangeManager()
    # Fetch a large dataset
    ohlcv = exchange_mgr.fetch_ohlcv('BTC/USDT', '4h', limit=4500)
    df_all = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df_all['timestamp'] = pd.to_datetime(df_all['timestamp'], unit='ms')
    
    # Filter for July 1, 2024
    start_date = pd.Timestamp('2024-07-01')
    df = df_all[df_all['timestamp'] >= start_date].copy()
    
    buy_hold_price_start = df.iloc[0]['close']
    buy_hold_price_end = df.iloc[-1]['close']
    buy_hold_return = ((buy_hold_price_end - buy_hold_price_start) / buy_hold_price_start) * 100
    
    print(f"Target: Beat Buy & Hold Return of {buy_hold_return:.2f}%\n")
    print(f"{'Fast':<5} | {'Slow':<5} | {'Final Value':<12} | {'Return %':<10} | {'Trades':<6}")
    print("-" * 50)
    
    best_value = 0
    best_params = (0, 0)
    
    # Brute force search for the best EMA combination
    for fast in [5, 9, 12, 20, 30]:
        for slow in [40, 50, 70, 100, 200]:
            if fast >= slow: continue
            
            val, count = test_strategy(df.copy(), fast, slow)
            ret = ((val - 1000) / 1000) * 100
            
            print(f"{fast:<5} | {slow:<5} | ${val:<11.2f} | {ret:<9.2f}% | {count:<6}")
            
            if val > best_value:
                best_value = val
                best_params = (fast, slow)
    
    print("\n" + "="*30)
    print(f"BEST STRATEGY FOUND:")
    print(f"EMA Fast: {best_params[0]}")
    print(f"EMA Slow: {best_params[1]}")
    print(f"Final Value: ${best_value:.2f}")
    print(f"Strategy Return: {((best_value-1000)/1000)*100:.2f}%")
    print(f"Buy & Hold Return: {buy_hold_return:.2f}%")
    print("="*30)

if __name__ == "__main__":
    main()
