# BTCUSDT Binance USDⓈ-M Futures Bot (Hybrid Baseline + AI-Ready Data Layer)

Production-leaning, safety-first Python bot with staged execution controls.

## Staged execution model
- `alert_only` (**default, safest**): analysis + signal + Telegram alerts only, never places exchange orders.
- `testnet_auto`: attempts automated order flow on Binance USDⓈ-M Futures testnet.
- `live_auto`: disabled by default and blocked unless `ENABLE_LIVE_TRADING=true`.

The rollout remains: `alert_only -> testnet_auto -> live_auto`.

## Hybrid architecture (safe-by-default)
1. **Deterministic baseline engine (authoritative)**
   - HTF bias (1h/4h), retest-first entry, room check, chase filter, news filter, RR 1:2.
   - Baseline remains source-of-truth execution logic.
2. **Structured setup logging**
   - Every evaluated setup (including `NO_TRADE`) is transformed into a feature row and logged.
   - Stable `setup_id` enables joining setup rows with later outcome labels.
3. **AI evaluation layer (shadow-first)**
   - AI evaluator scores setup quality and recommendation only.
   - AI cannot place orders, create new trades, or override hard risk constraints.
4. **Outcome labeling scaffold**
   - TP-first / SL-first / unresolved labels with MFE/MAE and bars-to-outcome interface.

## AI constraints (non-negotiable)
- AI does **not** create arbitrary trade direction/entry universe.
- AI does **not** set leverage, remove SL/TP constraints, or bypass hard blockers.
- Default mode is `AI_EVALUATION_MODE=shadow`: baseline still decides execution.
- `filter_testnet` can only **block** baseline `READY` setups and only in `testnet_auto`.
- Live AI filtering is blocked by default unless `ENABLE_AI_LIVE_OVERRIDE=true`.

## Dataset outputs
When enabled, files are written to `DATASET_DIR`:
- `setups_YYYY-MM-DD.jsonl`
- `ai_evals_YYYY-MM-DD.jsonl`
- `outcomes_YYYY-MM-DD.jsonl` (future/outcome hook usage)

Write failures are fail-soft (bot continues trading/alerting and logs the error).

## Project structure
- `config.py`: validated env config
- `data/`: market/news ingestion
- `indicators/`: MA20/50/200 + RSI14
- `strategy/`: structure, setup rules, news filter, risk, signal builder
- `intelligence/`: feature builder, evaluator, policy, outcome labeler
- `storage/`: schemas, dataset writer, trade logger
- `execution/`: exchange adapter, order manager, position guard/state
- `notifier/`: Telegram sender
- `utils/`: logger/time/formatting/exceptions
- `tests/`: unit tests for strategy + intelligence/storage scaffolding

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

## Safety-first rollout plan
1. Start with `EXECUTION_MODE=alert_only`, `AI_EVALUATION_MODE=shadow`.
2. Validate logs/datasets and AI-vs-baseline diagnostics.
3. Move to `testnet_auto` baseline execution.
4. Optionally test `AI_EVALUATION_MODE=filter_testnet` only after shadow validation.
5. Keep `live_auto` baseline-authoritative unless explicit, audited override is enabled.
