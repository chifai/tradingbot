import pandas as pd
import pandas_ta as ta

class TradingStrategy:
    def __init__(self, fast_ema=20, slow_ema=50, rsi_period=14, rsi_overbought=70):
        self.fast_ema = fast_ema
        self.slow_ema = slow_ema
        self.rsi_period = rsi_period
        self.rsi_overbought = rsi_overbought

    def generate_signals(self, ohlcv_data):
        """Processes data and returns a signal: 'buy', 'sell', or 'hold'."""
        # Convert OHLCV list to DataFrame
        df = pd.DataFrame(ohlcv_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # Calculate Indicators
        df['EMA_fast'] = ta.ema(df['close'], length=self.fast_ema)
        df['EMA_slow'] = ta.ema(df['close'], length=self.slow_ema)
        df['RSI'] = ta.rsi(df['close'], length=self.rsi_period)
        
        # Get the two most recent rows to check for a crossover
        if len(df) < 2 or df['RSI'].isnull().iloc[-1]:
            return 'hold'
            
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2]
        
        # Bullish Crossover (Golden Cross) + RSI Filter
        # Only BUY if Fast EMA crosses above Slow EMA AND RSI is not overbought (< 70)
        if prev_row['EMA_fast'] <= prev_row['EMA_slow'] and last_row['EMA_fast'] > last_row['EMA_slow']:
            if last_row['RSI'] < self.rsi_overbought:
                return 'buy'
            else:
                print(f"DEBUG: EMA Cross detected but RSI ({last_row['RSI']:.2f}) is too high. Skipping Buy.")
            
        # Bearish Crossover (Death Cross) -> Sell
        # We sell regardless of RSI to protect capital
        elif prev_row['EMA_fast'] >= prev_row['EMA_slow'] and last_row['EMA_fast'] < last_row['EMA_slow']:
            return 'sell'
            
        return 'hold'
