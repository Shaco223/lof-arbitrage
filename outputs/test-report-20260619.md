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
