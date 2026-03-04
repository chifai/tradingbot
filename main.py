import time
import os
from exchange import ExchangeManager
from strategy import TradingStrategy
from dotenv import load_dotenv

load_dotenv()

def main():
    # Configuration
    symbol = os.getenv('SYMBOL', 'BTC/USDT')
    timeframe = os.getenv('TIMEFRAME', '1h')
    
    # Initialize components
    exchange_mgr = ExchangeManager()
    strategy = TradingStrategy(fast_ema=10, slow_ema=50)
    
    print(f"Starting bot for {symbol} on {timeframe} timeframe...")
    
    current_position = None # Simplistic state management: None, 'long'

    while True:
        try:
            # 1. Fetch data
            ohlcv = exchange_mgr.fetch_ohlcv(symbol, timeframe)
            if not ohlcv:
                time.sleep(30)
                continue
                
            # 2. Analyze strategy
            signal = strategy.generate_signals(ohlcv)
            last_price = ohlcv[-1][4]
            
            print(f"Checking {symbol} | Price: {last_price} | Signal: {signal} | Position: {current_position}")
            
            # 3. Execute trades
            if signal == 'buy' and current_position != 'long':
                print(f"--- EXECUTE BUY SIGNAL at {last_price} ---")
                # In a real bot, you'd calculate amount based on balance
                exchange_mgr.create_order(symbol, 'market', 'buy', 0.001) 
                current_position = 'long'
                
            elif signal == 'sell' and current_position == 'long':
                print(f"--- EXECUTE SELL SIGNAL at {last_price} ---")
                exchange_mgr.create_order(symbol, 'market', 'sell', 0.001)
                current_position = None
                
            # Wait for next cycle (e.g., check every 1 minute)
            time.sleep(60)
            
        except KeyboardInterrupt:
            print("\nBot stopped by user.")
            break
        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
