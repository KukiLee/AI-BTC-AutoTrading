# BTCUSDT Binance USDⓈ-M Futures Bot (Stage-1 First)

Production-leaning, safety-first Python bot with staged execution controls.

## Staged execution model
- `alert_only` (**default, safest**): analysis + signal + Telegram alerts only, never places exchange orders.
- `testnet_auto`: attempts automated order flow on Binance USDⓈ-M Futures testnet.
- `live_auto`: disabled by default and blocked unless `ENABLE_LIVE_TRADING=true`.

The architecture is intentionally staged as `alert_only -> testnet_auto -> live_auto`.

## Current readiness and limitations
- Stage 1 signal/alert flow is the primary validated path.
- Automated execution paths include safety guards, precision validation, and mode gates.
- Conditional STOP/TP behavior on Binance USDⓈ-M Futures has migration risk (legacy conditional endpoints vs Algo Service). Current code keeps legacy compatibility path and blocks incomplete algo path safely.
- Real-money/live execution still requires exchange-current endpoint validation before production use.

## Exchange/Testnet notes
- USDⓈ-M Futures testnet REST base URL uses `https://demo-fapi.binance.com/fapi`.
- Exchange precision metadata (`PRICE_FILTER`, `LOT_SIZE`/`MARKET_LOT_SIZE`, and `MIN_NOTIONAL`/`NOTIONAL`) is required for safe auto execution.
- If precision metadata is missing, auto order flow is blocked instead of guessing precision.

## Safety behavior summary
- `alert_only` blocks all order placement.
- `live_auto` requires explicit `ENABLE_LIVE_TRADING=true`.
- `testnet_auto` requires `BINANCE_TESTNET=true`.
- Quantity/price values are normalized against exchange metadata before order payload creation.
- If conditional order placement is rejected (e.g., known migration-style errors), execution fails safely with operational error context.

## Project structure
- `config.py`: validated env config
- `data/`: market/news ingestion
- `indicators/`: MA20/50/200 + RSI14
- `strategy/`: structure, setup rules, news filter, risk, signal builder
- `execution/`: exchange adapter, order manager, position guard/state
- `notifier/`: Telegram sender
- `utils/`: logger/time/formatting/exceptions
- `tests/`: unit tests for strategy/indicator/risk modules

## Setup
```bash
cd bot
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Fill `.env` secrets:
- `BINANCE_API_KEY`, `BINANCE_API_SECRET`
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`

## Run
```bash
cd bot
python main.py
```
