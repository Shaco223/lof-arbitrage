# PRD 1.2 §6 新增字段免费源评估（dev-004）

> 本文档评估 PRD 1.2 §6 新增 list/detail 字段在免费数据源上的可得性、稳定性，
> 以及本期是否在本地 API 返回真实值。仅评估免费源（不引入付费 API、不消耗 RU/WU）。
>
> 评估时间：2026-06-19（节假日，盘后口径）。
> 评估范围：watchlist-v2 30 只；以 161725 / 161005 / 160706 / 160632 / 501203 为重点抽样。

## 一、本期已能返回真实值的字段

| 字段 | 数据源 | 调用方式 | 字段映射 | 稳定性 | 本期返回 |
|-----|------|---------|---------|------|--------|
| `price` | 腾讯 quote / 东财 push2 / 东财 kline / sina | `qt.gtimg.cn/q=sz161725` 等 | tencent fields[3] / push2 f43 | 高（POC 实测主源命中率 ≥99%） | ✅ 真实值 |
| `price_change_pct` | 腾讯 quote / 东财 push2 | `(price - previous_close) / previous_close` | tencent fields[3]/[4]、push2 f43/f60 | 高 | ✅ 真实值（已在解析层计算 `previous_close`，但 §6.1 此字段在 list 层由前端或后端二次计算；本期通过 `local-api-server` 注入分钟快照时由 sample-dataset / parse 层带入） |
| `volume_amount` | 腾讯 quote fields[37]（成交额，单位元，需 ÷10000 折算万元）、东财 push2 f48 | tencent fields[37] / push2 f48 | 中（节假日字段为 0；交易日命中率高） | ✅ 真实值（解析层已尝试取该字段；缺失时返回 `null`） |
| `iopv` | 天天基金 fundgz `gsz` | `fundgz.1234567.com.cn/js/{code}.js` | `gsz` | 高 | ✅ 真实值 |
| `nav_official` | 天天基金 fundgz `dwjz` | 同上 | `dwjz` | 高（每日 22:30 后更新；节假日沿用最近披露值） | ✅ 真实值 |
| `nav_official_date` | 天天基金 fundgz `jzrq` | 同上 | `jzrq` | 高 | ✅ 真实值 |
| `premium_nav` | 后端公式：`(price - nav_official) / nav_official` | 计算字段 | — | 高（依赖上面两源） | ✅ 真实值（云函数运行时计算） |
| `premium_error` | 后端公式：`iopv - nav_official` | 计算字段 | — | 高 | ✅ 真实值（云函数运行时计算） |
| `nav_estimate_error_pct` | 后端公式：`premium_error / nav_official` | 详情计算字段 | — | 高 | ✅ 真实值（云函数运行时计算） |
| `status` | `assets/lof-watchlist-v2.csv` | csv 读取 | csv `status` 列 | 高（人工固化口径） | ✅ 真实值（lof_meta 表 `status` 已对齐 v2） |

| `subscribe_status` | 天天基金移动端 `fundmob_basic`（`SGZT`）+ 备源概况页 HTML | 主源 7/7 全覆盖、结构化、40–170ms 稳定（探测 2839fad / PRD 1.3 转正） | ✅ 真实值（枚举 open/limited/suspended/closed/unknown，断源兜底 unknown） |
| `redeem_status` | 天天基金移动端 `fundmob_basic`（`SHZT`）+ 备源概况页 HTML | 同上 | ✅ 真实值（枚举 open/suspended/closed/unknown，断源兜底 unknown） |
| `subscribe_limit_amount` | `fundmob_basic` 申购额度文案解析 | 限大额带数字时可解析（50万/2万/20万）；开放/无数字/哨兵 1000亿→null | ✅ 部分真实值（无数字时 null，单位元） |
| `subscribe_limit_period` | 同上文案解析 | 「单日累计」→ day | ✅ 部分真实值（无额度时 null） |

## 二、本期返回 `null` / `unknown` 的字段（免费源不稳定）

| 字段 | 候选源 | 评估结论 | 本期返回 |
|-----|------|---------|--------|
| `fund_scale` | fundgz 概况页 `fund.eastmoney.com/{code}.html` 中的「规模」字段；或基金公告 PDF | HTML 抓取，季报披露才更新；非分钟级；本期资产 CSV 已带 `scale_yi`（人工固化），可作为 fallback | `null`（不强求实时；详情页仍可读 `scale_yi`） |
| `circulating_shares` | 天天基金 / 东财概况页「场内流通份额」 | 日更字段；HTML 抓取；与 `fund_scale` 同样不稳定；PRD §6.1 已明确**不进入分钟快照** | `null` |

## 三、AC-P3 降级口径落地

- 解析层（`fetcher/pipeline/real_poc.py` / `real_watchlist.py`）：
  - 计算 `nav_drift_pct = (iopv - nav_official) / nav_official`（来自 fundgz `gsz` 与 `dwjz`）。
  - `abs(nav_drift_pct) >= 1%` → 当分钟标记 `source_quality = degraded`，并在 `failure_reason` 追加 `nav_estimate_drift:±x.xxxx`。
  - 长跑循环已存在的 §M2-B 连续两次失败升级机制（`run_long_run` / `run_watchlist_long_run`）保持不变：
    任一连续两次非 `ok` 的样本会被升级为 `stale`，与 nav 漂移的本分钟降级互不冲突。

## 四、是否触发 CCR

- **不触发**。所有 PRD 1.2 §6 新增字段均在本期 list/detail 中返回（必填字段返回真实值；选填无源字段返回 `null` / `unknown`）；
  无新字段、无字段改名、无字段删除；类型与 PRD 1.2 §6 保持一致。
- 若后续要求 `subscribe_status` / `redeem_status` / `fund_scale` / `circulating_shares` 必须返回真实值，
  需要项目经理 dev-001 评估是否引入付费数据源或允许 HTML 抓取（含失败兜底口径），并升 PRD 1.3。

## 五、复测命令

```powershell
cd lof-fetcher
python -m pytest tests/test_real_poc.py tests/test_real_watchlist.py tests/test_real_poc_long_run.py -q
```

```powershell
cd uniCloud-aliyun
node tests/local-api-smoke.test.js
node tests/local-http-smoke.test.js
node tests/contract-smoke.test.js
node tests/local-api-real-snapshot.test.js
node tests/list-cache.test.js
node tests/local-real-snapshot.test.js
node tests/local-minute-snapshots.test.js
node tests/history-fallback.test.js
node tests/normalize-query.test.js
```
