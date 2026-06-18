# 测试报告 - LOF 基金套利信息（PRD 1.1 / 骨架阶段）

- 报告日期：2026-06-18
- 报告人：测试 Agent dev-005
- 被测对象：PRD 1.1（tag prd-v1.1）+ 资产文件 + 各模块 README 骨架
- 工作分支：feat/tests-ac-skeleton
- 用例集：tests/ac/ + tests/e2e/

## 一、本次交付

| 项 | 路径 | 数量 |
| --- | --- | --- |
| AC 验收骨架 | `tests/ac/AC-*.test.py` | 17（覆盖 §9 的 P1/P2/C1/C2/H1/H2/A1/A2/A3/I1-I4/S1-S3/T1） |
| 端到端冒烟 | `tests/e2e/test_smoke_pipeline.py` | 1 |
| 通用 fixture | `tests/conftest.py` + `tests/_lib/` | 2 |
| pytest 配置 | `tests/pytest.ini` + `tests/requirements.txt` | 2 |
| AC-P1 离线样本占位 | `tests/fixtures/realtime/ac-p1-index-lof-samples.json` | 5 只（161725/160706/501050/160119/160222） |
| README 升级 | `tests/README.md` | 测试矩阵 + 本地命令 + CI 预留 |

> PM 派单口述"16 条 AC"，按 PRD §9 实际为 17 条（P1/P2、C1/C2、H1/H2、A1/A2/A3、I1-I4、S1-S3、T1）；骨架按 17 条一一映射。

## 二、骨架自检结果

在 `tests/` 目录执行 `python -m pytest -q --strict-markers`：

```
18 skipped in 0.7s
```

- 收集到 18 个用例（17 AC + 1 e2e），全部因 `pending` 标记自动 skip。
- `pytest -k "AC-P1"` 单独筛中 1 个；`pytest -m ac_hard` 筛中 3 个（AC-S1 / AC-S3 / AC-T1）。
- 自检结论：骨架可被发现 / 可被筛选 / 无收集错误。

## 三、PRD 1.1 + 资产 静态核验（开工前快查）

在动手铺骨架前，对 PRD 1.1 和 30 只 watchlist + benchmark 映射做了一轮"测试 Agent 视角的静态核验"，结论：

### 通过项
- watchlist v1：30 行 / 30 唯一 code，类型分布 指数 7 + 行业 11 + 主动 12，status 分布 active 27 + pending_verify 3，与 PRD §7 描述一致。
- benchmark v1：30 只全部满足 sum(weight)=1.000±0.001，CASH 单独编码合规。
- watchlist 与 benchmark 双向 code 对账：无缺失、无多余。
- watchlist 名称与 benchmark 名称同 code 完全一致。
- §6 接口契约字段与 §5 字段表对齐，未发现命名冲突。

### 发现并需回推的疑点（详见第五节 Bug 清单）
1. `assets/benchmark-mapping-v1.csv` 中 `160212 国泰国证大宗商品(LOF)` 的 `index_code` 为 `399987.SZ`，但同一文件里 `160632 鹏华中证酒指数(LOF)` 的"中证酒指数"也写作 `399987.CSI`，两者数字主体相同后缀不同，疑似至少有一处指数代码错填。
2. PRD §7.2 文字称"`pending_verify` 共 3 只：161024 / 161121 / 160628（疑似分级基金）"，与 watchlist v1 实际 status=pending_verify 的 3 只完全一致，但其中 `161024 富国中证军工指数分级` 在 watchlist 的 type 列被标为"行业"，名称含"分级"+"指数"两层属性，与"指数型按 §M2 公式 1 / 行业型按 §M2 公式 2"的算法分流口径冲突，需要先定性。
3. PRD §3 / §6 中 API 路径与 §4.1 页面路径在 `pages/detail/[code]` 这一处使用了 Next.js 风格动态段，而 uniapp 小程序场景下普遍以 `pages/detail/detail` + query 形式工作，影响 AC-T1 / AC-S3 的实施口径，需 dev-003 与 PM 对齐。
4. PRD §6.1 `api-lof-list` 返回示例中 `pctile_30d` 字段名与 §6.2 详情、§5.4 历史里的 `premium_pctile_30d` 不一致；列表与详情建议统一字段名以避免前后端解析错位。
5. PRD §M2 公式 2（行业/主动型）说明"剩余仓位按基准结构补全"，但若 W_top10 已经含部分基准成分股（行业型 LOF 常见），存在双计风险，建议在公式注释中明确"top10 与基准 components 的去重口径"，避免覆盖率被高估。
6. PRD §9.1 AC-P1 描述为"5 只指数型 LOF"且要求误差 ≤ 0.5%，但 §M2 指数型公式输出 coverage≈1.00，IOPV 直接来自基准指数实时收益，反推计算口径与"档 3 + 基准补全"主流程不完全一致；测试 Agent 需要 dev-004 给出"AC-P1 反推流程"权威定义，否则用例填实时会产生口径分歧。
7. PRD §9.4 AC-A3 仅描述"非交易时段触发应被忽略"，但未定义"输入事件先到达、判定时已离开交易时段"等中间态行为；建议补一句"以告警判定时刻的交易时段为准"。

> 上述 7 条均为"在写测试用例之前必须先澄清"的 PRD/资产层级议题，按 PM 纪律应回推 dev-002（资产/PRD）与 dev-001（仲裁），而非阻塞骨架交付。骨架已先行落地。

## 四、AC 用例当前状态

| AC | 标题 | 主责 | 是否硬约束 | 当前状态 | 阻塞依赖 |
| --- | --- | --- | --- | --- | --- |
| AC-P1 | 5 只指数 LOF 实时溢价 vs 反推 ≤ 0.5% | dev-004 | 否 | pending | dev-004 拉取器 + 离线 NAV 数据；BUG-004 反推口径定义 |
| AC-P2 | 30 只整体覆盖率均值 ≥ 90% | dev-004 | 否 | pending | dev-004 拉取器 + api-lof-list |
| AC-C1 | 盘中每分钟 30 行 | dev-004 | 否 | pending | dev-004 调度 + 写入 |
| AC-C2 | 失败 30 秒内重试 3 次 | dev-004 | 否 | pending | dev-004 sources |
| AC-H1 | 详情页 30 天曲线无断点 | both | 否 | pending | dev-004 history API + dev-003 详情页 |
| AC-H2 | premium_pctile_30d 误差 ≤ 0.01 | dev-004 | 否 | pending | dev-004 校准任务 |
| AC-A1 | 溢价>5% 1 分钟内 2 分钟内告警 | dev-004 | 否 | pending | dev-004 告警引擎 |
| AC-A2 | 30 分钟冷却 + cooldown_blocked | dev-004 | 否 | pending | dev-004 告警引擎 |
| AC-A3 | 非交易时段忽略 | dev-004 | 否 | pending | dev-004 告警引擎；BUG-006 中间态定义 |
| AC-I1 | api-lof-list p95 ≤ 800ms | dev-004 | 否 | pending | dev-004 云函数 |
| AC-I2 | api-lof-detail 6 块齐全 | dev-004 | 否 | pending | dev-004 云函数 |
| AC-I3 | api-lof-history 30 天 ≥ 20 个交易日 | dev-004 | 否 | pending | dev-004 云函数 |
| AC-I4 | ingest-realtime 三路径码值 | dev-004 | 否 | pending | dev-004 云函数 |
| AC-S1 | uniCloud 配额连续 3 日达标 | dev-004 | 是 | pending | dev-004 架构落地后取真实日志 |
| AC-S2 | 写入仅走 ingest；前端不直连 | both | 否 | pending | 静态扫描可在骨架阶段先跑（已预留实现位） |
| AC-S3 | uniapp 不改源码 build:mp-weixin | dev-003 | 是 | pending | dev-003 工程化 + npm 脚本 |
| AC-T1 | 详情页头部三段式覆盖率 | dev-003 | 是 | pending | dev-003 详情页 + dev-004 detail API |
| e2e-smoke | 拉取器 → ingest → uniCloud → list 全链路 | both | 否 | pending | dev-004 拉取器 + ingest + list 联通 |

## 五、Bug 清单（开工前静态核验）

> 命名规则：BUG-编号 [优先级] 标题；定向回推 + 抄送 dev-001。

### BUG-001 [P1] 同一指数代码主体被分别写成 .CSI / .SZ 后缀，疑似数据准确性问题
- 关联 AC：AC-P2 / AC-I2 / AC-T1（覆盖率与详情页直接消费 benchmark_components）
- 文件：`F:\CodexWorkspace\10-项目\2026-06-17-LOF基金套利信息\assets\benchmark-mapping-v1.csv`
- 复现：grep 该文件，可见两行——
  - `160632,鹏华中证酒指数(LOF),中证酒指数,399987.CSI,0.95`
  - `160212,国泰国证大宗商品(LOF),国证大宗商品指数,399987.SZ,0.95`
- 期望：两个指数代码主体不应同为 399987；中证酒指数代码应核对（资料常见为 399987.SZ "中证酒"），国证大宗商品指数实际代码不是 399987.SZ。
- 实际：两条同主体，必有一条错；后端在 M1.2/M2.1 拿不到正确行情时会被降级为 `source_quality=degraded`，进而拉低 AC-P2 覆盖率均值。
- 影响等级：高（直接影响 2 只 LOF 的 IOPV 与 §9.1 AC-P2 验收）
- 回推：dev-002（资产 owner），抄送 dev-001。

### BUG-002 [P2] 161024 富国中证军工指数分级 在 watchlist type=行业，与 §M2 公式分流口径冲突
- 关联 AC：AC-P2 / AC-I2
- 文件：`assets/lof-watchlist-v1.csv`（type 列）/ PRD §M2
- 现象：名称含"指数"+"分级"，但 type 标记为"行业"。
- 期望：要么按"指数"分流（公式 1，coverage ≈ 1.00），要么在 §7.1 status=pending_verify 阶段保持 type 待定，由 dev-004 真实元数据回填后再固化。
- 实际：被算作行业 → 走公式 2 → 与 §10 决策"指数型走公式 1"对不上。
- 影响等级：中（仅 1 只标的，但会让 AC-P2 报告产生争议）
- 回推：dev-002（type 列定性），抄送 dev-001。

### BUG-003 [P2] 列表与详情接口分位字段名不一致
- 关联 AC：AC-I1 / AC-I2
- 文件：`01-需求.md` §6.1 与 §6.2
  - §6.1 列表：`pctile_30d`
  - §6.2 详情：`pctile_30d`（顶层）+ `realtime` 块无；§5.4 历史：`premium_pctile_30d`
- 现象：同一概念在列表 / 历史使用了不同字段名（`pctile_30d` vs `premium_pctile_30d`），前端 store 与 detail 解析需要写两套。
- 期望：字段名统一为 `premium_pctile_30d`（与 §5.4 数据库字段名对齐）。
- 影响等级：中（不阻塞实现，但会让 AC-I1 / AC-I2 字段断言写两版）
- 回推：dev-002（PRD 措辞），抄送 dev-001 + dev-003 + dev-004。

### BUG-004 [P1] AC-P1 的"反推"流程未给出权威定义
- 关联 AC：AC-P1
- 文件：PRD §9.1
- 现象：§9.1 描述"盘后用官方公告净值反推真实溢价"，但未说明：
  - 当日 NAV 公告的时间口径（T 日 NAV 一般 T+1 09:00 公告）
  - 盘中分钟级"真实溢价"如何由"日终 NAV"反推（是否使用基准指数日内涨幅近似）
  - 误差容忍 0.5% 是绝对数还是相对数
- 影响等级：高（不澄清就无法把骨架填实，导致 AC-P1 永远 pending）
- 回推：dev-004（算法 owner）+ dev-002（PRD），抄送 dev-001。

### BUG-005 [P3] 详情页路径风格疑似与 uniapp 不兼容
- 关联 AC：AC-T1 / AC-S3 / AC-H1
- 文件：PRD §4.1 `frontend/pages/detail/[code]`
- 现象：`[code]` 是 Next.js 文件式动态段，uniapp 一般用 `pages/detail/detail` + query 传 code；若按字面创建 `pages/detail/[code].vue`，HBuilderX 与 mp-weixin 编译可能报错。
- 期望：明确为 `pages/detail/detail` + `?code=xxx`（与 dev-003 现有 `frontend/src` 工程一致）。
- 影响等级：低（dev-003 当前实现已经是 `pages/detail/detail`，文档可对齐）
- 回推：dev-002（PRD 文字），抄送 dev-001 + dev-003。

### BUG-006 [P3] AC-A3 未定义"事件先到、判定时已离场"中间态
- 关联 AC：AC-A3
- 文件：PRD §9.4 AC-A3
- 现象：仅说"非交易时段触发应被忽略"，未明确以"事件时间"还是"判定时间"为准。
- 期望：补充"以判定时刻交易时段为准；判定时刻已离场则忽略"。
- 影响等级：低（边界条件，但用例需要明确才能写断言）
- 回推：dev-002（PRD），抄送 dev-001 + dev-004。

### BUG-007 [P3] §M2 公式 2 未定义 top10 与基准 components 的去重口径
- 关联 AC：AC-P2
- 文件：PRD §M2 公式 2
- 现象：行业型 / 主动型 LOF 的 top10 重仓股可能本身就是基准成分股，若不去重，"剩余仓位 × 基准补全"会与"top10 权重"重叠，造成覆盖率虚高。
- 期望：注释中追加一句"(1 - W_top10) 仅指 top10 之外的仓位；不再扣减基准中与 top10 同股的权重"，或反之，明确去重侧。
- 影响等级：低（数学口径，不影响代码骨架，但影响 AC-P2 用例填实时的预期值）
- 回推：dev-002（PRD），抄送 dev-001 + dev-004。

## 六、风险与下一步

| 项 | 描述 | 缓解 |
| --- | --- | --- |
| BUG-001 / BUG-004 | 影响 AC-P2 / AC-P1 用例填实 | 优先回推 dev-002 / dev-004 在 1~2 日内闭环 |
| 硬约束三件套（AC-T1 / AC-S3 / AC-S1） | dev-003 / dev-004 任一不达标禁止放行 | 骨架已隔离 `-m ac_hard` 入口 |
| dev-003 已合 frontend 脚手架到 main | 需要前端 detail 页与 store 字段同 §6 对齐 | dev-005 在 dev-003 详情页就绪后立即填 AC-T1 |
| 测试与开发并行 | 骨架 pending 阶段不阻塞 dev-003/dev-004 | 模块就绪后由 dev-005 顺序填实并回归 |

### 下一步动作（dev-005 自身）
1. 等 BUG-001~007 中 P1/P2 由 dev-002 / dev-004 闭环 → 更新 `tests/_lib/ac_meta.py` 与 fixture。
2. dev-004 拉取器接通 ingest-realtime 后，先填 AC-I4 / AC-C2（mock 友好）。
3. dev-003 详情页接入真实 detail API 后，填 AC-T1（playwright，硬约束）。
4. 跑完一个完整交易日后，开始累计 AC-S1 配额观察。

## 七、git 状态

- 分支：`feat/tests-ac-skeleton`
- 提交：`c0634cb test(tests): 按 PRD 1.1 §9 建 AC 验收骨架（17 条 AC + 1 e2e + fixtures）`
- 远程：尚未 push（等回执 dev-001 后由我推送，避免误并入 main）
- 工作树：clean

## 八、致 dev-001 / dev-002 / dev-003 / dev-004 的回执

1. **dev-001**：骨架已就绪，请决定是否现在 squash merge 到 main，还是等 BUG-001/004 闭环后一并合并。
2. **dev-002**：BUG-001 / BUG-002 / BUG-003 / BUG-004 / BUG-005 / BUG-006 / BUG-007 共 7 条 PRD/资产层议题，请按优先级修订或确认现状。
3. **dev-003**：骨架不会触碰 `frontend/`；AC-T1 / AC-H1 待详情页完成后由我填实，请在详情页 ready 时通知。
4. **dev-004**：请优先反馈 BUG-004（AC-P1 反推流程定义）+ BUG-001（中证酒指数 / 国证大宗商品指数代码核对）；ingest 端最早交付，将先解锁 AC-I4 / AC-C2。

---

# 测试报告 - 前端演示节点 AC-S3 / AC-T1 回归

- 日期：2026-06-18
- 测试人：dev-005
- worktree：`.worktrees/dev-005-test`
- 分支：`feat/tests-ac-skeleton`
- 基线：`origin/main = 1572d07`
- 范围：dev-003 uni-app 前端可演示节点合入后的硬约束验收起步

## 结论

| 项 | 结果 |
| --- | --- |
| AC-S3 | ✅ Pass：`npm run build:mp-weixin` 成功，产物目录 `frontend/dist/build/mp-weixin` 存在 |
| AC-T1 | ✅ Pass：Detail 页源码 + mock 数据已包含估算覆盖率标签、三段式明细、颜色阈值 |
| PRD §6 contract | ✅ Pass：9 个静态契约测试全部通过 |
| 全量 pytest | ✅ `11 passed, 16 skipped` |
| 阻断 dev-003/dev-004 | 无新增阻断 |

## 执行命令

```powershell
cd F:\CodexWorkspace\10-项目\2026-06-17-LOF基金套利信息\.worktrees\dev-005-test\tests
python -m pytest -q ac/AC-T1.test.py ac/AC-S3.test.py
python -m pytest -q
```

## 结果

```text
AC-S3 / AC-T1: 2 passed
Full: 11 passed, 16 skipped
```

## 验证点

### AC-S3
- 自动检测 `frontend/node_modules`，缺失时先执行 `npm install`。
- 执行 `npm run build:mp-weixin`。
- 断言退出码为 0。
- 断言 `frontend/dist/build/mp-weixin` 目录存在。

### AC-T1
- 检查 `frontend/src/pages/detail/detail.vue`：
  - 存在 `coverage-tag`。
  - 文案包含 `估算覆盖率`。
  - `@tap="toggleBreakdown"` 存在。
  - `v-if="showBreakdown"` 存在。
  - 三段字段 `top10_weight / benchmark_assigned_weight / cash_weight` 均被渲染。
  - CSS 类 `coverage-green / coverage-yellow / coverage-red` 存在。
- 检查 `frontend/src/mock/index.ts`：三段字段均在 mock detail 数据中存在。
- 检查 `frontend/src/utils/format.ts`：颜色阈值为 `>=0.9 green`、`>=0.7 yellow`、其余 red。

## Bug 清单

本轮未发现 dev-003 新增阻断问题。

### 提示级观察

- AC-T1 当前为静态验收（源码 + mock 数据），未启动 H5 Playwright 浏览器流。原因：本阶段目标是前端演示节点与字段结构校验；待后续 dev-003 提供稳定本地服务启动约定后，可升级为浏览器端真实交互验收。
- AC-S3 在 dev-005 worktree 首次执行时会触发 `npm install`，属于测试环境准备，不修改源码。



---


---

---

# Test Report - Backend M1 AC-P1 / marker warning regression

- Date: 2026-06-18
- Tester: dev-005
- worktree: `.worktrees/dev-005-test`
- Branch: `feat/tests-ac-skeleton`
- Baseline: `origin/main = df72a4b`
- Scope: fill AC-P1 offline NAV premium calibration after dev-004 M1 skeleton, and clear root pytest marker warnings.

## Result

| Item | Result |
| --- | --- |
| AC-P1 | Pass: 5 index LOF offline samples satisfy `abs(premium_estimated - premium_truth_close) <= 0.005` |
| marker warning | Pass: root `python -m pytest -q` no longer reports unregistered `contract / pending` markers |
| tests pytest | `12 passed, 15 skipped` |
| root pytest | `21 passed, 1 skipped` |
| Blockers for dev-003/dev-004 | No new blockers |

## Commands

```powershell
cd F:\CodexWorkspace\10-project\2026-06-17-LOF-arbitrage-info\.worktrees\dev-005-test
python -m pytest -q tests/ac/AC-P1.test.py
python -m pytest -q
cd tests
python -m pytest -q
```

## Checks

### AC-P1
- Fixture covers 5 PRD index LOF codes: `161725 / 160706 / 501050 / 160119 / 160222`.
- Calculation follows `lof-fetcher/docs/nav-premium-calibration.md`:
  - `premium_truth_close = (close_price_t - official_nav_t) / official_nav_t`
  - `premium_estimated = (price_t_m - iopv_est_t_m) / iopv_est_t_m`
  - `premium_error = abs(premium_estimated - premium_truth_close)`
- Samples with `source_quality = stale` or missing `iopv_estimated` are skipped.
- All 5 codes have valid minute samples and error is not greater than `0.005`.

## Bug List

No new blocking / major / normal issues found in this round.

### Note

- AC-P1 currently uses an offline calibrated fixture to verify algorithm convention. After real market/NAV sources are connected, replace the fixture with dev-004 actual minute samples and rerun the same AC.


---

---

# Test Report - watchlist-v2 / benchmark-v2 AC-P2 regression

- Date: 2026-06-18
- Tester: dev-005
- worktree: `.worktrees/dev-005-test`
- Branch: `feat/tests-ac-skeleton`
- Baseline: `origin/main = 126b241`
- Scope: implement AC-P2 static coverage / benchmark acceptance after watchlist-v2 and benchmark-v2 merge.

## Result

| Item | Result |
| --- | --- |
| AC-P2 | Pass: all 30 watchlist-v2 funds are covered by benchmark-v2; average coverage is 1.00; low coverage count is 0 |
| Benchmark weights | Pass: all 30 funds have weight sum 1.00; failures 0 |
| 399987 conflict | Pass: only `160632 -> 399987.SZ` remains; no same-numeric-code conflict |
| tests ac_p | `2 passed, 25 deselected` |
| tests full pytest | `13 passed, 14 skipped` |
| Blockers for dev-003/dev-004 | No new blockers |

## Commands

```powershell
cd F:\CodexWorkspace\10-project\2026-06-17-LOF-arbitrage-info\.worktrees\dev-005-test\tests
python -m pytest -q -m ac_p
python -m pytest -q
```

## Bug List

No new blocking / major / normal issues found in this round.

### Note

- AC-P2 currently verifies static watchlist-v2 and benchmark-v2 structure, weights, and conflict constraints. After dev-004 switches runtime defaults to v2 and emits real coverage, rerun the same AC against fetcher/API output.

---

# Test Report - M1 backend local smoke acceptance

- Date: 2026-06-18
- Tester: dev-005
- worktree: `.worktrees/dev-005-test`
- Branch: `feat/tests-ac-skeleton`
- Baseline: `origin/main = 65a276d`
- Scope: fill M1 local smoke acceptance for AC-I1~I4, AC-C1/C2, AC-P2 sample API coverage, and AC-S1 quota placeholder after dev-004 backend v2 smoke merge.

## Result

| Item | Result |
| --- | --- |
| AC-I1 | Pass: sample list output matches PRD 6.1 and local builder p95 <= 800ms |
| AC-I2 | Pass: sample detail output matches PRD 6.2 and contains 6 required blocks |
| AC-I3 | Pass: sample history output matches PRD 6.3, day granularity, >= 20 records |
| AC-I4 | Pass: ingest body contract plus local `contract-smoke` / `local-api-smoke` cover success and error codes |
| AC-C1 | Pass / partial: one local realtime snapshot minute contains 30 unique LOF rows with valid coverage/source_quality |
| AC-C2 | Pending: waiting for executable retry trace from dev-004 |
| AC-P2 | Pass: static v2 assets still pass; backend sample list coverage matches v2 policy |
| AC-S1 | Pending / hard: waiting for 3 trading days of quota evidence or offline quota-count fixture |
| Target AC pytest | `9 passed, 2 skipped` |
| M1 marker pytest | `11 passed, 3 skipped, 16 deselected` |
| tests full pytest | `21 passed, 9 skipped` |
| root pytest | `30 passed, 1 skipped` |
| git diff check | Pass |
| Blockers for dev-003/dev-004 | No blocking bug found; AC-C2/S1 remain evidence-dependent pending items |

## Commands

```powershell
cd .worktrees/dev-005-test
python -m pytest -q tests/ac/AC-I1.test.py tests/ac/AC-I2.test.py tests/ac/AC-I3.test.py tests/ac/AC-I4.test.py tests/ac/AC-C1.test.py tests/ac/AC-C2.test.py tests/ac/AC-S1.test.py tests/ac/AC-P2.test.py
cd tests
python -m pytest -q -m "ac_i or ac_c or ac_s or ac_p"
python -m pytest -q
python -m pytest -q ..
git diff --check
```

## Bug List

No new blocking / major / normal issues found in this round.

### Pending Evidence

- AC-C2: waiting for dev-004 failure/retry sample output: source failure -> 3 retries -> log and skip.
- AC-S1: waiting for dev-004/dev-001 quota evidence: cloud function calls, database reads, database writes for 3 trading days.
- Real deployed API regression is not executed in this round because no paid cloud / live uniCloud access should be used by dev-005 M1 local smoke.

---

# Test Report - AC-C2 retry trace and AC-S1 quota estimate

- Date: 2026-06-18
- Tester: dev-005
- worktree: `.worktrees/dev-005-test`
- Branch: `feat/tests-ac-skeleton`
- Baseline: `origin/main = 46560da`
- Scope: fill AC-C2 using dev-004 retry trace evidence; add AC-S1 local quota estimate check while keeping the hard gate pending.

## Result

| Item | Result |
| --- | --- |
| AC-C2 | Pass: success trace is failed, failed, success; failure trace is failed, failed, skipped |
| Retry timing | Pass: third attempt elapsed time is <= 30 seconds in both traces |
| History pollution | Pass: all retry events have `pollute_history=false` |
| AC-S1 local estimate | Pass: local quota estimate is within configured free-budget values |
| AC-S1 release gate | Pending / hard: still requires 3 real trading days of uniCloud quota evidence |
| Target pytest | `2 passed, 1 skipped` |
| AC-C/AC-S marker pytest | `3 passed, 2 skipped, 26 deselected` |
| M1 marker pytest | `12 passed, 2 skipped, 17 deselected` |
| tests full pytest | `23 passed, 8 skipped` |
| root pytest | `34 passed, 1 skipped` |
| git diff check | Pass |
| Blockers for dev-003/dev-004 | No blocking bug found; AC-S1 remains evidence-dependent hard pending |

## Commands

```powershell
cd .worktrees/dev-005-test
python -m pytest -q tests/ac/AC-C2.test.py tests/ac/AC-S1.test.py
```

## Bug List

No new blocking / major / normal issues found in this round.

### Pending Evidence

- AC-S1: formal release approval still waits for cloud function calls, database reads, and database writes from 3 real trading days.

---

# Test Report - Real API E2E readiness checklist

- Date: 2026-06-18
- Tester: dev-005
- worktree: `.worktrees/dev-005-test`
- Branch: `feat/tests-ac-skeleton`
- Baseline: `origin/main = f219e26`
- Scope: prepare real uniCloud / frontend-backend integration acceptance checklist; no live cloud calls executed in this round.

## Result

| Item | Result |
| --- | --- |
| Real API checklist | Prepared for AC-I1/I2/I3/I4, AC-C1/C2, AC-S1 evidence plan |
| Dev-004 prerequisites | Pending: base URL, function names, token policy, deploy/local steps, quota export method |
| AC-S1 gate | Still pending / hard; no early release from local estimate |
| Live API execution | Not started; waiting for dev-004 integration details |
| Blockers for dev-003/dev-004 | No defect reported; dev-004 integration info is the next dependency |

## Bug List

No new blocking / major / normal issues found in this preparation round.

---

# Test Report - Real API integration inputs recorded

- Date: 2026-06-18
- Tester: dev-005
- worktree: `.worktrees/dev-005-test`
- Branch: `feat/tests-ac-skeleton`
- Baseline: `origin/main = 11d6398`
- Scope: record dev-004 real API integration details into the e2e checklist; no live cloud calls or real ingest writes executed in this round.

## Result

| Item | Result |
| --- | --- |
| Function names | Recorded: `lof-list`, `lof-detail`, `lof-history`, `lof-ingest` |
| Read auth | Recorded: list/detail/history do not require token |
| Ingest auth | Recorded: `X-Ingest-Token: <UNICLOUD_INGEST_TOKEN>` required for `lof-ingest` |
| Deployment notes | Recorded: HBuilderX schema upload and four cloud function deployment steps |
| Local sample command | Recorded: `cd lof-fetcher; pip install -r requirements.txt; python -m fetcher.main sample-output --output-dir ..\outputs` |
| AC-S1 evidence | Recorded: local estimate plus 3 real trading days of uniCloud console exports/screenshots |
| Live API execution | Not executed; waiting for concrete public URL prefix and test token / execution approval |
| AC-S1 gate | Still pending / hard; no early release from local estimate |

## Bug List

No new blocking / major / normal issues found in this preparation round.

---

# Test Report - Real uniCloud API acceptance execution

- Date: 2026-06-18
- Tester: dev-005
- worktree: `.worktrees/dev-005-test`
- Branch: `feat/tests-ac-skeleton`
- Baseline: `origin/main = f10de56`
- API Base: `https://fc-mp-8550b592-295c-49da-a33a-57df17e450a1.next.bspapp.com`
- Scope: execute real read API acceptance for AC-I1/I2/I3, safe no-token AC-I4 path, and AC-C1/C2 local regression. Positive ingest write was not executed because token is private and must not be committed.

## Result

| Item | Result |
| --- | --- |
| AC-I1 structure | Pass: `lof-list` returned 30 rows with PRD 6.1 fields |
| AC-I1 p95 | Fail: p95 sample was about `9668ms`, above `800ms` |
| AC-I2 | Pass: `lof-detail` returned required detail blocks including `coverage_breakdown` and `realtime` |
| AC-I3 | Fail: `lof-history?days=30` returned 1 row, below the `>=20` trading-day requirement |
| AC-I4 missing token | Pass: `lof-ingest` without token returned `4010` |
| AC-I4 positive write | Pending: requires private token or dev-004 local execution; no token committed |
| AC-C1/C2 regression | Pass: local regression `3 passed, 1 skipped` with AC-S1 pending |
| AC-S1 | Still pending / hard; only smoke observation recorded, not release evidence |

## Commands

```powershell
cd .worktrees/dev-005-test
$env:REAL_API_BASE='https://fc-mp-8550b592-295c-49da-a33a-57df17e450a1.next.bspapp.com'
$env:REAL_API_P95_REPEAT='5'
python -m pytest -q tests/e2e/test_real_api_acceptance.py -ra
python -m pytest -q tests/ac/AC-C1.test.py tests/ac/AC-C2.test.py tests/ac/AC-S1.test.py
```

## Bug List

### BUG-REAL-001
- AC ID: AC-I1
- Endpoint / page: `GET /lof-list?sort=code`
- Environment: real uniCloud API base `https://fc-mp-8550b592-295c-49da-a33a-57df17e450a1.next.bspapp.com`
- Reproduction steps: set `REAL_API_BASE`, set `REAL_API_P95_REPEAT=5`, run `python -m pytest -q tests/e2e/test_real_api_acceptance.py -ra`
- Expected result: p95 response time `<= 800ms` and 30-row structure compliant response
- Actual result: 30-row structure passed, but p95 was about `9668ms` (`9667.697ms` in the latest sample run)
- Severity: blocking
- Responsible Agent: dev-004
- CC: dev-001

### BUG-REAL-002
- AC ID: AC-I3
- Endpoint / page: `GET /lof-history?code=160119&days=30`
- Environment: real uniCloud API base `https://fc-mp-8550b592-295c-49da-a33a-57df17e450a1.next.bspapp.com`
- Reproduction steps: set `REAL_API_BASE`, run `python -m pytest -q tests/e2e/test_real_api_acceptance.py -ra`
- Expected result: `granularity == day` and at least 20 trading-day rows under `days=30`
- Actual result: `granularity == day`, but returned 1 row
- Severity: blocking
- Responsible Agent: dev-004
- CC: dev-001

### Pending Evidence

- AC-I4 positive ingest write: waiting for private token execution by dev-004 or local environment variable outside git.
- AC-S1: waiting for 3 real trading days of uniCloud quota evidence.
