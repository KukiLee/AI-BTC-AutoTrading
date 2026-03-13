from datetime import datetime, timedelta, timezone

from strategy.news_filter import news_gate, score_news


def test_news_scoring_detects_keywords():
    headlines = [
        {"title": "Major exchange issue causes outage", "source": "x"},
        {"title": "Spot ETF inflow continues", "source": "x"},
    ]
    result = score_news(headlines)
    assert result["score"] < 0
    assert "exchange issue" in result["matched_keywords"]


def test_timestamp_filtering():
    old_ts = (datetime.now(timezone.utc) - timedelta(minutes=500)).isoformat()
    now_ts = datetime.now(timezone.utc).isoformat()
    headlines = [
        {"title": "exchange issue", "published_ts": old_ts, "source": "x"},
        {"title": "etf inflow", "published_ts": now_ts, "source": "x"},
    ]
    result = score_news(headlines, lookback_minutes=120)
    assert result["score"] == 2


def test_strong_risk_off_blocks_all():
    gate_long = news_gate(-5, "LONG")
    gate_short = news_gate(-5, "SHORT")
    assert gate_long["allowed"] is False
    assert gate_short["allowed"] is False


def test_positive_favors_long_but_not_force_short_block():
    gate_long = news_gate(4, "LONG")
    gate_short = news_gate(4, "SHORT")
    assert gate_long["allowed"] is True
    assert gate_short["allowed"] is True
