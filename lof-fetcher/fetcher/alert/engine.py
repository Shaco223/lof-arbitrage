from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Literal

Direction = Literal["premium", "discount"]
AlertStatus = Literal["sent", "failed", "cooldown_blocked", "ignored"]


@dataclass
class AlertDecision:
    should_send: bool
    direction: Direction | None
    status: AlertStatus
    reason: str


@dataclass
class AlertEngine:
    premium_threshold: float = 0.05
    discount_threshold: float = -0.02
    cooldown_minutes: int = 30
    _last_sent: dict[str, datetime] = field(default_factory=dict)

    def evaluate(self, code: str, premium: float, now: datetime, is_trading_time: bool = True) -> AlertDecision:
        if not is_trading_time:
            return AlertDecision(False, None, "ignored", "non_trading_time")

        direction: Direction | None = None
        if premium > self.premium_threshold:
            direction = "premium"
        elif premium < self.discount_threshold:
            direction = "discount"

        if direction is None:
            return AlertDecision(False, None, "ignored", "below_threshold")

        last_sent = self._last_sent.get(code)
        if last_sent and now - last_sent < timedelta(minutes=self.cooldown_minutes):
            return AlertDecision(False, direction, "cooldown_blocked", "cooldown")

        self._last_sent[code] = now
        return AlertDecision(True, direction, "sent", "threshold_triggered")
