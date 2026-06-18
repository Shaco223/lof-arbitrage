# Real uniCloud API E2E Acceptance Checklist

- Owner: dev-005 testing agent
- Phase: real uniCloud / frontend-backend integration
- Baseline main: f219e26
- Scope: prepare acceptance checklist and record dev-004 integration inputs; do not call paid cloud resources until dev-001 approves execution against the real endpoint.

## Required inputs from dev-004

| Item | Required detail | Blocking AC |
| --- | --- | --- |
| Base URL | `VITE_API_BASE=https://<uniCloud-url-prefix>/http`; public HBuilderX URL prefix only, without function name | AC-I1 / AC-I2 / AC-I3 |
| Function names | `lof-list`, `lof-detail`, `lof-history`, `lof-ingest` | AC-I1 / AC-I2 / AC-I3 / AC-I4 |
| Auth | read APIs do not need token; `lof-ingest` requires `X-Ingest-Token: <UNICLOUD_INGEST_TOKEN>` | AC-I4 |
| Deployment status | HBuilderX deploys database schemas and four cloud functions; exact public URL still supplied out-of-band | all real API checks |
| Local startup | `cd lof-fetcher; pip install -r requirements.txt; python -m fetcher.main sample-output --output-dir ..\outputs` | all local smoke checks |
| Quota export | local estimate command plus 3 real trading days of uniCloud console exports/screenshots | AC-S1 |

## Environment setup gate

1. Confirm dev-005 worktree is rebased to `origin/main`.
2. Create a local-only env file outside git or use shell env vars:
   - `VITE_USE_MOCK=false`
   - `VITE_API_BASE=https://<uniCloud-url-prefix>/http`
   - `VITE_API_FN_LIST=lof-list`
   - `VITE_API_FN_DETAIL=lof-detail`
   - `VITE_API_FN_HISTORY=lof-history`
   - `VITE_API_FN_INGEST=lof-ingest`
   - `UNICLOUD_INGEST_TOKEN=<token, only for ingest smoke>`
3. Run frontend config check before UI verification:
   - `cd frontend; npm run check:real-api-config`
4. Do not commit secrets, tokens, generated env files, or quota exports unless dev-001 explicitly approves sanitized fixtures.

## Deployment and data preparation notes from dev-004

- HBuilderX deployment:
  - Upload `uniCloud-aliyun/database/schema/*.schema.json`.
  - Deploy `lof-list`, `lof-detail`, `lof-history`, and `lof-ingest`.
  - Configure `lof-ingest` environment variable `UNICLOUD_INGEST_TOKEN=<token>`.
  - Optional setting: `MAX_INGEST_BATCH_SIZE=100`.
- Local fetcher sample output:
  - `cd lof-fetcher; pip install -r requirements.txt; python -m fetcher.main sample-output --output-dir ..\outputs`.
- Ingest smoke input:
  - POST `outputs/backend-sample-ingest-realtime-v2.json` to `lof-ingest`.
  - Include `X-Ingest-Token: <UNICLOUD_INGEST_TOKEN>`.
  - Execute only against a confirmed non-production or non-polluting target.


## AC-I1 list API acceptance

- Endpoint: `GET api-lof-list` or deployed list function mapping.
- Method:
  1. Call the endpoint 100 times against the real integration target.
  2. Measure p95 response time client-side.
  3. Validate response with PRD 6.1 contract.
- Pass criteria:
  - p95 response time `<= 800ms`.
  - `data.items` has exactly 30 rows.
  - Every row contains `code/name/type/price/iopv/premium/coverage/pctile_30d/source_quality`.
  - `source_quality` enum remains `ok/degraded/stale`.
- Bug trigger:
  - Missing/renamed fields, extra incompatible fields, wrong enum, row count drift, or p95 breach.

## AC-I2 detail API acceptance

- Endpoint: `GET api-lof-detail?code=<active code>` or deployed detail function mapping.
- Method:
  1. Select at least one index, one industry, and one active LOF from watchlist-v2.
  2. Validate response with PRD 6.2 contract.
  3. Cross-check Detail page renders the same code and coverage values when frontend uses real API.
- Pass criteria:
  - Required blocks exist: `coverage_top10`, `coverage_breakdown`, `benchmark_components`, `holdings_top10`, `realtime`, `pctile_30d`.
  - `coverage_breakdown` contains `top10_weight/benchmark_assigned_weight/cash_weight`.
  - `realtime` contains `ts/price/iopv/premium/coverage/source_quality`.
- Bug trigger:
  - Any required block missing, type mismatch, Detail page cannot render, or abnormal state not shown.

## AC-I3 history API acceptance

- Endpoint: `GET api-lof-history?code=<active code>&days=30` or deployed history function mapping.
- Method:
  1. Call at least three LOF codes used in AC-I2.
  2. Validate response with PRD 6.3 contract.
  3. Confirm Detail chart receives non-empty day-granularity data.
- Pass criteria:
  - `granularity == day`.
  - `data.items` has at least 20 trading-day rows.
  - Each row contains `date/close_price/official_nav/premium_close/premium_pctile_30d`.
- Bug trigger:
  - Less than 20 rows, wrong granularity, missing fields, non-rendering chart.

## AC-I4 ingest API acceptance

- Endpoint: `POST ingest-realtime` or deployed ingest function mapping.
- Method:
  1. Use `X-Ingest-Token: <UNICLOUD_INGEST_TOKEN>` only for `lof-ingest`; read APIs need no token.
  2. Submit `outputs/backend-sample-ingest-realtime-v2.json` if dev-004/dev-001 confirms the target will not pollute production history.
  3. Submit negative cases: wrong token, missing required field, and quota/limit simulation if available.
- Pass criteria:
  - Wrong token returns `4010`.
  - Missing field returns `4001`.
  - Normal test write returns `accepted == submitted item count` and `rejected == 0`.
  - If quota simulation exists, limit path returns `4290`.
- Safety gate:
  - If dev-004 cannot provide a non-polluting test target, keep real write pending and run only local `contract-smoke` / `local-api-smoke`.

## AC-C1 collection continuity regression

- Evidence source: real backend collection log, uniCloud database export, or exported `lof_realtime` row counts after real ingest.
- Method:
  1. Obtain one trading-day export after real ingest runs.
  2. Count rows per market minute for 09:30-11:30 and 13:00-15:00.
  3. Record missing complete minutes.
- Pass criteria:
  - Each market minute has 30 rows.
  - Complete missing minutes per day `<= 3`.
- Interim status:
  - Existing local sample remains pass/partial until a real trading-day export is available.

## AC-C2 retry regression

- Evidence source: dev-004 retry trace plus any real integration failure logs.
- Method:
  1. Re-run current AC-C2 local evidence test.
  2. If real source failure occurs during integration, request sanitized trace and compare against local format.
- Pass criteria:
  - 3 attempts complete within 30 seconds.
  - Two-failure path ends in success on attempt 3.
  - All-failure path ends as skipped and does not pollute history.

## AC-S1 quota evidence plan

- AC-S1 remains hard pending until real evidence exists.
- Required evidence per trading day:
  - Cloud function calls.
  - Database reads.
  - Database writes.
  - Date, environment, and collection window.
- Pass criteria after 3 trading days:
  - cloud function calls `<= 50000` per day.
  - database reads `<= 50000` per day.
  - database writes `<= 30000` per day.
- Local estimate command:
  - `cd lof-fetcher; python -m fetcher.main ac-evidence --output-dir ..\outputs`.
  - Inspect `outputs/backend-ac-s1-quota-estimate-v2.json`.
- Real evidence method:
  - Export or screenshot cloud function calls, database reads, and database writes from the uniCloud console for 3 consecutive trading days.
- Current allowed action:
  - Record export method and storage path for sanitized evidence only.
  - Do not mark AC-S1 pass from local estimate alone.

## Frontend real API smoke observations

- Dashboard:
  - 30 LOF rows load from real list API.
  - Premium, coverage, pctile, and source quality render without mock-only assumptions.
  - Loading/error/empty states are visible when API is slow or fails.
- Detail:
  - Detail blocks render for selected code.
  - Coverage breakdown colors and values remain consistent with AC-T1.
  - History chart handles real API data and empty/error states.
- Settings:
  - Shows real API mode or relevant status without exposing secrets.
  - Polling settings do not trigger unexpected write calls.

## Bug report template

Use this format for any real integration defect:

```text
- AC ID:
- Endpoint / page:
- Environment:
- Reproduction steps:
- Expected result:
- Actual result:
- Severity: blocking / major / normal / note
- Responsible Agent: dev-003 / dev-004
- CC: dev-001
- Evidence: response snippet, screenshot path, log path, timing sample, or quota export reference
```
