# IOPV 数据源探测报告 (POC)

- 探测时间: 2026-06-23T14:04:08+08:00
- 标的: 161725, 161005, 160706, 160632, 501203
- 本轮返回真 IOPV 的源: 无

## 标的 x 数据源对比

| code | source | ok | 真IOPV | 值 | 值类型 | 值时间 | 滞后(s) | 耗时(ms) | error |
|---|---|---|---|---|---|---|---|---|---|
| 161725 | eastmoney_fundmob | False | False | None | estimated_nav(GSZ) |  |  | 117 |  |
| 161725 | eastmoney_push2 | True | False | 0.519 | f92_net_asset(usually 0 for LOF) |  |  | 165 |  |
| 161725 | fundgz | True | False | 0.5181 | estimated_nav(gsz) | 2026-06-23 14:00 | 248 | 83 |  |
| 161725 | jisilu | False | False |  |  |  |  | 0 | code_not_in_free_list |
| 161725 | tencent_quote | True | False | 0.519 | no live IOPV field (f81=prior official NAV) |  |  | 154 |  |
| 161005 | eastmoney_fundmob | False | False | None | estimated_nav(GSZ) |  |  | 31 |  |
| 161005 | eastmoney_push2 | True | False | 3.182 | f92_net_asset(usually 0 for LOF) |  |  | 32 |  |
| 161005 | fundgz | True | False | 3.2217 | estimated_nav(gsz) | 2026-06-23 13:59 | 308 | 18 |  |
| 161005 | jisilu | False | False |  |  |  |  | 0 | code_not_in_free_list |
| 161005 | tencent_quote | True | False | 3.184 | no live IOPV field (f81=prior official NAV) |  |  | 39 |  |
| 160706 | eastmoney_fundmob | False | False | None | estimated_nav(GSZ) |  |  | 25 |  |
| 160706 | eastmoney_push2 | True | False | 1.25 | f92_net_asset(usually 0 for LOF) |  |  | 29 |  |
| 160706 | fundgz | True | False | 1.2577 | estimated_nav(gsz) | 2026-06-23 14:00 | 248 | 16 |  |
| 160706 | jisilu | False | False |  |  |  |  | 0 | code_not_in_free_list |
| 160706 | tencent_quote | True | False | 1.25 | no live IOPV field (f81=prior official NAV) |  |  | 37 |  |
| 160632 | eastmoney_fundmob | False | False | None | estimated_nav(GSZ) |  |  | 24 |  |
| 160632 | eastmoney_push2 | True | False | 0.251 | f92_net_asset(usually 0 for LOF) |  |  | 44 |  |
| 160632 | fundgz | True | False | 0.2511 | estimated_nav(gsz) | 2026-06-23 13:59 | 308 | 25 |  |
| 160632 | jisilu | True | False | None | estimate_value(member-gated; '-' when not logged in) | - |  | 0 |  |
| 160632 | tencent_quote | True | False | 0.251 | no live IOPV field (f81=prior official NAV) |  |  | 44 |  |
| 501203 | eastmoney_fundmob | False | False | None | estimated_nav(GSZ) |  |  | 37 |  |
| 501203 | eastmoney_push2 | True | False | 1.76 | f92_net_asset(usually 0 for LOF) |  |  | 38 |  |
| 501203 | fundgz | True | False | 1.7819 | estimated_nav(gsz) | 2026-06-23 14:00 | 248 | 19 |  |
| 501203 | jisilu | False | False |  |  |  |  | 0 | code_not_in_free_list |
| 501203 | tencent_quote | True | False | 1.76 | no live IOPV field (f81=prior official NAV) |  |  | 37 |  |
