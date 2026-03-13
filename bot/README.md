# BTCUSDT Binance USDⓈ-M Futures Bot (Deterministic Baseline + Constrained AI Testnet)

## Core philosophy
- Deterministic baseline remains intact and benchmark-authoritative.
- AI is constrained to score/filter/select only inside pre-defined BTCUSDT setup candidates.
- No unconstrained autonomous trading.
- Live trading is still disabled by default.

## Policy modes
- `baseline_alert_only` (default): baseline analysis + alerts, no orders.
- `baseline_testnet_auto`: baseline READY signals execute on testnet.
- `ai_shadow`: baseline executes normally, AI only logs diagnostics.
- `ai_filter_testnet`: AI may block baseline READY on testnet, never promotes NO_TRADE.
- `ai_testnet_auto`: AI may choose one allowed candidate (or no trade) from deterministic candidate universe.
- `baseline_vs_ai_ab_test`: logs both streams for clean comparison (baseline execute + AI shadow by default).

## Constrained setup universe
- Symbol fixed to BTCUSDT.
- 15m trigger + 1h/4h context.
- Candidate types limited to deterministic templates:
  - retest_long / retest_short
  - breakout_fallback_long / breakout_fallback_short
- Hard guardrails always win: mandatory SL, one-position limit, daily loss cap, strong risk-off news blocks.

## Data and learning pipeline
Every cycle (including NO_TRADE) is logged as JSONL for future offline training:
- `setups_YYYY-MM-DD.jsonl`
- `candidates_YYYY-MM-DD.jsonl`
- `ai_evals_YYYY-MM-DD.jsonl`
- `policy_decisions_YYYY-MM-DD.jsonl`
- `outcomes_YYYY-MM-DD.jsonl`

## A/B workflow
- Baseline and AI decisions are compared each cycle.
- Disagreements (AI-blocked baseline, candidate mismatch, etc.) are explicitly logged.
- This enables post-analysis before any stronger automation.

## Run
```bash
cd bot
pip install -r requirements.txt
python -m pytest -q
python main.py
```
