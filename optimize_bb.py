import pandas as pd
import pandas_ta as ta
import os
from pyxirr import xirr
from exchange import ExchangeManager

def calculate_xirr(initial_balance, final_balance, start_date, end_date):
    try:
        return xirr([start_date, end_date], [-initial_balance, final_balance]) * 100
    except:
        return 0.0

def test_bb_strategy(df_raw, length, std, start_date):
    df = df_raw.copy()
    bb = ta.bbands(df['close'], length=length, std=std)
    df = pd.concat([df, bb], axis=1)
    
    l_col = [c for c in df.columns if c.startswith('BBL')][0]
    u_col = [c for c in df.columns if c.startswith('BBU')][0]
    
    sim_df = df[df['timestamp'] >= start_date].copy()
    balance, position, trades = 1000.0, 0.0, 0
    
    for i in range(len(sim_df)):
        curr = sim_df.iloc[i]
        price = curr['close']
        
        if position == 0 and price < curr[l_col]:
            position = balance / price
            balance = 0
            trades += 1
        elif position > 0 and price > curr[u_col]:
            balance = position * price
            position = 0
            trades += 1
            
    final_val = balance + (position * sim_df.iloc[-1]['close'])
    return final_val, trades

def main():
    ex = ExchangeManager()
    start_date = pd.Timestamp('2024-07-01')
    ohlcv = ex.fetch_ohlcv('BTC/USDT', '4h', limit=4500)
    df_raw = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df_raw['timestamp'] = pd.to_datetime(df_raw['timestamp'], unit='ms')
    
    bh_start = df_raw[df_raw['timestamp'] >= start_date].iloc[0]['close']
    bh_end = df_raw.iloc[-1]['close']
    bh_ret = ((bh_end - bh_start) / bh_start) * 100
    
    print(f"600-Day Baseline (Buy & Hold): {bh_ret:.2f}%\n")
    print(f"{'Len':<5} | {'Std':<5} | {'Final Value':<12} | {'Return %':<10} | {'Trades':<6}")
    print("-" * 50)
    
    best_overall = {'val': 0}
    
    for length in [10, 20, 30, 50]:
        for std in [1.5, 2.0, 2.5, 3.0]:
            val, count = test_bb_strategy(df_raw, length, std, start_date)
            ret = ((val - 1000) / 1000) * 100
            
            print(f"{length:<5} | {std:<5} | ${val:<11.2f} | {ret:<9.2f}% | {count:<6}")
            
            if val > best_overall['val']:
                best_overall = {'val': val, 'ret': ret, 'len': length, 'std': std, 'trades': count}

    print("\n" + "="*40)
    print("BEST BOLLINGER BANDS SETTINGS")
    print(f"Length: {best_overall['len']} | StdDev: {best_overall['std']}")
    print(f"Strategy Return: {best_overall['ret']:.2f}%")
    print(f"Total Trades:    {best_overall['trades']}")
    print("="*40)

if __name__ == "__main__":
    main()
