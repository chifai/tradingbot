import os
import ccxt
from dotenv import load_dotenv

load_dotenv()

class ExchangeManager:
    def __init__(self):
        self.exchange_id = os.getenv('EXCHANGE_ID', 'binance')
        self.api_key = os.getenv('API_KEY')
        self.secret_key = os.getenv('SECRET_KEY')
        self.dry_run = os.getenv('DRY_RUN', 'true').lower() == 'true'
        
        # Initialize exchange
        exchange_class = getattr(ccxt, self.exchange_id)
        self.exchange = exchange_class({
            'apiKey': self.api_key,
            'secret': self.secret_key,
            'enableRateLimit': True,
        })
        
        if self.dry_run:
            print(f"--- DRY RUN MODE ENABLED on {self.exchange_id.upper()} ---")

    def fetch_ohlcv(self, symbol, timeframe='1h', limit=100, use_cache=True):
        """Fetches historical candlestick data with robust pagination."""
        cache_filename = f"data/{symbol.replace('/', '_')}_{timeframe}.csv"
        
        if use_cache and os.path.exists(cache_filename):
            import pandas as pd
            df = pd.read_csv(cache_filename)
            if len(df) >= limit:
                print(f"Loading {limit} candles for {symbol} ({timeframe}) from cache...")
                return df.tail(limit).values.tolist()
            print(f"Cache has {len(df)} candles. Need {limit}. Fetching more...")

        print(f"Fetching up to {limit} candles for {symbol} ({timeframe})...")
        
        all_ohlcv = []
        # Calculate approximate start time based on limit
        duration_ms = self.exchange.parse_timeframe(timeframe) * 1000
        since = self.exchange.milliseconds() - (limit * duration_ms)
        
        while len(all_ohlcv) < limit:
            try:
                # Fetch a batch (usually 500-1000 candles)
                new_batch = self.exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=1000)
                if not new_batch:
                    break
                
                # Update 'since' for the next batch to be 1ms after the last candle received
                since = new_batch[-1][0] + 1
                
                # Check for duplicates and add to our list
                for candle in new_batch:
                    if candle not in all_ohlcv:
                        all_ohlcv.append(candle)
                
                print(f"Retrieved {len(all_ohlcv)}/{limit} candles...")
                
                # Safety break if we aren't getting new data
                if len(new_batch) < 100:
                    break
                    
            except Exception as e:
                print(f"Error during pagination: {e}")
                break

        # Trim to the exact limit requested (most recent)
        final_data = all_ohlcv[-limit:]

        # Save to cache
        if use_cache and final_data:
            import pandas as pd
            df = pd.DataFrame(final_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df.to_csv(cache_filename, index=False)
            print(f"Saved {len(df)} candles to {cache_filename}")
            
        return final_data


    def get_balance(self):
        """Fetches account balance."""
        if not self.api_key or not self.secret_key:
            return "API keys not provided."
        try:
            return self.exchange.fetch_balance()
        except Exception as e:
            print(f"Error fetching balance: {e}")
            return None

    def create_order(self, symbol, type, side, amount, price=None):
        """Executes a trade or logs it in dry run mode."""
        if self.dry_run:
            print(f"[DRY RUN] Would place {side} {type} order for {amount} {symbol}")
            return {"status": "dry_run", "symbol": symbol, "side": side, "amount": amount}
        
        try:
            if type == 'market':
                return self.exchange.create_market_order(symbol, side, amount)
            elif type == 'limit':
                return self.exchange.create_limit_order(symbol, side, amount, price)
        except Exception as e:
            print(f"Error placing order: {e}")
            return None
