# 测试报告 2026-06-24 — PRD 1.2.2 / 1.2.3 / 1.3 集中验收 + history 契约修复

- 角色：测试 Agent (dev-005)
- 分支：feat/tests-ac-skeleton
- 基线：origin/main = 3070f15（含 PRD 1.2.2/1.2.3/1.3 全部产品+前后端实装）
- 工作目录：F:\CodexWorkspace\10-项目\2026-06-17-LOF基金套利信息\.worktrees\dev-005-test
- 本地真实 API：http://127.0.0.1:8787（lof-list / lof-detail / lof-history / lof-ingest）
- 约束：仅改 tests/ + outputs/ + .gitignore 报告白名单；未打线上 next.bspapp.com；未碰 token

## 一、任务一：history 契约 fail 闭环

- 现象：tests/e2e/test_real_api_acceptance.py::test_real_api_ac_i3_history_contract 报
  `lof-history.data.items[] has unknown keys: ['premium_deviation','premium_estimate_close']`。
- 根因：PRD 1.2.3 给 §6.3 history 增加 premium_estimate_close / premium_deviation，
  但 tests/contract/prd6_contracts.py 的 HISTORY_ITEM spec 未同步。
- 修复：
  - HISTORY_ITEM 新增 premium_estimate_close / premium_deviation（number、required=False、nullable=True）。
  - 同步把 close_price / official_nav / premium_close / premium_pctile_30d 标为 nullable：
    真实数据最新交易日官方净值 T+1 未公布时这些字段合法为 null（符合 AC-H4/H5 口径），
    旧 spec 误标必填非空会在真实数据上误报。
- 结果：**已闭环**。test_real_api_ac_i3_history_contract → pass。

## 二、AC-I1 / AC-I2 切回完整 1.2/1.3 契约

- 背景：dev-004 sample builder 已升级为输出完整 PRD 1.2/1.3 字段集，旧的 legacy 子集断言报 unknown keys。
- 修复：AC-I1 改用 API_LOF_LIST_ITEM，AC-I2 改用 API_LOF_DETAIL_DATA（完整契约）。
- 契约补字段：API_LOF_LIST_ITEM / API_LOF_DETAIL_DATA 已含 subscribe_limit_amount / subscribe_limit_period。
- 结果：AC-I1 / AC-I2 静态 smoke → pass。

## 三、新增 AC 验收（逐条结论）

| AC | 标题 | 方法 | 结论 |
|----|------|------|------|
| AC-H3 | history 真实日线非合成 | 本地 API 抽 5 只，排除 buildFallbackHistory 特征（close 非 0.9262 线性序列、各码序列不同） | pass |
| AC-H4 | premium_close=close/nav-1 | 逐行离线重算（>=30 行），误差 <=1e-4；缺 official_nav 则 premium_close=null | pass（145 行核验，bad=0） |
| AC-H5 | 滚动30交易日分位 | 非空分位∈[0,1]；days=90 取深窗口按 compute_premium_pctile 同口径重算误差<=0.01；缺 premium_close 必 null | pass（150 行全窗口重算，bad=0） |
| AC-H6 | premium_estimate_close 启用日前 null | 抽 5 只，2026-06-22 前必 null，启用日起非合成 | pass（本地链路尚未接真 IOPV，全 null 即非合成，前置守卫通过） |
| AC-H7 | premium_deviation=est-close | 任一操作数 null 则 null（不得置0）；都非空则误差<=1e-4 | pass（当前 est 全 null，deviation 全 null，符合） |
| AC-P6 | 申赎状态枚举受限 | list 30 行契约+枚举校验：申购5值/赎回4值（无 limited）；unknown 兜底不报错 | pass |
| AC-P7 | 额度独立解析 | 抽样核对：161725=500000 / 161005=20000 / 160632=200000 / 160706=null / 501203=null；仅 limited+数字解析；哨兵1e11→null；period=day iff amount | pass |

说明：
- AC-H6/H7 当前本地样例链路尚未接入真实收盘 IOPV，premium_estimate_close 全为 null，
  断言聚焦“禁合成 + 启用日前必 null + deviation 联动 null”，符合 PRD 1.2.3 与 dev-004 回放约定。
  dev-004 周一 09:30 真盘长跑产出真 degraded/真 estimate 样本后，可顺手盘中复跑（非阻断）。
- AC-P7 501203 为 limited 但文案无数字，金额正确解析为 null（已核对）。

## 四、回归口径结果

- tests/（cd tests; REAL_API_BASE=http://127.0.0.1:8787 python -m pytest -q）→ **57 passed, 17 skipped**
- 根目录（python -m pytest -q）→ **110 passed, 4 skipped**
- lof-fetcher（cd lof-fetcher; python -m pytest -q）→ **84 passed**
- node smoke 全套（10 个脚本）→ **全部 PASS**：
  contract-smoke / history-fallback / list-cache / local-api-prd1.2-fields /
  local-api-real-snapshot / local-api-smoke / local-http-smoke / local-minute-snapshots /
  local-real-snapshot / normalize-query

## 五、保持项 / 硬门禁

- 旧口径 AC-P3 6 条保持 skip（PRD 1.2.1 已废弃，采信 dev-004 回放）。
- AC-S1 继续 **hard pending**（需 3 个真实交易日配额证据）。
- AC-I4 正向 lof-ingest 写入仍 skipped（未配置 REAL_API_INGEST_TOKEN，非本轮放行项）。
- 仅用 127.0.0.1:8787，未打线上 next.bspapp.com，未消耗 RU/WU。

## 六、遗留 Bug 清单

- 本轮无新增 阻断 / 严重 / 一般 缺陷。
- history 契约 fail（任务一）已在 tests/contract/prd6_contracts.py 修复闭环。
- 提示级观察（非阻断）：本地样例链路 premium_estimate_close / premium_deviation 全 null，
  真实 estimate 验收需待 dev-004 真盘收盘 IOPV 接入后做一次盘中复跑确认逐日出现。
