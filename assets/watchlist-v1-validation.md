# watchlist-v1 元数据验证报告

- 生成时间：2026-06-18T11:01:56+08:00
- 数据源：东方财富 pingzhongdata
- 验证范围：30 只 LOF
- 需回推关注：25 只
- PRD pending_verify：161024, 161121, 160628

## 结论摘要

以下条目需 dev-001/dev-002 复核；本报告不直接修改 `assets/lof-watchlist-v1.csv`。

## 需回推条目

| code | 清单名称 | 官方名称 | type | scale_yi | status | 风险 | 说明 |
| --- | --- | --- | --- | ---: | --- | --- | --- |
| 163406 | 兴全合润分级混合(LOF) | 兴全合润混合A | active | 150.0 | active | name_changed | official_name=兴全合润混合A |
| 160706 | 嘉实沪深300(LOF) | 嘉实沪深300ETF联接A | index | 80.0 | active | name_changed | official_name=嘉实沪深300ETF联接A |
| 162411 | 华宝标普石油天然气(LOF)A | 华宝标普油气上游股票人民币A | industry | 40.0 | active | name_changed | official_name=华宝标普油气上游股票人民币A |
| 501050 | 华夏中证500ETF联接(LOF) | 华夏上证50AH优选指数A | index | 40.0 | active | name_changed | official_name=华夏上证50AH优选指数A |
| 162605 | 景顺长城鼎益混合(LOF) | 景顺长城鼎益混合(LOF)A | active | 30.0 | active | name_changed | official_name=景顺长城鼎益混合(LOF)A |
| 160222 | 国泰国证食品饮料行业指数(LOF) | 国泰国证食品饮料行业(LOF)A | industry | 25.0 | active | name_changed | official_name=国泰国证食品饮料行业(LOF)A |
| 161024 | 富国中证军工指数分级 | 富国中证军工指数(LOF)A | industry | 18.0 | pending_verify | pending_verify | PRD 标记为 pending_verify；需人工确认是否已转型/合并/清盘 |
| 166006 | 中欧成长优选混合(LOF) | 中欧行业成长混合(LOF)A | active | 15.0 | active | name_changed | official_name=中欧行业成长混合(LOF)A |
| 160516 | 诺安油气能源(LOF) | 博时证券公司ETF联接A | industry | 15.0 | active | name_changed | official_name=博时证券公司ETF联接A |
| 160119 | 南方中证500(LOF)A | 南方中证500ETF联接(LOF)A | index | 15.0 | active | name_changed | official_name=南方中证500ETF联接(LOF)A |
| 160630 | 鹏华动力增长混合(LOF) | 鹏华中证国防指数(LOF)A | active | 12.0 | active | name_changed | official_name=鹏华中证国防指数(LOF)A |
| 160632 | 鹏华中证酒指数(LOF) | 鹏华酒A | industry | 12.0 | active | name_changed | official_name=鹏华酒A |
| 160314 | 华夏行业精选混合(LOF) | 华夏行业混合(LOF) | active | 10.0 | active | name_changed | official_name=华夏行业混合(LOF) |
| 161121 | 易方达银行分级 | 易方达中证银行ETF联接(LOF)A | industry | 8.0 | pending_verify | pending_verify | PRD 标记为 pending_verify；需人工确认是否已转型/合并/清盘 |
| 160218 | 国泰国证医药卫生行业指数(LOF) | 国泰国证房地产行业指数A | industry | 8.0 | active | name_changed | official_name=国泰国证房地产行业指数A |
| 160628 | 鹏华金融地产分级 | 鹏华中证800地产指数(LOF)A | industry | 6.0 | pending_verify | pending_verify | PRD 标记为 pending_verify；需人工确认是否已转型/合并/清盘 |
| 160611 | 鹏华消费优选混合(LOF) | 鹏华优质治理混合(LOF)A | active | 5.0 | active | name_changed | official_name=鹏华优质治理混合(LOF)A |
| 161116 | 易方达黄金主题(LOF)A | 易方达黄金主题人民币A | industry | 5.0 | active | name_changed | official_name=易方达黄金主题人民币A |
| 161610 | 融通行业景气混合(LOF) | 融通领先成长混合(LOF)A | active | 5.0 | active | name_changed | official_name=融通领先成长混合(LOF)A |
| 161226 | 国投瑞银新兴产业混合(LOF) | 国投瑞银白银期货(LOF)A | active | 5.0 | active | name_changed | official_name=国投瑞银白银期货(LOF)A |
| 160213 | 国泰estoxx50(LOF) | 国泰纳斯达克100指数 | index | 4.0 | active | name_changed | official_name=国泰纳斯达克100指数 |
| 160212 | 国泰国证大宗商品(LOF) | 国泰估值优势混合(LOF)A | industry | 4.0 | active | name_changed | official_name=国泰估值优势混合(LOF)A |
| 160416 | 海富通中证内地低碳经济主题(LOF) | 华安标普全球石油指数(LOF)A | index | 3.0 | active | name_changed | official_name=华安标普全球石油指数(LOF)A |
| 160220 | 国泰国证房地产行业指数(LOF) | 国泰民益混合(LOF)A | industry | 3.0 | active | name_changed | official_name=国泰民益混合(LOF)A |
| 161227 | 国投瑞银中证创业新动力(LOF) | 国投瑞银深证100指数 | index | 3.0 | active | name_changed | official_name=国投瑞银深证100指数 |

## 全量验证明细

| code | 清单名称 | 官方名称 | type | status | 风险 |
| --- | --- | --- | --- | --- | --- |
| 161725 | 招商中证白酒指数(LOF)A | 招商中证白酒指数(LOF)A | index | active | ok |
| 161005 | 富国天惠成长混合(LOF)A | 富国天惠成长混合(LOF)A | active | active | ok |
| 163406 | 兴全合润分级混合(LOF) | 兴全合润混合A | active | active | name_changed |
| 160706 | 嘉实沪深300(LOF) | 嘉实沪深300ETF联接A | index | active | name_changed |
| 162411 | 华宝标普石油天然气(LOF)A | 华宝标普油气上游股票人民币A | industry | active | name_changed |
| 501050 | 华夏中证500ETF联接(LOF) | 华夏上证50AH优选指数A | index | active | name_changed |
| 160505 | 博时主题行业混合(LOF) | 博时主题行业混合(LOF) | active | active | ok |
| 162605 | 景顺长城鼎益混合(LOF) | 景顺长城鼎益混合(LOF)A | active | active | name_changed |
| 160222 | 国泰国证食品饮料行业指数(LOF) | 国泰国证食品饮料行业(LOF)A | industry | active | name_changed |
| 161024 | 富国中证军工指数分级 | 富国中证军工指数(LOF)A | industry | pending_verify | pending_verify |
| 166006 | 中欧成长优选混合(LOF) | 中欧行业成长混合(LOF)A | active | active | name_changed |
| 160516 | 诺安油气能源(LOF) | 博时证券公司ETF联接A | industry | active | name_changed |
| 160119 | 南方中证500(LOF)A | 南方中证500ETF联接(LOF)A | index | active | name_changed |
| 160630 | 鹏华动力增长混合(LOF) | 鹏华中证国防指数(LOF)A | active | active | name_changed |
| 160632 | 鹏华中证酒指数(LOF) | 鹏华酒A | industry | active | name_changed |
| 160314 | 华夏行业精选混合(LOF) | 华夏行业混合(LOF) | active | active | name_changed |
| 161121 | 易方达银行分级 | 易方达中证银行ETF联接(LOF)A | industry | pending_verify | pending_verify |
| 160218 | 国泰国证医药卫生行业指数(LOF) | 国泰国证房地产行业指数A | industry | active | name_changed |
| 161706 | 招商优质成长混合(LOF) | 招商优质成长混合(LOF) | active | active | ok |
| 161903 | 万家行业优选混合(LOF) | 万家行业优选混合(LOF) | active | active | ok |
| 160628 | 鹏华金融地产分级 | 鹏华中证800地产指数(LOF)A | industry | pending_verify | pending_verify |
| 160611 | 鹏华消费优选混合(LOF) | 鹏华优质治理混合(LOF)A | active | active | name_changed |
| 161116 | 易方达黄金主题(LOF)A | 易方达黄金主题人民币A | industry | active | name_changed |
| 161610 | 融通行业景气混合(LOF) | 融通领先成长混合(LOF)A | active | active | name_changed |
| 161226 | 国投瑞银新兴产业混合(LOF) | 国投瑞银白银期货(LOF)A | active | active | name_changed |
| 160213 | 国泰estoxx50(LOF) | 国泰纳斯达克100指数 | index | active | name_changed |
| 160212 | 国泰国证大宗商品(LOF) | 国泰估值优势混合(LOF)A | industry | active | name_changed |
| 160416 | 海富通中证内地低碳经济主题(LOF) | 华安标普全球石油指数(LOF)A | index | active | name_changed |
| 160220 | 国泰国证房地产行业指数(LOF) | 国泰民益混合(LOF)A | industry | active | name_changed |
| 161227 | 国投瑞银中证创业新动力(LOF) | 国投瑞银深证100指数 | index | active | name_changed |

## 元数据来源与局限

- 使用东方财富 `pingzhongdata/{code}.js` 校验基金代码是否存在、官方名称是否可解析。
- 该接口不能单独证明基金是否已转型、合并或清盘；`pending_verify` 条目仍需 dev-001/dev-002 做人工复核或引入公告/交易状态二次验证。
- 本轮只输出验证报告，不修改 PRD 或 watchlist CSV。
