from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable


@dataclass(frozen=True)
class RetryOutcome:
    success: bool
    attempts: int
    skipped: bool
    result: Any = None


class RetryTraceRecorder:
    def __init__(self, base_delay_seconds: int = 5, now: str = "2026-06-18T10:00:00+08:00") -> None:
        self.base_delay_seconds = base_delay_seconds
        self.started_at = datetime.fromisoformat(now)
        self.events: list[dict[str, Any]] = []

    def record(self, source: str, code: str, attempt: int, status: str, reason: str = "") -> None:
        elapsed_seconds = (attempt - 1) * self.base_delay_seconds
        event = {
            "ts": (self.started_at + timedelta(seconds=elapsed_seconds)).isoformat(),
            "source": source,
            "code": code,
            "attempt": attempt,
            "status": status,
            "reason": reason,
            "elapsed_seconds": elapsed_seconds,
            "pollute_history": False,
        }
        self.events.append(event)

    def write_jsonl(self, path: str | Path) -> Path:
        import json

        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text("".join(json.dumps(event, ensure_ascii=False) + "\n" for event in self.events), encoding="utf-8")
        return output


def run_with_retry_trace(
    source: str,
    code: str,
    operation: Callable[[], Any],
    recorder: RetryTraceRecorder | None = None,
    max_attempts: int = 3,
) -> RetryOutcome:
    trace = recorder or RetryTraceRecorder()
    last_reason = ""
    for attempt in range(1, max_attempts + 1):
        try:
            result = operation()
        except Exception as exc:  # noqa: BLE001 - trace records public failure reason for AC-C2 evidence.
            last_reason = str(exc) or type(exc).__name__
            status = "skipped" if attempt == max_attempts else "failed"
            trace.record(source, code, attempt, status, last_reason)
            if attempt == max_attempts:
                return RetryOutcome(success=False, attempts=attempt, skipped=True, result=None)
            continue
        trace.record(source, code, attempt, "success")
        return RetryOutcome(success=True, attempts=attempt, skipped=False, result=result)
    return RetryOutcome(success=False, attempts=max_attempts, skipped=True, result=None)


class PlannedFailureSource:
    def __init__(self, failures_before_success: int, payload: dict[str, Any] | None = None) -> None:
        self.failures_before_success = failures_before_success
        self.payload = payload or {"source": "eastmoney", "status": "ok"}
        self.calls = 0

    def __call__(self) -> dict[str, Any]:
        self.calls += 1
        if self.calls <= self.failures_before_success:
            raise TimeoutError(f"planned source failure {self.calls}")
        return self.payload


def build_retry_trace_samples(output_dir: str | Path) -> dict[str, Path]:
    output = Path(output_dir)
    success_recorder = RetryTraceRecorder()
    run_with_retry_trace("eastmoney", "161725", PlannedFailureSource(2), recorder=success_recorder)
    failure_recorder = RetryTraceRecorder()
    run_with_retry_trace("eastmoney", "161725", PlannedFailureSource(3), recorder=failure_recorder)
    return {
        "success": success_recorder.write_jsonl(output / "backend-ac-c2-retry-success-v2.jsonl"),
        "failure": failure_recorder.write_jsonl(output / "backend-ac-c2-retry-failure-v2.jsonl"),
    }
