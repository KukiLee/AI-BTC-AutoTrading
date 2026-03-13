"""Centralized configuration loading and validation."""

from __future__ import annotations

from enum import Enum
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ExecutionMode(str, Enum):
    ALERT_ONLY = "alert_only"
    TESTNET_AUTO = "testnet_auto"
    LIVE_AUTO = "live_auto"


class AIEvaluationMode(str, Enum):
    OFF = "off"
    SHADOW = "shadow"
    ADVISORY = "advisory"
    FILTER_TESTNET = "filter_testnet"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    binance_api_key: str = Field(default="", alias="BINANCE_API_KEY")
    binance_api_secret: str = Field(default="", alias="BINANCE_API_SECRET")
    binance_testnet: bool = Field(default=True, alias="BINANCE_TESTNET")

    telegram_bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str = Field(default="", alias="TELEGRAM_CHAT_ID")

    execution_mode: ExecutionMode = Field(default=ExecutionMode.ALERT_ONLY, alias="EXECUTION_MODE")
    enable_live_trading: bool = Field(default=False, alias="ENABLE_LIVE_TRADING")

    symbol: str = Field(default="BTCUSDT", alias="SYMBOL")

    risk_pct: float = Field(default=0.01, alias="RISK_PCT")
    leverage: int = Field(default=5, alias="LEVERAGE")
    max_daily_loss_r: float = Field(default=2.0, alias="MAX_DAILY_LOSS_R")
    cooldown_minutes: int = Field(default=30, alias="COOLDOWN_MINUTES")

    news_lookback_minutes: int = Field(default=120, alias="NEWS_LOOKBACK_MINUTES")
    chase_threshold_pct: float = Field(default=1.8, alias="CHASE_THRESHOLD_PCT")
    box_lookback: int = Field(default=40, alias="BOX_LOOKBACK")
    retest_tolerance_pct: float = Field(default=0.0015, alias="RETEST_TOLERANCE_PCT")
    retest_lookback_bars: int = Field(default=8, alias="RETEST_LOOKBACK_BARS")
    loop_interval_seconds: int = Field(default=60, alias="LOOP_INTERVAL_SECONDS")
    alert_on_no_trade: bool = Field(default=False, alias="ALERT_ON_NO_TRADE")
    alert_dedup_exclude_timestamp: bool = Field(default=True, alias="ALERT_DEDUP_EXCLUDE_TIMESTAMP")

    strict_precision_validation: bool = Field(default=True, alias="STRICT_PRECISION_VALIDATION")
    conditional_order_mode: str = Field(default="legacy", alias="CONDITIONAL_ORDER_MODE")

    stop_buffer_pct: float = Field(default=0.001, alias="STOP_BUFFER_PCT")
    state_file: Path = Field(default=Path("bot_state.json"), alias="STATE_FILE")

    ai_evaluation_enabled: bool = Field(default=True, alias="AI_EVALUATION_ENABLED")
    ai_evaluation_mode: AIEvaluationMode = Field(default=AIEvaluationMode.SHADOW, alias="AI_EVALUATION_MODE")
    ai_min_score_to_allow: float = Field(default=0.70, alias="AI_MIN_SCORE_TO_ALLOW")
    ai_policy_mode: str = Field(default="observe_only", alias="AI_POLICY_MODE")
    dataset_logging_enabled: bool = Field(default=True, alias="DATASET_LOGGING_ENABLED")
    dataset_dir: str = Field(default="./bot/logs/datasets", alias="DATASET_DIR")
    setup_log_jsonl: bool = Field(default=True, alias="SETUP_LOG_JSONL")
    outcome_labeling_enabled: bool = Field(default=True, alias="OUTCOME_LABELING_ENABLED")
    baseline_rules_authoritative: bool = Field(default=True, alias="BASELINE_RULES_AUTHORITATIVE")
    enable_ai_live_override: bool = Field(default=False, alias="ENABLE_AI_LIVE_OVERRIDE")

    news_sources: list[str] = Field(
        default=["https://www.coindesk.com/arc/outboundfeeds/rss/"], alias="NEWS_SOURCES"
    )

    @field_validator("news_sources", mode="before")
    @classmethod
    def parse_news_sources(cls, value):
        if isinstance(value, str):
            parsed = [item.strip() for item in value.split(",") if item.strip()]
            return parsed or ["https://www.coindesk.com/arc/outboundfeeds/rss/"]
        return value

    @model_validator(mode="after")
    def validate_settings(self) -> "Settings":
        if self.execution_mode not in set(ExecutionMode):
            raise ValueError("EXECUTION_MODE must be one of: alert_only, testnet_auto, live_auto")
        if not 0 < self.risk_pct <= 0.05:
            raise ValueError("RISK_PCT must be > 0 and <= 0.05")
        if self.execution_mode == ExecutionMode.LIVE_AUTO and not self.enable_live_trading:
            raise ValueError("LIVE mode requested but ENABLE_LIVE_TRADING is false")
        if self.execution_mode == ExecutionMode.TESTNET_AUTO and not self.binance_testnet:
            raise ValueError("testnet_auto mode requires BINANCE_TESTNET=true")
        if self.retest_tolerance_pct <= 0:
            raise ValueError("RETEST_TOLERANCE_PCT must be > 0")
        if self.box_lookback < self.retest_lookback_bars:
            raise ValueError("BOX_LOOKBACK must be >= RETEST_LOOKBACK_BARS")
        if self.conditional_order_mode not in {"legacy", "algo"}:
            raise ValueError("CONDITIONAL_ORDER_MODE must be one of: legacy, algo")
        if not 0.0 <= self.ai_min_score_to_allow <= 1.0:
            raise ValueError("AI_MIN_SCORE_TO_ALLOW must be between 0.0 and 1.0")
        if self.execution_mode == ExecutionMode.LIVE_AUTO and self.ai_evaluation_mode != AIEvaluationMode.OFF:
            if not self.enable_ai_live_override:
                raise ValueError(
                    "LIVE mode with AI enabled requires ENABLE_AI_LIVE_OVERRIDE=true (default false for safety)"
                )
        return self


load_dotenv()
settings = Settings()
