# 份额序列 + 场内申购到账规则探测报告 (POC)

- 探测时间: 2026-06-24T16:52:01+08:00
- 标的: 161725, 161005, 160632, 501203, 501050, 160706, 160216
- 纯只读探测，不接入主链路，不动 §6 字段，不打线上，不提交 token

## 探测点一：逐日份额序列

- 结论: **no_free_daily_share_series; only quarter-end report disclosure**
- 是否找到稳定免费逐日份额序列: False

| source | ok/total | 粒度分布 |
|---|---|---|
| eastmoney_f10_gmbd | 7/7 | quarterly_report=7 |
| eastmoney_fundmob_ivinfo | 7/7 | quarterly_report=7 |
| jisilu_lof | 0/7 | none=7 |

### 标的 x 源 (份额序列) 明细

| code | source | ok | 有逐日序列 | 粒度 | 行数 | 最新日期 | 需登录 | 耗时(ms) |
|---|---|---|---|---|---|---|---|---|
| 161725 | eastmoney_f10_gmbd | True | True | quarterly_report | 37 | 2026-03-31 | False | 278 |
| 161725 | eastmoney_fundmob_ivinfo | True | False | quarterly_report | 45 | 2026-03-31 | False | 198 |
| 161725 | jisilu_lof | False | False | none | 20 |  | False | 266 |
| 161005 | eastmoney_f10_gmbd | True | True | quarterly_report | 85 | 2026-03-31 | False | 119 |
| 161005 | eastmoney_fundmob_ivinfo | True | False | quarterly_report | 84 | 2026-03-31 | False | 30 |
| 161005 | jisilu_lof | False | False | none | 20 |  | False | 67 |
| 160632 | eastmoney_f10_gmbd | True | True | quarterly_report | 34 | 2026-03-31 | False | 98 |
| 160632 | eastmoney_fundmob_ivinfo | True | False | quarterly_report | 46 | 2026-03-31 | False | 38 |
| 160632 | jisilu_lof | False | False | none | 20 |  | False | 78 |
| 501203 | eastmoney_f10_gmbd | True | True | quarterly_report | 23 | 2026-03-31 | False | 91 |
| 501203 | eastmoney_fundmob_ivinfo | True | False | quarterly_report | 23 | 2026-03-31 | False | 37 |
| 501203 | jisilu_lof | False | False | none | 20 |  | False | 89 |
| 501050 | eastmoney_f10_gmbd | True | True | quarterly_report | 44 | 2026-03-31 | False | 121 |
| 501050 | eastmoney_fundmob_ivinfo | True | False | quarterly_report | 39 | 2026-03-31 | False | 25 |
| 501050 | jisilu_lof | False | False | none | 20 |  | False | 69 |
| 160706 | eastmoney_f10_gmbd | True | True | quarterly_report | 85 | 2026-03-31 | False | 130 |
| 160706 | eastmoney_fundmob_ivinfo | True | False | quarterly_report | 83 | 2026-03-31 | False | 27 |
| 160706 | jisilu_lof | False | False | none | 20 |  | False | 68 |
| 160216 | eastmoney_f10_gmbd | True | True | quarterly_report | 83 | 2026-03-31 | False | 170 |
| 160216 | eastmoney_fundmob_ivinfo | True | False | quarterly_report | 56 | 2026-03-31 | False | 25 |
| 160216 | jisilu_lof | False | False | none | 20 |  | False | 75 |

## 探测点二：场内申购份额 T+N 可卖规则

- 结论: **no_structured_onexchange_T+N_sellable; only open-end buy/sell CONFIRM day (T+1) which is a DIFFERENT concept**
- 是否有结构化场内到账字段: False
- 原始确认日文案(场外口径): ['T+1', 'T+2']

| code | source | 有确认日字段 | 买入确认 | 卖出确认 | 场内可卖结构化 | 耗时(ms) |
|---|---|---|---|---|---|---|
| 161725 | eastmoney_f10_jjfl | True | T+1 | T+1 | None | 326 |
| 161005 | eastmoney_f10_jjfl | True | T+1 | T+1 | None | 167 |
| 160632 | eastmoney_f10_jjfl | True | T+1 | T+1 | None | 174 |
| 501203 | eastmoney_f10_jjfl | False | None | None | None | 127 |
| 501050 | eastmoney_f10_jjfl | True | T+1 | T+1 | None | 165 |
| 160706 | eastmoney_f10_jjfl | True | T+1 | T+1 | None | 141 |
| 160216 | eastmoney_f10_jjfl | True | T+2 | T+2 | None | 156 |

