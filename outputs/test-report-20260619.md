# 测试报告 - LOF 基金套利信息（M3 POC 集中验收）

- 报告日期：2026-06-19
- 报告人：测试 Agent dev-005
- 阶段：M3 真实行情 POC 本地集中验收
- 工作分支：feat/tests-ac-skeleton
- worktree：.worktrees/dev-005-test
- 基线：`origin/main = 9b3a88d`
- PRD 范围：§M3 全章 + §6 字段契约
- 边界：仅本地 POC 链路；不打线上 `next.bspapp.com`；不放行 AC-S1。

## 一、本轮交付

| 项 | 路径 | 说明 |
| --- | --- | --- |
| M3 POC 验收用例 | `tests/e2e/test_m3_real_poc.py` | 6 用例对应 M3-V1 ~ M3-V6 |
| M3 验收清单 | `tests/m3-poc-acceptance-checklist.md` | 验收映射、长跑证据缺口、不放行项 |
| M3 验收报告 | `outputs/test-report-20260619.md` | 本文件 |
| 复用产物 | `outputs/backend-real-poc-report-v2.json`、`outputs/local-minute-snapshots-v2.jsonl` | dev-004 已合入 main 的 POC 输出 |

未改动 `frontend/`、`lof-fetcher/`、`uniCloud-aliyun/`、`assets/`，未触发 PRD §6 CCR。

## 二、验收结论（M3-V1 ~ M3-V6）

| 编号 | 验收项 | 结论 | 证据 |
| --- | --- | --- | --- |
| M3-V1 | POC 标的范围 = `161725 / 161005 / 160706 / 160632 / 501203`，不混入 QDII | pass | `backend-real-poc-report-v2.json.items` 顺序匹配；`assets/lof-watchlist-v2.csv` 5 行不含 QDII / 跨境 / 港股 / 美股 关键词 |
| M3-V2 | 至少 3 只、目标 5 只连续采集 ≥10 分钟 | pass（结构合规） + 长跑证据待补 | `local-minute-snapshots-v2.jsonl` 当前 1 行，每行 5 个 POC 代码；ts 单调；连续 ≥10 分钟需 dev-004 长跑产物 |
| M3-V3 | 有效分钟率 ≥80% | pass | `summary.field_completeness = 1.0`，`ok_count=5/target=5` |
| M3-V4 | §6 字段不新增/删除/改名 | pass | snapshot items 仅含 `{code, price, iopv, premium, coverage, source_quality}`；POC 报告 ok 行 `premium = price/iopv - 1` 误差 ≤ 1e-4（5 只均通过） |
| M3-V5 | degraded/stale 在 Dashboard/详情页可见 | pass（本轮无负样本） | source_quality 枚举受限；ok 行 `failure_reason=""`，coverage=1.0；本轮 5 只全 ok，建议 dev-004 后续补 degraded/stale 真样本 |
| M3-V6 | 仅走 `http://127.0.0.1:8787`，不打线上 uniCloud | pass | POC 产物文本不含 `next.bspapp.com / bspapp / qdii`；本地 base 固定 127.0.0.1:8787 |

## 三、命令与输出

```powershell
cd F:\CodexWorkspace\10-项目\2026-06-17-LOF基金套利信息\.worktrees\dev-005-test\tests
python -m pytest -q e2e/test_m3_real_poc.py -ra
# 输出：6 passed in 0.51s

python -m pytest -q -ra
# 输出：35 passed, 11 skipped in 8.94s
```

未跑额外网络/线上 uniCloud；未启动本地 API 服务，仅读取已落库产物，符合 “集中验收、不做频繁回归” 节奏。

## 四、POC 数据快照（来自 dev-004 产物）

| code | name | price | iopv | premium | coverage | source_quality | price_source | nav_source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 161725 | 招商中证白酒指数(LOF)A | 0.526 | 0.5233 | 0.00516 | 1.0 | ok | tencent_quote | fundgz |
| 161005 | 富国天惠成长混合(LOF)A | 3.184 | 3.189 | -0.001568 | 1.0 | ok | tencent_quote | fundgz |
| 160706 | 嘉实沪深300ETF联接A | 1.255 | 1.2604 | -0.004284 | 1.0 | ok | tencent_quote | fundgz |
| 160632 | 鹏华酒A | 0.255 | 0.2533 | 0.006711 | 1.0 | ok | tencent_quote | fundgz |
| 501203 | 易方达创新未来混合(LOF) | 1.757 | 1.7815 | -0.013752 | 1.0 | ok | tencent_quote | fundgz |

`summary.elapsed_ms = 969`，`field_completeness = 1.0`，5 只均经 `tencent_quote + fundgz` 主源拿到价格与估算净值。

## 五、本轮发现与建议

### 1. 长跑证据缺口（M3-V2）

- 等级：提示
- AC：M3-V2
- 现象：`outputs/local-minute-snapshots-v2.jsonl` 当前仅 1 行（`2026-06-19T10:31:00+08:00`），无法覆盖 PRD §M3.7 “连续采集 ≥10 分钟” 硬指标。
- 期望：盘中开 1 个 fetcher 进程持续 append ≥10 分钟，每分钟 5 只全到位。
- 实际：本地 POC 单次输出，结构合规但条数=1。
- 建议责任 Agent：dev-004（继续在 `feat/backend-fetcher-m1` 跑长跑并 append）
- 抄送：dev-001
- dev-005 后续动作：长跑证据补齐后只扩 `test_m3_v2_*` 的长度断言，不动其他用例。

### 2. degraded / stale 真样本缺失（M3-V5）

- 等级：提示
- AC：M3-V5
- 现象：本轮 5 只 POC 全部 `source_quality=ok`，无 degraded/stale 真实证据，`test_m3_v5_*` 仅命中 ok 分支断言。
- 期望：dev-004 在后续真实采集中保留 ≥1 条 degraded（备源接管）+ ≥1 条 stale（连续失败/iopv 缺失），并通过 `failure_reason` 暴露给 Dashboard。
- 实际：5/5 ok。
- 建议责任 Agent：dev-004
- 抄送：dev-001、dev-003（后续 Dashboard 展示复核）

### 3. 是否扩到 30 只（决策建议）

- 等级：提示
- 结论：建议先补齐 M3-V2 长跑证据 + M3-V5 真负样本后再由 dev-001 裁定是否扩到 30 只 watchlist-v2。
- 理由：当前 5 只主源全 ok 仅证明短时连通性，未验证长跑稳定性与降级链路；扩到 30 只前应先看 fundgz / 东财 / 新浪在 30 只上的覆盖率与失败率。
- 责任 Agent：dev-001（裁定）、dev-004（补长跑与降级证据）

## 六、PRD §6 与 CCR

- PRD §6 API 字段未新增/删除/改名；契约测试 `tests/contract/` 4 套保持 pass。
- POC 报告新增的 `failure_reason / sources / elapsed_ms / summary` 仅落 `outputs/` 调试文件，不进入 §6 API 响应；`test_m3_v4_section6_field_reuse` 在 snapshot JSONL 上做了硬约束。
- 不触发 CCR，不升 PRD 1.2。

## 七、不放行项

- AC-S1：继续 hard pending，等 3 个真实交易日 uniCloud 配额证据；线上 RU/WU 超额仅作为风险证据。
- AC-I4 正向写入：本地真实链路已 pass，但本轮不重复跑；线上正向写入受 `REAL_API_INGEST_TOKEN` 控制，仍按 PM 之前的 “非本轮放行项” 处理。

## 八、是否阻断后续开发

- 阻断：无
- 严重：无
- 一般：无
- 提示：M3-V2 长跑证据待补、M3-V5 degraded/stale 真样本待补（均为 dev-004 后续补样，不阻断 M3 POC 集中验收的功能链路结论）。

## 九、回执（建议格式）

```
【From: 测试 Agent (dev-005)】【To: 项目经理 (dev-001)】
M3 POC 集中验收完成。
- 基线：origin/main = 9b3a88d
- 验收用例：tests/e2e/test_m3_real_poc.py 6 passed
- 整体：M3-V1 ~ M3-V6 pass，无阻断/严重/一般缺陷
- 提示：M3-V2 长跑证据 + M3-V5 真降级样本待 dev-004 后续补
- 是否扩到 30 只：建议补齐长跑/降级证据后由 dev-001 裁定
- AC-S1：继续 hard pending
- 报告：outputs/test-report-20260619.md
```


---

# 测试报告 - LOF 基金套利信息（M3 POC 长跑 + 降级证据复测）

- 报告日期：2026-06-19（增量 update）
- 报告人：测试 Agent dev-005
- 阶段：M3 POC 集中验收（长跑 + 降级证据补样）
- 工作分支：feat/tests-ac-skeleton
- worktree：.worktrees/dev-005-test
- 基线：`origin/main = 96b2ad4`
- 范围：复跑 dev-004 长跑命令 + 降级 / stale 复现命令；补充 M3-V2 长跑硬验证与 M3-V5 真样本硬验证。
- 边界：仅本地 POC 链路；不打线上 `next.bspapp.com`；不提交 token；AC-S1 继续 hard pending。

## 一、本轮新增交付

| 项 | 路径 | 说明 |
| --- | --- | --- |
| M3-V2 长跑硬校验 | `tests/e2e/test_m3_real_poc.py::test_m3_v2_long_run_minute_count` | 校验 long-run summary iterations≥10、duration≥9 min、JSONL 行数≥10 |
| M3-V5 真样本硬校验 | `tests/e2e/test_m3_real_poc.py::test_m3_v5_degraded_and_stale_evidence` | 校验 `outputs/degraded-evidence/` 单次全 degraded、连跑后出现 stale |
| M3-V3 / M3-V4 兼容 | 同文件 | 兼容新 summary 字段 `stale_count` 与 degraded/stale 行 `coverage=0.0`、`premium=null` |
| 长跑产物 | `outputs/local-minute-snapshots-v2.jsonl`、`outputs/backend-real-poc-report-v2.json`、`outputs/backend-real-poc-long-run-v2.json` | 11 分钟、12 次迭代 |
| 降级 / stale 产物 | `outputs/degraded-evidence/local-minute-snapshots-degraded-single.jsonl`、`outputs/degraded-evidence/local-minute-snapshots-degraded.jsonl`、`outputs/degraded-evidence/backend-real-poc-long-run-v2.json`、`outputs/degraded-evidence/backend-real-poc-report-v2.json` | `LOF_POC_BLOCK_NAV=1` 复现，dev-004 给的命令 |

未改动 `frontend/`、`lof-fetcher/`、`uniCloud-aliyun/`、`assets/`，未触发 PRD §6 CCR。

## 二、复跑命令与结果

```powershell
# 长跑（11 分钟、60s 间隔）
cd lof-fetcher
python -m fetcher.main real-poc --output-dir ..\outputs --snapshot-file ..\outputs\local-minute-snapshots-v2.jsonl --duration-minutes 11 --interval-seconds 60

# degraded 单批（5/5 degraded）
$env:LOF_POC_BLOCK_NAV='1'
python -m fetcher.main real-poc --output-dir ..\outputs\degraded-evidence --snapshot-file ..\outputs\degraded-evidence\local-minute-snapshots-degraded-single.jsonl

# degraded → stale streak（连续 2 次失败转 stale）
$env:LOF_POC_BLOCK_NAV='1'
python -m fetcher.main real-poc --output-dir ..\outputs\degraded-evidence --snapshot-file ..\outputs\degraded-evidence\local-minute-snapshots-degraded.jsonl --duration-minutes 0.05 --interval-seconds 5
Remove-Item Env:\LOF_POC_BLOCK_NAV

# 测试
cd tests
python -m pytest -q e2e/test_m3_real_poc.py -ra
python -m pytest -q -ra
```

### 长跑产物

```json
{"iterations": 12, "started_at": "2026-06-19T11:59:25+08:00", "ended_at": "2026-06-19T12:10:34+08:00", "duration_seconds": 668, "interval_seconds": 60.0, "ok_total": 60, "degraded_total": 0, "stale_total": 0, "elapsed_total_ms": 8614, "last_summary": {"target_count": 5, "ok_count": 5, "degraded_count": 0, "stale_count": 0, "field_completeness": 1.0, "elapsed_ms": 471}}
```

- `outputs/local-minute-snapshots-v2.jsonl` 共 12 行，每行 5 个 POC item；ts 单调递增。
- 12 次迭代均 `source_quality=ok`，主源 `tencent_quote + fundgz`。
- 平均每分钟 elapsed≈718ms，符合 PRD §M3 “60s 节奏” 要求。

### 降级 / stale 产物

- `local-minute-snapshots-degraded-single.jsonl`：5 行 `source_quality=degraded`，`coverage=0.0`，`premium=null`。
- `local-minute-snapshots-degraded.jsonl`：第 1 批 5/5 degraded，第 2 批 5/5 stale（连续失败 streak ≥2 升级）。
- `backend-real-poc-long-run-v2.json` (degraded-evidence) `degraded_total=5、stale_total=5`。

## 三、验收结论（M3-V1 ~ M3-V6）

| 编号 | 结论 | 关键证据 |
| --- | --- | --- |
| M3-V1 | pass | `backend-real-poc-report-v2.json.items` = 5 个 POC code；watchlist-v2 不含 QDII 关键词 |
| M3-V2 | pass（长跑硬校验通过） | `iterations=12`、`duration_seconds=668`（≈11 min）、JSONL 12 行 |
| M3-V3 | pass | `field_completeness=1.0`，5/5 ok 全程 |
| M3-V4 | pass | snapshot 仅含 §6 子集字段；ok 行 `premium = price/iopv - 1` 误差 ≤ 1e-4 |
| M3-V5 | pass（真样本硬校验通过） | degraded JSONL 5/5 degraded；连跑 streak 升级 stale；`failure_reason` 含 `nav_BlockedByEnv;missing_estimated_nav;stale_consecutive_failures:2` |
| M3-V6 | pass | 产物文本不含 `next.bspapp.com / bspapp / qdii`；本地 base 固定 127.0.0.1:8787 |

## 四、是否还有阻断

- 阻断：无
- 严重：无
- 一般：无
- 提示：无（M3-V2 / M3-V5 之前提示项已闭环）

## 五、是否建议本地阶段就扩 30 只

结论：**不建议**本地阶段就扩到 30 只，建议先维持 5 只 POC 至少再积累 1 个真实交易日，理由如下：

- 当前 11 分钟长跑均 `source_quality=ok`，仅 5 只主源验证通过；扩到 30 只后行业/主动型 LOF 在 `fundgz` / 东财备源的覆盖率与稳定性未知，应先在 5 只之外抽 1~2 只非指数 LOF 做小步扩张。
- M3-V5 stale 验证目前依赖 `LOF_POC_BLOCK_NAV` 环境注入的"假降级"，没有真实盘中波动样本；扩 30 只前希望至少捕获 1 次主源真实失败 + 备源接管证据。
- watchlist-v2 30 只里包含 `active_low_liquidity` 13 只，扩张需要前端配合 “低流动性提示” 复核；前端目前未在新一轮真实数据上做扩量复核。
- AC-S1 仍 hard pending，扩 30 只会显著增加 RU/WU 风险预估；线上沉淀仍未放行。
- 建议节奏：先让 dev-004 跑 1 个真实交易日 5 只 POC、覆盖盘中 + 收盘；之后再由 dev-001 裁定是否扩到 30 只 watchlist-v2。

## 六、约束遵守

- 未访问 `next.bspapp.com`，本轮全部命令读写本地文件或免费数据源（tencent_quote / fundgz）。
- 未提交任何 token；`UNICLOUD_INGEST_TOKEN` 与 `REAL_API_INGEST_TOKEN` 均未在 worktree 内出现。
- AC-S1 仍 hard pending，仍未放行。
- 未发现阻断/严重缺陷，本轮未发起额外全量回归（仅一次默认回归用于覆盖率验证）。

## 七、回执（建议格式）

```
【From: 测试 Agent (dev-005)】【To: 项目经理 (dev-001)】
M3-V2 长跑 + M3-V5 降级证据已复测通过。
- 基线：origin/main = 96b2ad4
- 长跑：11 min / 12 iterations / JSONL 12 行 / 全 ok
- 降级：LOF_POC_BLOCK_NAV=1 单批 5/5 degraded、连跑 streak 升级 5/5 stale
- M3-V1~V6 全 pass，无阻断/严重/一般
- 是否扩 30 只：不建议本地立刻扩，理由见 outputs/test-report-20260619.md
- AC-S1：继续 hard pending
- 测试：tests/e2e/test_m3_real_poc.py 8 passed；默认 37 passed, 11 skipped
```


---

# PRD 1.2 ?????dev-005????

????? origin/main = 75a8743?PRD 1.2 ???????????? rebase ? origin/main = 4f888ff?? dev-004 ?????? + ???? 30 ?????rebase ?????? 52 passed / 11 skipped / 0 failed?
?????F:\CodexWorkspace\10-??\2026-06-17-LOF??????\.worktrees\dev-005-test
???feat/tests-ac-skeleton
???? API?http://127.0.0.1:8787????? next.bspapp.com?

## ???6 ????? 1.2

- tests/contract/prd6_contracts.py ??? PRD 1.2?
  - list item = 20 ????? status / price_change_pct / volume_amount / nav_official / nav_official_date / premium_nav / premium_error / subscribe_status / redeem_status / fund_scale / circulating_shares??? 9 ????? API_LOF_LIST_ITEM_LEGACY_REQUIRED?
  - detail = 28 ????? nav_estimate_error_pct + holdings_top10[].price_change_pct / contribution_pct???????
  - assert_field_types ?? nullable?None ?????assert_no_unknown_keys ? 1.2 ?????
  - ?? 1.1 legacy ???API_LOF_LIST_ITEM_LEGACY / API_LOF_DETAIL_DATA_LEGACY?? Python ?? smoke ??
- ?????cd tests; python -m pytest -q contract ? 12 passed?

## ??AC-P3 / AC-P4 / AC-P5 ??

| AC | ?? | ?? |
| --- | --- | --- |
| AC-P3 ?????? | pass | ?? dev-004 fetcher.pipeline.real_poc????? NAV_DRIFT_DEGRADED_THRESHOLD==0.01?<1% drift?ok??1%?? ?3%??1% ????degraded ? failure_reason ? nav_estimate_drift?????? drift ? run_long_run ? stale?degraded_total?1, stale_total?1????????????6 passed |
| AC-P4 ?????? | pass | ???? API lof-list 30 ????? (price-nav_official)/nav_official ? premium_nav ?? ? 1e-4??? round6??????????????????2 passed |
| AC-P5 ?????? | pass | ?????? null + ??? unknown ? assert_contract ??????????????????? 9 ??????? 1.2 item ??????4 passed |

## ??e2e ?? API??? 127.0.0.1:8787?

???REAL_API_BASE=http://127.0.0.1:8787 python -m pytest -q tests/e2e/test_real_api_acceptance.py -ra

| AC | ?? | ?? |
| --- | --- | --- |
| AC-I1 list ?? + p95 | pass | 30 ????? 1.2 schema?20 ???????? p95 ? 800ms?? schema 1.1 ??? fail ??? |
| AC-I2 detail 6 ? | pass | ? 1.2 detail?28 ??????coverage_breakdown / realtime / benchmark_components ???? fail ??? |
| AC-I3 history days=30 | pass | granularity=day?items ? 20 ???? |
| AC-I4 ingest ? token | pass | ? token ?? code=4010 |
| AC-I4 ingest ???? | pending?skipped? | ??? REAL_API_INGEST_TOKEN??????? |

???4 passed, 1 skipped?

## ??????

???cd tests; python -m pytest -q -ra?REAL_API_BASE=http://127.0.0.1:8787?
???**52 passed, 11 skipped, 0 failed**?
- ? main ? 2 ????ac/AC-I1?ac/AC-I2 ?? smoke?????
- AC-S1 ?? hard pending?skipped??
- AC-I4 ?? ingest pending?skipped??

## ???? Bug ??

| ?? | AC | ?? | ?? | ?? | ?? |
| --- | --- | --- | --- | --- | --- |
| BUG-P12-001 | AC-I1/AC-I2 | ?? | dev-004 | ?? | Python ??? sample-output ??? API ??????? |

### BUG-P12-001
- AC ???AC-I1 / AC-I2????? smoke?
- ?????
  1. cd lof-fetcher
  2. python -c "from fetcher.pipeline.snapshot import build_sample_api_outputs as b; o=b('../assets/lof-watchlist-v2.csv','../assets/benchmark-mapping-v2.csv','2026-06-18T10:31:00+08:00'); print(sorted(o['list']['data']['items'][0].keys()))"
- ?????sample-output ? list/detail ??????? API??? 1.2????? status/nav_official/premium_nav ? 1.2 ???
- ?????sample-output ???? 1.1 ???list 9 ? / detail 11 ?????? API ? 1.2 ????????
- ???????????? lof-list/lof-detail ?? 1.2 ????? e2e???? Python sample builder ???dev-005 ?? AC-I1/AC-I2 ?? smoke ? 1.1 legacy ???????????? 1.2 ??? API e2e ????????????
- ?? Agent?dev-004??? dev-001?
- ???dev-004 ? fetcher.pipeline.snapshot.build_sample_api_outputs ??? PRD 1.2 ????? dev-005 ?? AC-I1/AC-I2 ?? smoke ???? 1.2 ???

## ??????

- ??? next.bspapp.com?e2e ????? 127.0.0.1:8787?NO_PROXY ????
- ????? token??? ingest ?? token ?? skipped/pending?
- AC-S1 ?? hard pending???????????????????
- ??? tests/ ? outputs/???? frontend/ / lof-fetcher/ / uniCloud-aliyun/ / assets/ / 01-??.md?
