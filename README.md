
# AI Trading Bot (Pro Starter) — Coinbase + Alpaca + Alerts

Use this to run signals, backtest, and place paper trades on **Alpaca** or sandbox/live trades on **Coinbase Advanced Trade**.
It includes Discord and Telegram alerts.

## Quick Start
1) Install Python 3.10+
2) In the project folder:
```
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
```
3) Copy `.env.example` → `.env` and fill keys:
   - For Coinbase sandbox: set `COINBASE_SANDBOX=true` and add API key/secret
   - For Alpaca paper: set `ALPACA_PAPER=true` and add API key/secret
   - Optional: set `DISCORD_WEBHOOK_URL` and/or `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID`

## Run
- Dry run (no orders), Coinbase candles, crypto:
```
python run.py --broker coinbase --product BTC-USD --timeframe 1m --dry
```
- Coinbase sandbox paper trade:
```
python run.py --broker coinbase --product BTC-USD --timeframe 1m --sandbox
```
- Alpaca paper trade (stocks/crypto supported by Alpaca symbol, e.g., AAPL or BTCUSD):
```
python run.py --broker alpaca --product AAPL --timeframe 1Min --paper
```
- Backtest CSV:
```
python backtest.py --csv sample_data.csv
```

## Notes
- Robinhood: no stable public API; use Alpaca for equities automation.
- Educational starter. Extend and validate before using with real money.
