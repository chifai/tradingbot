# 🤖 Crypto Trading Bot (EMA Crossover Strategy)

A modular cryptocurrency trading bot built with Python, utilizing the `ccxt` library for exchange connectivity and `pandas-ta` for technical analysis.

## 🚀 Strategy: EMA Crossover (10/50)
The bot uses an Exponential Moving Average (EMA) crossover strategy:
- **Buy Signal (Golden Cross):** When the 10-period EMA crosses above the 50-period EMA.
- **Sell Signal (Death Cross):** When the 10-period EMA crosses below the 50-period EMA.

## 🛠 Setup Instructions

### 1. Clone & Navigate
```bash
cd /Users/chifaiwong/prog/tradingbot
```

### 2. Create and Activate Virtual Environment
```bash
# Create the virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
1. Copy the template file:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` and add your **Binance API Key** and **Secret Key**.
3. Ensure `DRY_RUN=true` for safe testing without real money.

## 📈 Running the Bot

### Live Bot (Dry Run Mode)
This will monitor live market data and log simulated trades based on real-time price action.
```bash
python3 main.py
```

### Backtesting
Test the strategy against historical data (default: 4h timeframe, last 1000 candles).
```bash
python3 backtest.py
```
*The results will be printed to the console and saved to `backtest_4h_results.txt`.*

## 📂 Project Structure
- `main.py`: Core execution loop for live/dry-run trading.
- `backtest.py`: Historical simulation and performance reporting.
- `strategy.py`: EMA crossover logic and indicator calculation.
- `exchange.py`: Unified API wrapper for crypto exchanges (via CCXT).
- `requirements.txt`: Necessary Python libraries.
- `.env`: (Private) Your API credentials and bot settings.

## ⚠️ Disclaimer
This bot is for educational purposes. Cryptocurrency trading involves significant risk. **Always use DRY_RUN=true** until you are confident in your strategy's performance.
