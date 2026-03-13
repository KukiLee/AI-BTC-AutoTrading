# BTCUSDT Binance USDⓈ-M Futures Bot (Stage-1 First)

Production-leaning, testnet-first Python bot with strict safety defaults.

## What this bot does
- Stage 1 (default): multi-timeframe analysis, deterministic structure rules, headline scoring filter, risk sizing calculation, Telegram alerts only.
- Stage 2 patch in progress: testnet order placement, precision normalization, conditional-order routing split(legacy/algo placeholder), cooldown and daily loss checks.

## Exchange/Testnet notes
- USDⓈ-M Futures testnet REST base URL is configured as `https://demo-fapi.binance.com/fapi`.
- `alert_only` is safest default and never sends orders.
- `testnet_auto` can place testnet orders (and uses test-order dry-run for entry by default path).
- `live_auto` is blocked unless `ENABLE_LIVE_TRADING=true`.

## Safety warnings
- If symbol precision metadata is missing, auto order flow is blocked.
- Conditional order endpoint behavior changed on Binance side (Algo Service migration); verify latest production endpoint behavior before real-money deployment.
- Live trading is not enabled by default.

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
