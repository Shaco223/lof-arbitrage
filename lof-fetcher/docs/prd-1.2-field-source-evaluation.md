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

| `shares_onexchange` | 集思录「实时数据-LOF」`amount` | 30/30 可得、日更、不进分钟快照；全量需登录 Cookie（游客仅前 20 条），有反爬限频风险（探测 68fc269 / PRD 1.4） | ✅ 真实值（需 Cookie；单位万份；无源 null） |
| `shares_incr_daily` | 集思录「实时数据-LOF」`amount_incr` | 同上 | ✅ 真实值（需 Cookie；单位万份；无源 null） |
| `purchase_confirm_day` | 东财 `jjfl` 场外申购合同买入确认日 | 6/7 可得（160216=T+2、501203 缺）；静态规则、日更或更低频；属确认日参考、非到账可卖日（PRD 1.4） | ✅ 真实值（缺则 null） |
| `redeem_confirm_day` | 东财 `jjfl` 场外赎回合同卖出确认日 | 同上 | ✅ 真实值（缺则 null） |

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

## 六、PRD 1.6 QDII/跨境基金参考指数估算溢价评估（PM 补充）

> 来源：dev-004 QDII reference-index estimate POC，commit `2e30d4a`。本节只记录 PRD 1.6 字段与数据源口径，不代表已实装线上链路。

### 6.1 POC 结论
- 集思录 QDII 登录后能拿全量列表，但 `estimate_value` / `discount_rt` 为空，不能直接拿现成估算溢价。
- 参考指数估算法可行，但只适合部分 high 质量标的。
- 一期 high 标的：`510900` / `159920` / `159941` / `513500` / `161125`。
- 商品/区域类暂不正式接入：`162411` / `160216` / `501018` / `513870` / `513520` / `164824`。

### 6.2 PRD 1.6 字段口径
| 字段 | 数据源/算法 | 本期返回 |
| --- | --- | --- |
| `qdii_estimate_nav` | `nav_official × (1 + qdii_reference_index_change_pct) × (1 + qdii_fx_change_pct)` | high 且输入完整时真实计算；否则 `null` |
| `qdii_estimate_premium` | `price / qdii_estimate_nav - 1` | high 且输入完整时真实计算；否则 `null` |
| `qdii_reference_index_code` | dev-004 按基金合同/公开资料固化映射 | high 标的尽量返回；缺映射时 `null` |
| `qdii_reference_index_name` | 同上 | high 标的尽量返回；缺映射时 `null` |
| `qdii_reference_index_change_pct` | 参考指数行情源 | 可得时返回小数；缺源时 `null` |
| `qdii_fx_change_pct` | 汇率行情源；无需修正时为 `0` | 可得时返回小数或 `0`；缺源时 `null` |
| `qdii_estimate_quality` | 后端质量判定 | `high` / `low` / `unsupported` / `missing_nav` / `missing_index` / `missing_fx` |
| `qdii_estimate_source` | 后端来源标识 | 如 `reference_index_fx_v1`；无估算时 `null` |
| `qdii_nav_date` | 官方净值源 | `YYYY-MM-DD`；缺 T-1 净值时 `null` |

### 6.3 CCR 判断
- **触发 CCR**。PRD 1.6 正式新增 QDII `qdii_*` 字段与独立 QDII 展示模块，属于 §6 结构性新增字段/模块。
- 普通 LOF 既有 `iopv` / `premium` 字段不改名、不删除；QDII 估算不得写成“真实 IOPV”，必须展示“非交易所 IOPV，存在跟踪误差”。
- 缺 T-1 净值、缺参考指数、低质量标的必须返回 `null`；不使用 fallback 合成估算；验收不打线上 uniCloud。
## 七、PRD 1.6.1 §M6 QDII high 名单扩至 12 只（PM 补充）

> 来源：dev-004 batch13 POC v2，commit `6c7b287`。本节只记录 PRD 1.6.1 §M6 名单增补与代理关系口径，不代表已实装线上链路。

### 7.1 batch13 POC v2 结论
- 修正集思录 E 类接口后，`501225` 全球芯片LOF 由 unavailable 升 high。
- 新增 6 只（美股行业/港股/纳指 100）用 ETF 代理均达 high：`161126` / `161127` / `161128` / `161130` / `160125` / `501312`。
- `161125` 作为 POC 回归对照，探测结论一致，予以保留。
- 观察池 5 只（`164824` / `160140` / `162415` / `164906` / `160644`）暂不进 high；其中 `164906` / `160644` 因复合指数结构挂起 PRD 1.6.2。

### 7.2 PRD 1.6.1 `QDII_REFERENCE_MAPPINGS` 定档
| code | 一期处理 | 质量 | qdii_reference_index_code | 参考指数/代理 | 备注 |
| --- | --- | --- | --- | --- | --- |
| `510900` | 正式接入 | high | `hkHSCEI` | 恒生中国企业指数 | PRD 1.6 保留 |
| `159920` | 正式接入 | high | `hkHSI` | 恒生指数 | PRD 1.6 保留 |
| `159941` | 正式接入 | high | `usNDX` | 纳斯达克100指数 | PRD 1.6.1 精确化：原 `usIXIC` 为权宜代理，修正为 `usNDX`，生效需通过 §7.3 RMSE 门槛 |
| `513500` | 正式接入 | high | `usINX` | 标普500指数（新浪 `.INX`） | PRD 1.6 保留；对齐 dev-004 生效版本（原文档 `usSPX` 为笔误） |
| `161125` | 正式接入 | high | `usINX` | 标普500指数（新浪 `.INX`） | POC 回归对照；对齐 dev-004 生效版本（原文档 `usSPX` 为笔误） |
| `501225` | 正式接入 | high | `usSOXX` | iShares 半导体 ETF | 代理费城半导体指数 SOX |
| `161126` | 正式接入 | high | `usXLV` | SPDR 医疗保健精选 ETF | 代理 S5HLTH |
| `161127` | 正式接入 | high | `usXBI` | SPDR 生物科技 ETF | 代理 SPSIBI |
| `161128` | 正式接入 | high | `usXLK` | SPDR 信息科技精选 ETF | 代理 S5INFT |
| `161130` | 正式接入 | high | `usNDX` | 纳斯达克100指数 | 与 `159941` 共享 |
| `160125` | 正式接入 | high | `hkHSI` | 恒生指数 | 与 `159920` 共享 |
| `501312` | 正式接入 | high | `usXLK` | SPDR 信息科技精选 ETF | 与 `161128` 共享代理 |

### 7.3 代理关系与文案红线
- 因免费实时指数（`S5HLTH` / `S5INFT` / `SPSIBI`）缺失，`161126` / `161127` / `161128` / `501312` 使用同类 SPDR/iShares ETF 作为参考指数代理。
- `501225` 参考指数为 `usSOXX`（iShares 半导体 ETF）而非官方费城半导体指数 `SOX`，PRD 1.6.1 明确注明代理关系。
- 前端展示文案保持 PRD 1.6 口径不变——「参考指数估算溢价 / 非交易所 IOPV，存在跟踪误差」；不得改写成「真实 IOPV」或隐去代理关系。
- 后端 `qdii_reference_index_code` / `qdii_reference_index_name` 必须与 §M6.2 表一致；代理 ETF 出现异常（停牌、下市、跟踪误差飙升）时该只 LOF 降级为 `low` 并输出 `null`。

- **PRD 1.6.1 返修（2026-07-03）**：
  - 符号笔误返修：`513500` / `161125` 由 `usSPX` 改回 `usINX`（新浪 `.INX`），对齐 dev-004 生效版本 `QDII_REFERENCE_MAPPINGS`（`.worktrees/dev-004-backend/lof-fetcher/fetcher/sources/qdii_estimate.py`）；未确认 `usSPX` 免费源可得前禁止再次出现。
  - `159941` 精确化 `usIXIC` → `usNDX`：PRD 1.6 原 `usIXIC`（纳指综合）为权宜代理，1.6.1 修正为 `usNDX` 精确跟踪；生效必须通过 RMSE 门槛（`usNDX` 相对 `nav_official` 的 RMSE 严格低于 `usIXIC`），未达门槛前继续以 `usIXIC` 运行；详见 §01-需求.md R12.2、R12.3。
  - 其余 5 只映射（`510900→hkHSCEI` / `159920→hkHSI`）与新增 7 只映射均与 dev-004 batch13 POC v2 探测输出一致，无第 3 处不一致。

### 7.4 CCR 判断
- **触发 CCR**。§6 字段名/类型/接口名不变；§M6 QDII high 名单由 5 只扩至 12 只、`QDII_REFERENCE_MAPPINGS` 映射表结构性新增、代理关系口径新增，属于 §M6 结构性变更 → 触发 CCR，走 PRD 1.6.1 小版本。
- 复合指数结构（`qdii_reference_index_weights`）挂起，另立 PRD 1.6.2 单独讨论。
