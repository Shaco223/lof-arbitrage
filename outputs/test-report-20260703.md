# 测试报告 2026-07-03 — PRD 1.6.1 QDII high 扩至 12 + 观察池 5

- 角色：测试 Agent (dev-005)
- 分支：feat/tests-prd-v1.6.1-ac（rebase 自 origin/main = b6fc573）
- 工作目录：F:\CodexWorkspace\10-项目\2026-06-17-LOF基金套利信息\.worktrees\dev-005-test
- 本地真实 API：http://127.0.0.1:8787（127.0.0.1，不打线上 next.bspapp.com）
- 约束：仅改 tests/ + outputs/ + .gitignore 报告白名单；未改 fetcher / cloudfunctions 源码；未触碰 Cookie/token

## 一、AC-Q1（PRD 1.6.1 §9.8）— pass

- 契约升级：`tests/contract/prd6_contracts.py` 的 `QDII_ESTIMATE_QUALITY` 枚举新增 `not_supported`。
- 新增 `tests/ac/AC-Q1.test.py` 5 条子用例（marker `ac_q`），启动 `uniCloud-aliyun/local-api-server.js` 于随机端口，
  注入 12 只 high + 5 只观察池 minute-snapshot 后调用 `/lof-list?type=qdii`、`/lof-detail?code=<...>` 断言：
  1. 12 只 high 全部返回 `qdii_estimate_quality=high`，`qdii_reference_index_code` 与 PRD 1.6.1 §M6.2 一一对应
     （510900=hkHSCEI / 159920=hkHSI / 159941=usIXIC / 513500=usINX / 161125=usINX / 501225=usSOXX /
     161126=usXLV / 161127=usXBI / 161128=usXLK / 161130=usNDX / 160125=hkHSI / 501312=usXLK），
     `qdii_estimate_nav` / `qdii_estimate_premium` 数值与 rt 注入完全一致。
  2. 5 只观察池（164824 / 160140 / 162415 / 164906 / 160644）即便 rt 尝试写入 quality=high +
     `qdii_estimate_nav=999`+`qdii_reference_index_code=MALICIOUS`，后端强制返回
     `qdii_estimate_quality=not_supported` 且 8 个 `qdii_*` 字段全部 null。
  3. `/lof-list?type=qdii` 计数：high=12、not_supported=5（观察池不进 QDII Tab 数值展示）。
  4. `/lof-detail?code=164906` 强制 not_supported + 全部 qdii_* null；`/lof-detail?code=501225` 保持 high + usSOXX。
  5. AC-Q1 专项：`159941` 仍为 `usIXIC`（R12.3 门槛未达，dev-004 commit 59aa052 已注明 RMSE(usIXIC)=2.193% < RMSE(usNDX)=2.320%）。

### 代理关系 R12.1 / R12.2 断言（含在 AC-Q1 test 1）
- 501225 → `usSOXX`（iShares 半导体 ETF 代理 SOX）
- 161126 → `usXLV`（SPDR 医疗保健 ETF 代理 S5HLTH）
- 161127 → `usXBI`（SPDR 生物科技 ETF 代理 SPSIBI）
- 161128 → `usXLK`（SPDR 信息科技 ETF 代理 S5INFT）；501312 与 161128 共享 `usXLK`
- 513500 & 161125 → `usINX`（新浪 `.INX` 标普500，非 `usSPX`，R12.2 笔误返修）
- 160125 → `hkHSI`（与 159920 共享 HSI）；161130 → `usNDX`（与 159941 未来接入 NDX 共享）

## 二、观察池 5 只字段实测（本地 API 无 snapshot 时）

| 代码 | qdii_estimate_quality | qdii_* 其余 8 字段 |
|------|-----------------------|--------------------|
| 164824 | not_supported | 全部 null |
| 160140 | not_supported | 全部 null |
| 162415 | not_supported | 全部 null |
| 164906 | not_supported | 全部 null |
| 160644 | not_supported | 全部 null |

- `/lof-list?type=qdii` 返回 17 只（12 high + 5 观察池 not_supported）——观察池纳入 type=qdii 展示层但字段全 null，符合 PRD §M6.7。
- 注入 snapshot 场景（AC-Q1 test 2/4）验证：即便 rt 恶意注入 quality=high，后端仍强制 not_supported + null，未泄漏 MALICIOUS 引用符号。

## 三、契约配套升级

- `HISTORY_ITEM` 保持 PRD 1.4.1 `shares_incr_daily`（选填、nullable）。
- `API_LOF_LIST_ITEM` / `API_LOF_DETAIL_DATA` 补齐 PRD 1.4/1.4.1 4 个共享字段（`shares_onexchange`、`shares_incr_daily`、`purchase_confirm_day`、`redeem_confirm_day`），
  否则 `assert_no_unknown_keys` 会误报——真实 API/detail 已返回这些字段。
- `tests/contract/test_api_lof_list_contract.py` / `test_api_lof_detail_contract.py` 期望集合 / 长度断言同步更新：list 35 字段、detail 43 字段。

## 四、回归口径结果

- `cd tests; python -m pytest -q -ra`：**37 passed, 6 failed, 36 skipped**
  - 5 个 AC-Q1 子用例 pass；contract 全 pass。
  - 6 个 failing 全部为 **PRD 1.5 watchlist 30→122 + PRD 1.6 QDII +17 = 139 只扩容后遗留问题**，与本轮 1.6.1 无关（已在 clean origin/main 复现，见「五、遗留 Bug」）。
- `cd lof-fetcher; python -m pytest -q`：**111 passed**。
- node smoke 12 个脚本：**11 PASS / 1 FAIL**。唯一 FAIL 为 `local-http-smoke.test.js`（`detail.data.realtime` null）；已在 clean main 复现，属预存问题（见「五」）。
- 本地 API 抽样（`/lof-list?type=qdii` + `/lof-detail`）3-5 只：high/not_supported 分流、代理符号、`qdii_*` null 兜底行为均符合 PRD 1.6.1 §9.8 / §M6.2 / §M6.7。

## 五、遗留 Bug 清单（均为 PRD 1.5 起 pre-existing，非本轮 1.6.1 引入）

### BUG-Q1-A｜AC-P2 watchlist / benchmark 版本失配（严重）
- AC 编号：AC-P2
- 复现步骤：`cd tests; python -m pytest -q ac/AC-P2.test.py -ra`
- 期望：`assets/lof-watchlist-v2.csv` 与 `assets/benchmark-mapping-v2.csv` 一一对应且各 code 权重和为 1.0
- 实际：watchlist 现 139 行、benchmark 仅覆盖 30 code（老 30 只），109 只无 benchmark；AC-P2 两条子测试皆 fail
- 影响等级：**严重**（AC-P2 直接与 §M2 覆盖率口径挂钩，若不修，PRD 1.5 起 §9.2 覆盖率验收在 CI 层持续红灯）
- 责任 Agent：dev-002（`assets/benchmark-mapping-v2.csv` 扩容）或 dev-004（覆盖率算法降级/分层）；抄送 dev-001

### BUG-Q1-B｜AC-C1 / AC-I1 / AC-I4 硬编码 30 行（一般）
- AC 编号：AC-C1、AC-I1、AC-I4
- 复现：`cd tests; python -m pytest -q ac/AC-C1.test.py ac/AC-I1.test.py ac/AC-I4.test.py -ra`
- 期望：断言应基于当前 watchlist 大小（139），或用 `>= 30` 门槛
- 实际：三处仍写 `assert len(items) == 30`；PRD 1.5 扩容后每次都 fail
- 影响等级：**一般**（测试脚本自身滞后，功能未坏）
- 责任 Agent：dev-005 自身（本轮聚焦 1.6.1，未随手改；建议单独一轮做 tests hardcoded-30 清理）

### BUG-Q1-C｜AC-I2 sample builder 首只样本无 benchmark_components（一般）
- AC 编号：AC-I2
- 复现：`cd tests; python -m pytest -q ac/AC-I2.test.py -ra`
- 期望：`build_sample_api_outputs` 返回的 detail 至少有 1 条 benchmark_components
- 实际：sample builder 固定选 `watchlist[0]`，PRD 1.5 扩容后首行变为 161226（国投白银LOF），benchmark-mapping-v2 无该 code 对应记录 → 返回空数组
- 影响等级：**一般**
- 责任 Agent：dev-004（`lof-fetcher/fetcher/pipeline/snapshot.py::build_sample_api_outputs` 选样策略需固定到 161725 等已知有 benchmark 的样本，或 dev-002 扩 benchmark-mapping-v2）

### BUG-Q1-D｜local-http-smoke detail.realtime null（一般）
- 复现：`node uniCloud-aliyun/tests/local-http-smoke.test.js`
- 期望：detail 返回 `realtime` block 非 null
- 实际：list 按 code 排序后首行 code detail.realtime = null（sample-dataset 只对老 30 只提供 realtime）
- 影响等级：**一般**
- 责任 Agent：dev-004（`uniCloud-aliyun/local-api-server.js` 或 sample-dataset 补齐扩容后 code 的 realtime；亦可让 local-http-smoke.test.js 选一个已知有 realtime 的 code）

## 六、硬约束与是否可发布

- **AC-Q1（本轮核心）：pass**。PRD 1.6.1 QDII high 12 只 + 观察池 5 只 not_supported 的产品口径已达标。
- **AC-S1 继续 hard pending**（需 3 个真实交易日 uniCloud 配额证据，本轮未涉及）。
- 4 条遗留 bug 均为 **PRD 1.5 扩容后未回填** 的 pre-existing 问题，与本次 1.6.1 CCR 无关联；不阻断 1.6.1 打 tag，但建议 dev-001 在打 tag 前起一个短小的 hygiene 小闭环补齐：
  1) benchmark-mapping-v2 扩容或分层降级（BUG-Q1-A）；
  2) build_sample_api_outputs 选样固定（BUG-Q1-C）；
  3) tests hardcoded 30 → 动态 watchlist 计数（BUG-Q1-B）；
  4) local-http-smoke 选码替换或 sample-dataset 补齐（BUG-Q1-D）。

- **是否可发布服务器**：**AC-Q1 层面可放行**。发布前请项目经理裁定：
  - 若严格审核，建议先修 BUG-Q1-A（AC-P2 严重），其余可作为 fast-follow；
  - 若发布只针对 1.6.1 CCR 而不重跑 §M2 覆盖率验收，本轮 AC-Q1 已完整达标，可以走。
