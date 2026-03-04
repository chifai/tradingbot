import pandas as pd
import pandas_ta as ta

class TradingStrategy:
    def __init__(self, fast_ema=50, slow_ema=200, rsi_period=14, rsi_overbought=70):
        self.fast_ema = fast_ema
        self.slow_ema = slow_ema
        self.rsi_period = rsi_period
        self.rsi_overbought = rsi_overbought

    def generate_signals(self, ohlcv_data):
        """Processes data and returns a signal: 'buy', 'sell', or 'hold'."""
        df = pd.DataFrame(ohlcv_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # Calculate Indicators
        df['EMA_fast'] = ta.ema(df['close'], length=self.fast_ema)
        df['EMA_slow'] = ta.ema(df['close'], length=self.slow_ema)
        df['RSI'] = ta.rsi(df['close'], length=self.rsi_period)
        
        if len(df) < 2 or df['RSI'].isnull().iloc[-1]:
            return 'hold'
            
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2]
        
        # BUY: Fast EMA crosses above Slow EMA AND RSI < 70
        if prev_row['EMA_fast'] <= prev_row['EMA_slow'] and last_row['EMA_fast'] > last_row['EMA_slow']:
            if last_row['RSI'] < self.rsi_overbought:
                return 'buy'
            
        # SELL: Fast EMA crosses below Slow EMA (Crossover Exit)
        elif prev_row['EMA_fast'] >= prev_row['EMA_slow'] and last_row['EMA_fast'] < last_row['EMA_slow']:
            return 'sell'
            
        return 'hold'
