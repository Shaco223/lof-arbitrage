# 申购/赎回状态数据源探测报告 (POC)

- 探测时间: 2026-06-24T10:27:03+08:00
- 标的: 161725, 161005, 160706, 160632, 501050, 501203, 501090

## 源覆盖率 (返回结构化状态字段的标的数/总数)

| source | subscribe | redeem | limit | total |
|---|---|---|---|---|
| eastmoney_f10_html | 7 | 7 | 0 | 7 |
| eastmoney_fundmob_basic | 7 | 7 | 3 | 7 |
| eastmoney_push2 | 0 | 0 | 0 | 7 |
| jisilu_lof | 0 | 0 | 0 | 7 |

- 原始申购状态文案: ['开放申购', '限大额']
- 原始赎回状态文案: ['开放赎回']
- 原始申购额度文案: ['限大额(单日累计购买上限20000元。)', '限大额(单日累计购买上限20万元。)', '限大额(单日累计购买上限50万元。)']
- 建议申购枚举: ['closed', 'limited', 'open', 'other', 'suspended', 'unknown']
- 建议赎回枚举: ['closed', 'open', 'other', 'suspended', 'unknown']

## 标的 x 数据源明细

| code | source | ok | 申购字段 | 赎回字段 | 申购原值 | 赎回原值 | 需登录 | 耗时(ms) | error |
|---|---|---|---|---|---|---|---|---|---|
| 161725 | eastmoney_f10_html | True | True | True | 限大额 | 开放赎回 | False | 349 |  |
| 161725 | eastmoney_fundmob_basic | True | True | True | 限大额 | 开放赎回 | False | 171 |  |
| 161725 | eastmoney_push2 | False |  |  |  |  |  | 147 | RemoteProtocolError |
| 161725 | jisilu_lof | False | False | False | None | None | False | 228 |  |
| 161005 | eastmoney_f10_html | True | True | True | 限大额 | 开放赎回 | False | 248 |  |
| 161005 | eastmoney_fundmob_basic | True | True | True | 限大额 | 开放赎回 | False | 58 |  |
| 161005 | eastmoney_push2 | False |  |  |  |  |  | 226 | RemoteProtocolError |
| 161005 | jisilu_lof | False | False | False | None | None | False | 76 |  |
| 160706 | eastmoney_f10_html | True | True | True | 开放申购 | 开放赎回 | False | 327 |  |
| 160706 | eastmoney_fundmob_basic | True | True | True | 开放申购 | 开放赎回 | False | 49 |  |
| 160706 | eastmoney_push2 | False |  |  |  |  |  | 205 | RemoteProtocolError |
| 160706 | jisilu_lof | False | False | False | None | None | False | 85 |  |
| 160632 | eastmoney_f10_html | True | True | True | 限大额 | 开放赎回 | False | 263 |  |
| 160632 | eastmoney_fundmob_basic | True | True | True | 限大额 | 开放赎回 | False | 57 |  |
| 160632 | eastmoney_push2 | False | False | False |  |  | False | 304 |  |
| 160632 | jisilu_lof | False | False | False | None | None | False | 75 |  |
| 501050 | eastmoney_f10_html | True | True | True | 开放申购 | 开放赎回 | False | 160 |  |
| 501050 | eastmoney_fundmob_basic | True | True | True | 开放申购 | 开放赎回 | False | 52 |  |
| 501050 | eastmoney_push2 | False | False | False |  |  | False | 232 |  |
| 501050 | jisilu_lof | False | False | False | None | None | False | 92 |  |
| 501203 | eastmoney_f10_html | True | True | True | 限大额 | 开放赎回 | False | 149 |  |
| 501203 | eastmoney_fundmob_basic | True | True | True | 限大额 | 开放赎回 | False | 49 |  |
| 501203 | eastmoney_push2 | False | False | False |  |  | False | 229 |  |
| 501203 | jisilu_lof | False | False | False | None | None | False | 78 |  |
| 501090 | eastmoney_f10_html | True | True | True | 开放申购 | 开放赎回 | False | 147 |  |
| 501090 | eastmoney_fundmob_basic | True | True | True | 开放申购 | 开放赎回 | False | 40 |  |
| 501090 | eastmoney_push2 | False | False | False |  |  | False | 240 |  |
| 501090 | jisilu_lof | False | False | False | None | None | False | 85 |  |

## 申购额度 (购买上限, 与申购状态区分)

| code | source | 状态 | 有额度字段 | 额度文案 | 解析金额(元) | 周期 | MAXSG原值 |
|---|---|---|---|---|---|---|---|
| 161725 | eastmoney_fundmob_basic | 限大额 | True | 限大额(单日累计购买上限50万元。) | 500000.0 | day | 500000 |
| 161005 | eastmoney_fundmob_basic | 限大额 | True | 限大额(单日累计购买上限20000元。) | 20000.0 | day | 20000 |
| 160706 | eastmoney_fundmob_basic | 开放申购 | False | None | None | None | 100000000000 |
| 160632 | eastmoney_fundmob_basic | 限大额 | True | 限大额(单日累计购买上限20万元。) | 200000.0 | day | 200000 |
| 501050 | eastmoney_fundmob_basic | 开放申购 | False | None | None | None | 100000000000 |
| 501203 | eastmoney_fundmob_basic | 限大额 | False | None | None | None | -- |
| 501090 | eastmoney_fundmob_basic | 开放申购 | False | None | None | None | 100000000000 |
