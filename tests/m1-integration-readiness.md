# M1 Integration Test Readiness (dev-005)

Stage: M1 integration readiness.
Boundary: no new requirements, no PRD section 6 contract changes, no QDII, no paid cloud resources.
Strategy: prepare upgrade points only. Keep related AC tests pending or static until dev-004 provides runnable APIs and sample outputs.

## 1. Inputs Waiting For dev-004

| Input | Purpose | Blocking AC |
| --- | --- | --- |
| Local API startup command and base URL | Run list/detail/history/ingest HTTP acceptance | AC-I1 / AC-I2 / AC-I3 / AC-I4 |
| Auth method and test token | Verify ingest success, bad token, and missing-field paths | AC-I4 |
| Confirmation that runtime defaults read watchlist-v2 and benchmark-v2 | Upgrade AC-P2 from static asset acceptance to real coverage/API regression | AC-P2 |
| One trading day minute sample output or replayable fetcher logs | Count 30 realtime rows per minute and missing minutes | AC-C1 |
| Data-source failure, stale, and retry sample output | Verify retry and skip-on-failure behavior | AC-C2 |
| uniCloud usage sample or local counting policy | Prepare quota accounting without paid cloud calls | AC-S1 |

## 2. AC Upgrade Plan

| AC | Current State | M1 Upgrade Method | Pass Criteria |
| --- | --- | --- | --- |
| AC-I1 | pending | Request api-lof-list repeatedly and apply PRD 6.1 contract | p95 <= 800ms; 30 rows returned; fields and types do not drift |
| AC-I2 | pending | Sample 5 codes from api-lof-detail and apply PRD 6.2 contract | Six blocks exist; coverage / benchmark / holdings / realtime fields match contract |
| AC-I3 | pending | Sample 5 codes from api-lof-history?days=30 and apply PRD 6.3 contract | At least 20 trading days; field types are correct |
| AC-I4 | pending | Run bad token, missing field, and success cases against ingest-realtime | codes are 4010 / 4001 / 0; accepted equals submitted item count |
| AC-C1 | pending | Replay or read one-day collection sample and aggregate lof_realtime by minute | 30 rows per market minute; missing full minutes <= 3 |
| AC-C2 | pending | Inject or read data-source failure sample and inspect retry logs | 3 retries within 30 seconds; final failure is logged and skipped |
| AC-P2 | pass (static) | Recheck coverage and benchmark-v2 through real list/detail/API outputs | Static constraints still pass; real coverage satisfies PRD thresholds |
| AC-S1 | pending / hard | Define local quota counting first; collect 3 real trading days later | uniCloud reads/writes stay within free quota before release |

## 3. Field Drift Bug Template

If dev-004 sample output differs from PRD section 6 contracts, report to dev-004 and copy dev-001:

```markdown
### BUG-xxx [severity]
- AC ID: AC-Ix / AC-Cx / AC-P2 / AC-S1
- Repro steps: command, request URL, payload, sample output path
- Expected: PRD section 6 or AC pass criteria field / code / threshold
- Actual: actual field, type, error code, count, or latency
- Severity: blocker / major / normal / note
- Owner Agent: dev-004
- CC: dev-001
```

## 4. Not Executed Yet

- Do not call paid uniCloud resources.
- Do not change AC-I1~I4 / AC-C1~C2 / AC-S1 from pending to pass yet.
- Do not modify PRD, assets, backend, or frontend implementation.
- Do not add fields to PRD section 6 for M1 integration.
