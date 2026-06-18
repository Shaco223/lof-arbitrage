from datetime import datetime, timedelta

from fetcher.alert.engine import AlertEngine


def test_alert_engine_cooldown():
    engine = AlertEngine(cooldown_minutes=30)
    now = datetime(2026, 6, 18, 10, 0)

    first = engine.evaluate("161725", 0.06, now)
    second = engine.evaluate("161725", 0.07, now + timedelta(minutes=10))

    assert first.should_send is True
    assert first.status == "sent"
    assert second.should_send is False
    assert second.status == "cooldown_blocked"


def test_alert_engine_ignores_non_trading_time():
    engine = AlertEngine()

    decision = engine.evaluate("161725", 0.06, datetime(2026, 6, 18, 18, 0), is_trading_time=False)

    assert decision.status == "ignored"
    assert decision.reason == "non_trading_time"
