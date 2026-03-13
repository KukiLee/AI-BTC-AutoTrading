# BTCUSDT Binance USDⓈ-M Futures Bot (Stage-1 First)

Production-leaning, testnet-first Python bot with strict safety defaults.

## What this bot does
- Stage 1 (default): multi-timeframe analysis (15m trigger, 1h/4h bias), deterministic structure rules, headline scoring filter, risk sizing calculation, Telegram alerts only.
- Stage 2 scaffold ready: testnet order placement, SL/TP support, one-position guard, cooldown and daily loss checks.
- Stage 3 scaffold ready: live mode switch with explicit `ENABLE_LIVE_TRADING=true` requirement.

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

## Execution modes
- `alert_only` (default): never places orders
- `testnet_auto`: requires `BINANCE_TESTNET=true`, can place testnet orders
- `live_auto`: blocked unless `ENABLE_LIVE_TRADING=true`

## Safety warnings
- Do not run live mode without deep validation and production monitoring.
- Position precision normalization is intentionally isolated for Stage-2 hardening.
- News scoring is deterministic keyword-based and should be expanded carefully.

## Strategy summary (v1)
- Bias:
  - LONG: 4h close > 4h MA50 and 1h close > 1h MA20
  - SHORT: 4h close < 4h MA50 and 1h close < 1h MA20
  - Else NEUTRAL -> no trade
- Entry/SL:
  - LONG entry at recent box high, SL below box low with configurable buffer
  - SHORT entry at recent box low, SL above box high with configurable buffer
- TP: fixed RR=2.0
- Filters: chase guard, room check (intermediate S/R), headline risk gate

## Next steps
1. Harden exchange precision handling (`stepSize`, `tickSize`) and leverage/margin mode checks.
2. Add persistent realized PnL -> R tracking after fills/close events.
3. Add integration tests against Binance Futures testnet endpoints.
