# 30 只 watchlist-v2 长跑稳定性结论

- 时间窗：2026-06-22T13:39:43+08:00 ~ 2026-06-22T13:51:17+08:00
- 迭代次数：12
- 总样本：30 只 × 12 次
- 累计 ok=257，degraded=13，stale=90
- 推荐分布：keep=18，watch=3，replace=9

## 单只稳定性

| code | name | type | status | scale_yi | ok_ratio | avg_elapsed_ms | primary_source_hits | failure_reasons | recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 160119 | 南方中证500ETF联接(LOF)A | index | active | 15.0 | 1.0 | 82.42 | tencent_quote:12 | - | keep |
| 160220 | 国泰民益混合(LOF)A | active | active | 3.0 | 1.0 | 85.42 | tencent_quote:12 | - | keep |
| 160632 | 鹏华酒A | industry | active | 12.0 | 1.0 | 91.58 | tencent_quote:12 | - | keep |
| 161005 | 富国天惠成长混合(LOF)A | active | active | 180.0 | 1.0 | 79.0 | tencent_quote:12 | - | keep |
| 161024 | 富国中证军工指数(LOF)A | index | active | 18.0 | 1.0 | 80.67 | tencent_quote:12 | - | keep |
| 162605 | 景顺长城鼎益混合(LOF)A | active | active | 30.0 | 1.0 | 73.17 | tencent_quote:12 | - | keep |
| 501077 | 富国创新企业灵活配置混合(LOF)A | active | active_low_liquidity | 4.0 | 1.0 | 86.58 | tencent_quote:12 | - | keep |
| 501078 | 广发科创主题灵活配置混合(LOF) | active | active_low_liquidity | 4.0 | 1.0 | 90.33 | tencent_quote:12 | - | keep |
| 501081 | 中欧科创主题混合(LOF)A | active | active_low_liquidity | 4.0 | 1.0 | 94.08 | tencent_quote:12 | - | keep |
| 501085 | 财通科创主题灵活配置混合(LOF) | active | active_low_liquidity | 4.0 | 1.0 | 97.33 | tencent_quote:12 | - | keep |
| 501090 | 华宝中证消费龙头ETF联接A | index | active_low_liquidity | 4.0 | 1.0 | 79.75 | tencent_quote:12 | - | keep |
| 501095 | 中银证券科技创新混合(LOF) | active | active_low_liquidity | 4.0 | 1.0 | 95.58 | tencent_quote:12 | - | keep |
| 501203 | 易方达创新未来混合(LOF) | active | active_low_liquidity | 5.0 | 1.0 | 78.83 | tencent_quote:12 | - | keep |
| 501205 | 鹏华创新未来混合(LOF)C | active | active | 12.0 | 1.0 | 74.5 | tencent_quote:12 | - | keep |
| 501206 | 汇添富创新未来混合(LOF) | active | active_low_liquidity | 4.0 | 1.0 | 77.17 | tencent_quote:12 | - | keep |
| 501208 | 中欧创新未来混合(LOF) | active | active_low_liquidity | 5.0 | 1.0 | 70.25 | tencent_quote:12 | - | keep |
| 501219 | 华夏智胜先锋股票(LOF)A | active | active_low_liquidity | 4.0 | 1.0 | 78.33 | tencent_quote:12 | - | keep |
| 501227 | 泓德红利优选混合(LOF)A | active | active | 12.0 | 1.0 | 90.67 | tencent_quote:12 | - | keep |
| 160505 | 博时主题行业混合(LOF) | active | active | 30.0 | 0.0 | 100.0 | tencent_quote:12 | nav_estimate_drift:+0.0184;stale_consecutive_failures:3:1,nav_estimate_drift:+0.0184;stale_consecutive_failures:9:1,nav_estimate_drift:+0.0187;stale_consecutive_failures:4:1,nav_estimate_drift:+0.0187;stale_consecutive_failures:5:1,nav_estimate_drift:+0.0187;stale_consecutive_failures:6:1,nav_estimate_drift:+0.0187;stale_consecutive_failures:7:1,nav_estimate_drift:+0.0187;stale_consecutive_failures:8:1,nav_estimate_drift:+0.0188;stale_consecutive_failures:10:1,nav_estimate_drift:+0.0189;stale_consecutive_failures:2:1,nav_estimate_drift:+0.0192:1,nav_estimate_drift:+0.0194;stale_consecutive_failures:12:1,nav_estimate_drift:+0.0195;stale_consecutive_failures:11:1 | replace |
| 160706 | 嘉实沪深300ETF联接A | index | active | 80.0 | 0.0 | 80.42 | tencent_quote:12 | nav_estimate_drift:+0.0140;stale_consecutive_failures:8:1,nav_estimate_drift:+0.0140;stale_consecutive_failures:9:1,nav_estimate_drift:+0.0145;stale_consecutive_failures:6:1,nav_estimate_drift:+0.0146;stale_consecutive_failures:3:1,nav_estimate_drift:+0.0147:1,nav_estimate_drift:+0.0147;stale_consecutive_failures:2:1,nav_estimate_drift:+0.0148;stale_consecutive_failures:7:1,nav_estimate_drift:+0.0149;stale_consecutive_failures:10:1,nav_estimate_drift:+0.0149;stale_consecutive_failures:11:1,nav_estimate_drift:+0.0149;stale_consecutive_failures:4:1,nav_estimate_drift:+0.0149;stale_consecutive_failures:5:1,nav_estimate_drift:+0.0155;stale_consecutive_failures:12:1 | replace |
| 163406 | 兴全合润混合A | active | active | 150.0 | 0.0 | 72.17 | tencent_quote:12 | nav_estimate_drift:+0.0106;stale_consecutive_failures:2:1,nav_estimate_drift:+0.0108:1,nav_estimate_drift:+0.0112;stale_consecutive_failures:10:1,nav_estimate_drift:+0.0112;stale_consecutive_failures:3:1,nav_estimate_drift:+0.0112;stale_consecutive_failures:4:1,nav_estimate_drift:+0.0112;stale_consecutive_failures:8:1,nav_estimate_drift:+0.0112;stale_consecutive_failures:9:1,nav_estimate_drift:+0.0113;stale_consecutive_failures:7:1,nav_estimate_drift:+0.0117;stale_consecutive_failures:5:1,nav_estimate_drift:+0.0117;stale_consecutive_failures:6:1,nav_estimate_drift:+0.0119;stale_consecutive_failures:11:1,nav_estimate_drift:+0.0135;stale_consecutive_failures:12:1 | replace |
| 501050 | 华夏上证50AH优选指数A | index | active | 40.0 | 0.0 | 94.33 | tencent_quote:12 | nav_estimate_drift:+0.0150;stale_consecutive_failures:9:1,nav_estimate_drift:+0.0151;stale_consecutive_failures:10:1,nav_estimate_drift:+0.0153;stale_consecutive_failures:11:1,nav_estimate_drift:+0.0157;stale_consecutive_failures:6:1,nav_estimate_drift:+0.0158:1,nav_estimate_drift:+0.0158;stale_consecutive_failures:3:1,nav_estimate_drift:+0.0158;stale_consecutive_failures:7:1,nav_estimate_drift:+0.0158;stale_consecutive_failures:8:1,nav_estimate_drift:+0.0159;stale_consecutive_failures:2:1,nav_estimate_drift:+0.0159;stale_consecutive_failures:4:1,nav_estimate_drift:+0.0159;stale_consecutive_failures:5:1,nav_estimate_drift:+0.0160;stale_consecutive_failures:12:1 | replace |
| 501096 | 国联安科创混合(LOF) | active | active | 6.0 | 0.0 | 96.17 | tencent_quote:12 | nav_estimate_drift:+0.0193:1,nav_estimate_drift:+0.0193;stale_consecutive_failures:2:1,nav_estimate_drift:+0.0197;stale_consecutive_failures:6:1,nav_estimate_drift:+0.0197;stale_consecutive_failures:7:1,nav_estimate_drift:+0.0197;stale_consecutive_failures:8:1,nav_estimate_drift:+0.0197;stale_consecutive_failures:9:1,nav_estimate_drift:+0.0202;stale_consecutive_failures:3:1,nav_estimate_drift:+0.0204;stale_consecutive_failures:4:1,nav_estimate_drift:+0.0204;stale_consecutive_failures:5:1,nav_estimate_drift:+0.0214;stale_consecutive_failures:10:1,nav_estimate_drift:+0.0214;stale_consecutive_failures:11:1,nav_estimate_drift:+0.0222;stale_consecutive_failures:12:1 | replace |
| 501097 | 国寿安保科技创新混合(LOF) | active | active_low_liquidity | 4.0 | 0.0 | 90.92 | tencent_quote:12 | nav_estimate_drift:+0.0119;stale_consecutive_failures:2:1,nav_estimate_drift:+0.0119;stale_consecutive_failures:3:1,nav_estimate_drift:+0.0127;stale_consecutive_failures:10:1,nav_estimate_drift:+0.0127;stale_consecutive_failures:11:1,nav_estimate_drift:+0.0127;stale_consecutive_failures:4:1,nav_estimate_drift:+0.0127;stale_consecutive_failures:5:1,nav_estimate_drift:+0.0127;stale_consecutive_failures:6:1,nav_estimate_drift:+0.0128:1,nav_estimate_drift:+0.0133;stale_consecutive_failures:7:1,nav_estimate_drift:+0.0133;stale_consecutive_failures:8:1,nav_estimate_drift:+0.0133;stale_consecutive_failures:9:1,nav_estimate_drift:+0.0143;stale_consecutive_failures:12:1 | replace |
| 501099 | 平安新兴产业混合(LOF) | active | active | 6.0 | 0.0 | 102.17 | tencent_quote:12 | nav_estimate_drift:+0.0137;stale_consecutive_failures:3:1,nav_estimate_drift:+0.0148:1,nav_estimate_drift:+0.0148;stale_consecutive_failures:2:1,nav_estimate_drift:+0.0151;stale_consecutive_failures:4:1,nav_estimate_drift:+0.0151;stale_consecutive_failures:5:1,nav_estimate_drift:+0.0151;stale_consecutive_failures:6:1,nav_estimate_drift:+0.0157;stale_consecutive_failures:7:1,nav_estimate_drift:+0.0158;stale_consecutive_failures:10:1,nav_estimate_drift:+0.0164;stale_consecutive_failures:8:1,nav_estimate_drift:+0.0164;stale_consecutive_failures:9:1,nav_estimate_drift:+0.0166;stale_consecutive_failures:11:1,nav_estimate_drift:+0.0176;stale_consecutive_failures:12:1 | replace |
| 501311 | 嘉实港股通新经济指数A | index | active_low_liquidity | 4.0 | 0.0 | 81.67 | tencent_quote:12 | nav_estimate_drift:-0.0185:1,nav_estimate_drift:-0.0192;stale_consecutive_failures:2:1,nav_estimate_drift:-0.0192;stale_consecutive_failures:3:1,nav_estimate_drift:-0.0197;stale_consecutive_failures:4:1,nav_estimate_drift:-0.0197;stale_consecutive_failures:5:1,nav_estimate_drift:-0.0197;stale_consecutive_failures:6:1,nav_estimate_drift:-0.0203;stale_consecutive_failures:7:1,nav_estimate_drift:-0.0203;stale_consecutive_failures:8:1,nav_estimate_drift:-0.0214;stale_consecutive_failures:12:1,nav_estimate_drift:-0.0217;stale_consecutive_failures:10:1,nav_estimate_drift:-0.0217;stale_consecutive_failures:11:1,nav_estimate_drift:-0.0221;stale_consecutive_failures:9:1 | replace |
| 501201 | 红土创新科技创新股票(LOF)A | active | active | 6.0 | 0.75 | 100.08 | tencent_quote:12 | nav_estimate_drift:+0.0105:1,nav_estimate_drift:+0.0105;stale_consecutive_failures:2:1,nav_estimate_drift:+0.0119:1 | replace |
| 161725 | 招商中证白酒指数(LOF)A | index | active | 300.0 | 0.833333 | 257.25 | tencent_quote:12 | nav_estimate_drift:+0.0101:1,nav_estimate_drift:+0.0113;stale_consecutive_failures:2:1 | watch |
| 161903 | 万家行业优选混合(LOF) | active | active | 8.0 | 0.916667 | 73.08 | tencent_quote:12 | nav_estimate_drift:-0.0103:1 | watch |
| 501057 | 汇添富中证新能源汽车产业指数(LOF)A | index | active_low_liquidity | 4.0 | 0.916667 | 74.25 | tencent_quote:12 | nav_estimate_drift:+0.0104:1 | watch |

## 处理建议口径

- keep：ok_ratio ≥ 0.95，主源稳定命中，无显著失败；可全量保留。
- watch：0.80 ≤ ok_ratio < 0.95，存在偶发降级，建议交易日复跑确认。
- replace：ok_ratio < 0.80，主源持续失败，建议进入 watchlist-v2.1 评审替换。

## 约束

- 仅本地真实采集，不打 next.bspapp.com，不消耗线上 RU/WU。
- §6 字段未变更；snapshot JSONL 仍只暴露 code/price/iopv/premium/coverage/source_quality。
- 长跑 stale 计数沿用 PRD §M2-B 连续两分钟失败口径。
