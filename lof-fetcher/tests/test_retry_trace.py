from __future__ import annotations

from fetcher.pipeline.retry_trace import RetryOutcome, RetryTraceRecorder, run_with_retry_trace


class FlakySource:
    def __init__(self, failures_before_success: int) -> None:
        self.failures_before_success = failures_before_success
        self.calls = 0

    def __call__(self) -> dict[str, str]:
        self.calls += 1
        if self.calls <= self.failures_before_success:
            raise TimeoutError(f"source timeout {self.calls}")
        return {"source": "eastmoney", "status": "ok"}


def test_retry_trace_succeeds_on_third_attempt_within_30_seconds():
    recorder = RetryTraceRecorder(base_delay_seconds=5, now="2026-06-18T10:00:00+08:00")

    outcome = run_with_retry_trace("quote", "161725", FlakySource(2), recorder=recorder)

    assert outcome == RetryOutcome(success=True, attempts=3, skipped=False, result={"source": "eastmoney", "status": "ok"})
    assert [event["status"] for event in recorder.events] == ["failed", "failed", "success"]
    assert recorder.events[-1]["elapsed_seconds"] == 10
    assert recorder.events[-1]["elapsed_seconds"] <= 30


def test_retry_trace_logs_and_skips_after_three_failures():
    recorder = RetryTraceRecorder(base_delay_seconds=5, now="2026-06-18T10:00:00+08:00")

    outcome = run_with_retry_trace("quote", "161725", FlakySource(3), recorder=recorder)

    assert outcome.success is False
    assert outcome.attempts == 3
    assert outcome.skipped is True
    assert outcome.result is None
    assert [event["status"] for event in recorder.events] == ["failed", "failed", "skipped"]
    assert recorder.events[-1]["reason"] == "source timeout 3"
    assert recorder.events[-1]["pollute_history"] is False
    assert recorder.events[-1]["elapsed_seconds"] <= 30
