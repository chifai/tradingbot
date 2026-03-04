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

    def fetch_ohlcv(self, symbol, timeframe='1h', limit=100):
        """Fetches historical candlestick data."""
        try:
            return self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        except Exception as e:
            print(f"Error fetching OHLCV: {e}")
            return None

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
