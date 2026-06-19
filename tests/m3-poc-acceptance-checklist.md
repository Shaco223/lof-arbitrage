# M3 POC 本地集中验收清单 (dev-005)

- 阶段：M3 POC 真实行情采集集中验收
- 阅读：PRD §M3 全章（§M3.1~§M3.8）+ §6 字段契约
- 主干基线：`origin/main = 9b3a88d`
- 测试分支：`feat/tests-ac-skeleton`
- 边界：只看本地 POC 链路，不打线上 `next.bspapp.com`，不放行 AC-S1。
- 测试 Agent 不产 PRD/前端/后端代码改动，只读取产物 + 编写 `tests/`、`outputs/`。

## 1. POC 输入产物

| 产物 | 路径 | 用途 |
| --- | --- | --- |
| 真实行情 POC 报告 | `outputs/backend-real-poc-report-v2.json` | 5 只 LOF 真实拉取/估算/降级证据 |
| 本地分钟快照 | `outputs/local-minute-snapshots-v2.jsonl` | append-only JSONL，每行 = 1 分钟 5 只快照 |
| 后端 SOP | `lof-fetcher/docs/runbook.md` §M3 | dev-004 已登记 `real-poc` 命令与降级口径 |
| watchlist v2 | `assets/lof-watchlist-v2.csv` | 验证 5 只 POC 标的均在 v2 池且无 QDII |

若以上产物未生成，相关用例 `pytest.skip`，不强行 fail。

## 2. 验收映射 M3-V1 ~ M3-V6

| 编号 | PRD 标准 | 测试方法 | 测试用例 | 当前结论 |
| --- | --- | --- | --- | --- |
| M3-V1 | POC 标的范围只含 5 只，不混入 QDII | 校验 `backend-real-poc-report-v2.json` items 顺序 + watchlist-v2 行不含 QDII/跨境关键字 | `tests/e2e/test_m3_real_poc.py::test_m3_v1_poc_codes_no_qdii` | pass |
| M3-V2 | 至少 3 只、目标 5 只连续采集 ≥10 分钟 | 校验 JSONL 每行 5 个 POC 代码、ts 单调递增；连续 ≥10 分钟仍依赖 dev-004 长跑证据 | `test_m3_v2_continuous_snapshot_structure` | pass（结构）; 长跑证据待 dev-004 补 |
| M3-V3 | 有效分钟率 ≥80% | 校验 `summary.field_completeness = ok_count/target_count ≥ 0.8` | `test_m3_v3_valid_minute_ratio_within_snapshot` | pass（当前批次=1.0） |
| M3-V4 | list/detail/history/ingest 不新增/删除/改名 §6 字段 | snapshot items 仅含 §6 子集字段；POC 报告中 ok 行 `premium = price/iopv - 1` 误差 ≤ 1e-4 | `test_m3_v4_section6_field_reuse` | pass |
| M3-V5 | degraded/stale 在 Dashboard/详情页可见 | source_quality 枚举受限；非 ok 行需带 `failure_reason` 给前端展示 | `test_m3_v5_degraded_stale_visibility` | pass（本轮 5 只全 ok） |
| M3-V6 | 仅走 `http://127.0.0.1:8787`，不打线上 uniCloud | 产物字符串不含 `next.bspapp.com` / `bspapp` / QDII；本地 base 固定 127.0.0.1:8787 | `test_m3_v6_local_loop_only` | pass |

## 3. 长跑证据缺口（dev-004 后续补）

M3-V2 的 “≥10 分钟连续采集” 当前 JSONL 只有 1 行（`2026-06-19T10:31:00+08:00`）。这是 dev-004 单次 POC 输出，结构正确但无法覆盖连续 10 分钟硬指标。建议后续：

- dev-004 在盘中开 1 个 fetcher 进程，连跑 ≥10 分钟，append 到 `outputs/local-minute-snapshots-v2.jsonl`。
- dev-005 不强制 fail M3-V2，先记为 “结构合规、长跑证据待补”。
- 长跑证据补齐后，仅扩充本测试文件中长度断言，不动其他用例。

## 4. degraded / stale 可见性补样建议

本轮 5 只 POC 全部 `source_quality=ok`，`test_m3_v5_*` 走的是 ok 分支。建议 dev-004 在后续 POC 跑动中：

- 至少捕获 1 条 `degraded`（备源接管）+ 1 条 `stale`（连续失败）样本。
- 通过同名 JSON 报告产出 `failure_reason`，dev-005 不做注入测试，只对真实样本做断言。

## 5. 与 §6 契约关系

- M3 不触发 PRD §6 CCR：`tests/contract/` 4 套接口契约保持 pass，未变化。
- POC 报告新增的 `failure_reason / sources / elapsed_ms / summary` 仅落在 `outputs/` 调试文件，未进入 §6 API 响应字段。
- 测试用例显式禁止 snapshot JSONL 新增 §6 之外的字段。

## 6. 不放行项（继续 hard pending）

- AC-S1：等 3 个真实交易日 uniCloud 配额证据；线上超额仅作为风险证据。
- AC-I4 正向写入：仍受 `REAL_API_INGEST_TOKEN` 控制，本地真实链路通过，线上正向写入不在本轮放行范围。

## 7. 命令速查

```powershell
cd F:\CodexWorkspace\10-项目\2026-06-17-LOF基金套利信息\.worktrees\dev-005-test\tests
python -m pytest -q e2e/test_m3_real_poc.py -ra
python -m pytest -q -ra
```
