import pandas as pd
import pandas_ta as ta

class TradingStrategy:
    def __init__(self, fast_ema=10, slow_ema=50):
        self.fast_ema = fast_ema
        self.slow_ema = slow_ema

    def generate_signals(self, ohlcv_data):
        """Processes data and returns a signal: 'buy', 'sell', or 'hold'."""
        # Convert OHLCV list to DataFrame
        df = pd.DataFrame(ohlcv_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # Calculate EMAs
        df['EMA_fast'] = ta.ema(df['close'], length=self.fast_ema)
        df['EMA_slow'] = ta.ema(df['close'], length=self.slow_ema)
        
        # Get the two most recent rows to check for a crossover
        if len(df) < 2:
            return 'hold'
            
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2]
        
        # Bullish Crossover (Golden Cross) -> Buy
        if prev_row['EMA_fast'] <= prev_row['EMA_slow'] and last_row['EMA_fast'] > last_row['EMA_slow']:
            return 'buy'
            
        # Bearish Crossover (Death Cross) -> Sell
        elif prev_row['EMA_fast'] >= prev_row['EMA_slow'] and last_row['EMA_fast'] < last_row['EMA_slow']:
            return 'sell'
            
        return 'hold'
