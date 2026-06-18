# M2 local acceptance checklist (dev-005)

> Status: preparation only; fill after dev-003 / dev-004 delivery.  
> Default API: `http://127.0.0.1:8787`.  
> Online `next.bspapp.com` is skipped by default and requires dev-001 approval.

## 1. Scope matrix

| Item | Coverage | Owner | Automation entry | Status |
| --- | --- | --- | --- | --- |
| Dashboard signals | high premium, high discount, neutral, `source_quality` risk overlay, low-liquidity warning | dev-003 + dev-004 | `tests/e2e/test_m2_dashboard_alerts.py` | pending |
| Refresh UX | 60s polling, manual refresh, non-trading-session banner | dev-003 | `tests/e2e/test_m2_dashboard_alerts.py` | pending |
| Local real API e2e | `lof-list` / `lof-detail` / `lof-history` / `lof-ingest`, default `127.0.0.1`, online skipped | dev-004 | `tests/e2e/test_real_api_acceptance.py` | local-ready |
| Minute snapshot JSONL | local generation, batch shape, 30 funds, timezone timestamp, local-first persistence | dev-004 | `tests/e2e/test_m2_minute_snapshot_jsonl.py` | local-ready |
| AC-S1 | quota risk and 3-trading-day evidence | dev-004 / dev-001 | `tests/ac/AC-S1.test.py` | hard pending |

## 2. Dashboard signal acceptance

### Method

1. Start dev-004 local real API at `http://127.0.0.1:8787`.
2. Use local samples that force these Dashboard states:
   - High premium: `premium >= 0.05`; PRD label: `gao yi jia`.
   - High discount: `premium <= -0.02`; PRD label: `gao zhe jia`.
   - Neutral: `-0.02 < premium < 0.05`; PRD label: `zheng chang`.
   - Degraded data: `source_quality = degraded`; PRD label: `shu ju jiang ji, bu ke mang yong`.
   - Stale data: `source_quality = stale`; PRD label: `shu ju zhi hou, bu ke mang yong`.
   - Low liquidity: `status = active_low_liquidity`; PRD label: `di liu dong xing, cheng jiao e bu zu, jin shen can kao`.
3. Frontend uses `VITE_USE_MOCK=false` and `VITE_API_BASE=http://127.0.0.1:8787`.
4. Verify visible Dashboard states are driven by local real API data, not mock data.

### Pass criteria

- All signal states are visibly distinguishable.
- When `degraded/stale` overlaps with high premium/discount, price direction color remains visible and risk warning is also shown.
- Settings or page mode still identifies real API mode.
- No online uniCloud request is made.

## 3. Refresh and non-trading-session acceptance

### Method

1. Frontend uses local real API and `VITE_USE_MOCK=false`.
2. Verify Dashboard default polling interval is 60 seconds.
3. Click manual refresh and verify current page APIs are requested immediately.
4. Simulate or wait for non-trading session; verify top banner label equivalent to `fei jiao yi shi duan, shu ju ke neng zhi hou`.
5. Manual refresh must not change alert cooldown rules.

### Pass criteria

- 60s polling exists and does not hit online uniCloud.
- Manual refresh triggers local real API request for the current page.
- Non-trading-session banner is visible.
- No online uniCloud request is made.

## 4. Local real API e2e

### Default command

```powershell
cd .worktrees/dev-005-test
$env:REAL_API_BASE='http://127.0.0.1:8787'
$env:REAL_API_INGEST_TOKEN='local-dev-token'
python -m pytest -q tests/e2e/test_real_api_acceptance.py -ra
```

### Pass criteria

- `lof-list` returns 30 rows, PRD section 6.1 fields, and p95 <= 800ms.
- `lof-detail` returns PRD section 6.2 required blocks.
- `lof-history?days=30` returns at least 20 trading days.
- `lof-ingest` returns `4010` without token; local token positive write accepts submitted rows.
- Online `next.bspapp.com` is skipped unless `ALLOW_ONLINE_REAL_API=1` is explicitly set after dev-001 approval.

## 5. Minute snapshot JSONL acceptance

### Local command

```powershell
cd .worktrees/dev-005-test
node uniCloud-aliyun/local-minute-snapshots.js --output outputs/local-minute-snapshots-v2.jsonl --ts 2026-06-18T10:31:00+08:00
python -m pytest -q tests/e2e/test_m2_minute_snapshot_jsonl.py
```

### Pass criteria

- JSONL file is generated locally without online uniCloud writes.
- Every non-empty line is valid JSON.
- Each JSONL line is one minute batch with top-level `ts/items`.
- Each item includes `code/price/iopv/premium/coverage/source_quality`.
- One minute covers 30 unique watchlist-v2 fund codes.
- Timestamp is ISO-8601 and timezone-aware.
- Output supports local-first history persistence; online database persistence remains post-AC-S1.

## 6. Risk and gates

- `localhost:8787` is not an acceptance base URL; use `127.0.0.1:8787`.
- `AC-S1` remains hard pending; online overage `865RU / 500RU`, `436WU / 300WU` is risk evidence only.
- M2 explicitly excludes QDII, online high-frequency integration, and AC-S1 release.
- dev-005 does not change requirements or implementation; bugs are reported to the responsible Agent with dev-001 copied.
