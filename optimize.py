import pandas as pd
import pandas_ta as ta
import os
import math
from exchange import ExchangeManager

def backtest(df, fast, slow, rsi_buy=70):
    balance = 1000.0
    position = 0.0
    trades_count = 0
    
    # Indicators
    df['fast'] = ta.ema(df['close'], length=fast)
    df['slow'] = ta.ema(df['close'], length=slow)
    df['rsi'] = ta.rsi(df['close'], length=14)
    
    for i in range(1, len(df)):
        prev = df.iloc[i-1]
        curr = df.iloc[i]
        
        if pd.isna(curr['slow']) or pd.isna(curr['rsi']): continue
        
        # BUY: Fast crosses Slow AND RSI is not overbought
        if prev['fast'] <= prev['slow'] and curr['fast'] > curr['slow']:
            if curr['rsi'] < rsi_buy and balance > 0:
                position = balance / curr['close']
                balance = 0
                trades_count += 1
        
        # SELL: Fast crosses below Slow
        elif prev['fast'] >= prev['slow'] and curr['fast'] < curr['slow']:
            if position > 0:
                balance = position * curr['close']
                position = 0
                trades_count += 1
                
    final_val = balance + (position * df.iloc[-1]['close'])
    return final_val, trades_count

def main():
    ex = ExchangeManager()
    start_date = pd.Timestamp('2024-07-01')
    best_overall = {'val': 0}

    # Test multiple timeframes
    for tf in ['1h', '4h']:
        print(f"\n--- Optimizing for Timeframe: {tf} ---")
        ohlcv = ex.fetch_ohlcv('BTC/USDT', tf, limit=10000) # Fetch max possible
        df_raw = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df_raw['timestamp'] = pd.to_datetime(df_raw['timestamp'], unit='ms')
        df = df_raw[df_raw['timestamp'] >= start_date].copy()
        
        bh_start = df.iloc[0]['close']
        bh_end = df.iloc[-1]['close']
        bh_ret = ((bh_end - bh_start) / bh_start) * 100
        print(f"Buy & Hold Return ({tf}): {bh_ret:.2f}%")

        # Test EMA combinations
        for fast in [10, 20, 30, 50]:
            for slow in [50, 100, 200]:
                if fast >= slow: continue
                
                # Test different RSI filters
                for rsi in [70, 80, 90]:
                    val, count = backtest(df.copy(), fast, slow, rsi)
                    ret = ((val - 1000) / 1000) * 100
                    
                    if val > best_overall['val']:
                        best_overall = {
                            'val': val, 'ret': ret, 'tf': tf, 
                            'fast': fast, 'slow': slow, 'rsi': rsi, 
                            'trades': count, 'bh': bh_ret
                        }
                    
                    # Log progress for high performers
                    if ret > bh_ret:
                        print(f"WINNER! EMA {fast}/{slow} | RSI {rsi} | Return: {ret:.2f}% (Trades: {count})")

    print("\n" + "="*40)
    print("FINAL OPTIMIZED STRATEGY FOUND")
    print(f"Timeframe:     {best_overall['tf']}")
    print(f"EMA Fast:      {best_overall['fast']}")
    print(f"EMA Slow:      {best_overall['slow']}")
    print(f"RSI Filter:    <{best_overall['rsi']}")
    print(f"Strategy Ret:  {best_overall['ret']:.2f}%")
    print(f"Buy & Hold Ret: {best_overall['bh']:.2f}%")
    print(f"Total Trades:  {best_overall['trades']}")
    print("="*40)

if __name__ == "__main__":
    main()
