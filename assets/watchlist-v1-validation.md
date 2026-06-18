# watchlist-v1 元数据验证报告

- 生成时间：2026-06-18T11:42:01+08:00
- 一阶段数据源：东方财富 pingzhongdata
- 二次验证数据源：东方财富场内行情 / 东方财富 20 日 K 线 / 天天基金估值净值 / 东方财富 pingzhongdata 辅助名称
- 验证范围：30 只 LOF
- 一阶段需回推关注：25 只
- PRD pending_verify：161024, 161121, 160628
- 二次建议统计：keep=8, rename=4, type_fix=0, replace=13, phase2_qdii=4, manual_review=1

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

## 二次验证结果

### 处理建议汇总

| 建议 | code | 说明 |
| --- | --- | --- |
| keep | 161725, 161005, 163406, 160706, 160505, 162605, 160119, 161903 | 可保留原条目 |
| rename | 501050, 161024, 160632, 160220 | 建议按场内/净值多源名称更新名称或状态 |
| type_fix | 无 | 建议修正 type |
| replace | 160222, 166006, 160516, 160630, 160314, 161121, 160218, 161706, 160628, 160611, 161610, 160212, 161227 | 不适合一期，建议替换 |
| phase2_qdii | 162411, 161116, 160213, 160416 | QDII 或跨境品种，建议二期处理 |
| manual_review | 161226 | 需人工公告/交易规则复核 |

### 二次验证明细

| code | 清单名称 | 场内名称 | 净值名称 | 交易状态 | 类型 | LOF | QDII | 可取净值 | 可取场内行情 | 最新规模(亿) | 20日均成交额 | 活跃度 | 多源名称比对 | 建议 | 证据 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: | --- | --- | --- | --- |
| 161725 | 招商中证白酒指数(LOF)A | 白酒基金LOF | 招商中证白酒指数(LOF)A | tradable | 指数 | Y | N | Y | Y | 300.00 | 49847398.33 | active | multi_source_match | keep | venue=白酒基金LOF price=0.526 amount=22303261.399; nav=招商中证白酒指数(LOF)A nav_date=2026-06-17; activity=active avg20=49847398.33; name_compare=multi_source_match |
| 161005 | 富国天惠成长混合(LOF)A | 富国天惠LOF | 富国天惠成长混合(LOF)A | tradable | 主动 | Y | N | Y | Y | 180.00 | 9913354.69 | active | multi_source_match | keep | venue=富国天惠LOF price=3.187 amount=7083320.532; nav=富国天惠成长混合(LOF)A nav_date=2026-06-17; activity=active avg20=9913354.69; name_compare=multi_source_match |
| 163406 | 兴全合润分级混合(LOF) | 兴全合润LOF | 兴全合润混合A | tradable | 主动 | Y | N | Y | Y | 150.00 | 13804537.86 | active | multi_source_match | keep | venue=兴全合润LOF price=2.64 amount=6338805.023; nav=兴全合润混合A nav_date=2026-06-17; activity=active avg20=13804537.86; name_compare=multi_source_match |
| 160706 | 嘉实沪深300(LOF) | 沪深300LOF | 嘉实沪深300ETF联接A | tradable | 指数 | Y | N | Y | Y | 80.00 | 2097902.60 | low_active | multi_source_match | keep | venue=沪深300LOF price=1.25 amount=962616.116; nav=嘉实沪深300ETF联接A nav_date=2026-06-17; activity=low_active avg20=2097902.6; name_compare=multi_source_match |
| 162411 | 华宝标普石油天然气(LOF)A | 华宝油气LOF | 华宝标普油气上游股票人民币A | tradable | QDII | Y | Y | Y | Y | 40.00 | 147797456.68 | active | interface_mapping_suspect | phase2_qdii | venue=华宝油气LOF price=0.814 amount=51976661.42; nav=华宝标普油气上游股票人民币A nav_date=2026-06-16; activity=active avg20=147797456.68; name_compare=interface_mapping_suspect |
| 501050 | 华夏中证500ETF联接(LOF) | 50AHLOF | 华夏上证50AH优选指数A | tradable | 指数 | Y | N | Y | Y | 40.00 | 861523.65 | low_active | true_rename_or_share_class_change | rename | venue=50AHLOF price=1.731 amount=690074.0; nav=华夏上证50AH优选指数A nav_date=2026-06-17; activity=low_active avg20=861523.65; name_compare=true_rename_or_share_class_change |
| 160505 | 博时主题行业混合(LOF) | 博时主题LOF | 博时主题行业混合(LOF) | tradable | 主动 | Y | N | Y | Y | 30.00 | 1045715.17 | low_active | multi_source_match | keep | venue=博时主题LOF price=1.139 amount=1377349.928; nav=博时主题行业混合(LOF) nav_date=2026-06-17; activity=low_active avg20=1045715.17; name_compare=multi_source_match |
| 162605 | 景顺长城鼎益混合(LOF) | 景顺鼎益LOF | 景顺长城鼎益混合(LOF)A | tradable | 主动 | Y | N | Y | Y | 30.00 | 9312995.74 | active | venue_nav_divergence | keep | venue=景顺鼎益LOF price=1.883 amount=7423606.086; nav=景顺长城鼎益混合(LOF)A nav_date=2026-06-17; activity=active avg20=9312995.74; name_compare=venue_nav_divergence |
| 160222 | 国泰国证食品饮料行业指数(LOF) | 食品LOF | 国泰国证食品饮料行业(LOF)A | tradable | 行业指数 | Y | N | Y | Y | 25.00 | 202064.05 | inactive | multi_source_match | replace | venue=食品LOF price=0.635 amount=82480.195; nav=国泰国证食品饮料行业(LOF)A nav_date=2026-06-17; activity=inactive avg20=202064.05; name_compare=multi_source_match |
| 161024 | 富国中证军工指数分级 | 军工LOF | 富国中证军工指数(LOF)A | tradable | 行业指数 | Y | N | Y | Y | 18.00 | 1307124.97 | low_active | multi_source_match | rename | venue=军工LOF price=1.25 amount=510091.318; nav=富国中证军工指数(LOF)A nav_date=2026-06-17; activity=low_active avg20=1307124.97; name_compare=multi_source_match |
| 166006 | 中欧成长优选混合(LOF) | 中欧成长LOF | 中欧行业成长混合(LOF)A | tradable | 主动 | Y | N | Y | Y | 15.00 | 125392.17 | inactive | multi_source_match | replace | venue=中欧成长LOF price=2.507 amount=6013.6; nav=中欧行业成长混合(LOF)A nav_date=2026-06-17; activity=inactive avg20=125392.17; name_compare=multi_source_match |
| 160516 | 诺安油气能源(LOF) | 证券指数基金 | 博时证券公司ETF联接A | not_tradable_or_suspended | 行业指数 | Y | N | Y | Y | 15.00 | - | no_kline | true_rename_or_share_class_change | replace | venue=证券指数基金 price=- amount=-; nav=博时证券公司ETF联接A nav_date=2026-06-17; activity=no_kline avg20=-; name_compare=true_rename_or_share_class_change |
| 160119 | 南方中证500(LOF)A | 500ETF联接LOF | 南方中证500ETF联接(LOF)A | tradable | 指数 | Y | N | Y | Y | 15.00 | 1231948.34 | low_active | multi_source_match | keep | venue=500ETF联接LOF price=2.412 amount=846978.492; nav=南方中证500ETF联接(LOF)A nav_date=2026-06-17; activity=low_active avg20=1231948.34; name_compare=multi_source_match |
| 160630 | 鹏华动力增长混合(LOF) | 国防LOF | 鹏华中证国防指数(LOF)A | tradable | 主动 | Y | N | Y | Y | 12.00 | 358994.84 | inactive | true_rename_or_share_class_change | replace | venue=国防LOF price=1.097 amount=353110.84; nav=鹏华中证国防指数(LOF)A nav_date=2026-06-17; activity=inactive avg20=358994.84; name_compare=true_rename_or_share_class_change |
| 160632 | 鹏华中证酒指数(LOF) | 酒LOF | 鹏华酒A | tradable | 行业指数 | Y | N | Y | Y | 12.00 | 4209709.31 | low_active | true_rename_or_share_class_change | rename | venue=酒LOF price=0.255 amount=1589828.807; nav=鹏华酒A nav_date=2026-06-17; activity=low_active avg20=4209709.31; name_compare=true_rename_or_share_class_change |
| 160314 | 华夏行业精选混合(LOF) | 华夏行业LOF | 华夏行业混合(LOF) | tradable | 主动 | Y | N | Y | Y | 10.00 | 95403.78 | inactive | multi_source_match | replace | venue=华夏行业LOF price=1.604 amount=161483.639; nav=华夏行业混合(LOF) nav_date=2026-06-17; activity=inactive avg20=95403.78; name_compare=multi_source_match |
| 161121 | 易方达银行分级 | 银行LOF易方达 | 易方达中证银行ETF联接(LOF)A | tradable | 行业指数 | Y | N | Y | Y | 8.00 | 141604.51 | inactive | interface_mapping_suspect | replace | venue=银行LOF易方达 price=1.55 amount=132637.35; nav=易方达中证银行ETF联接(LOF)A nav_date=2026-06-17; activity=inactive avg20=141604.51; name_compare=interface_mapping_suspect |
| 160218 | 国泰国证医药卫生行业指数(LOF) | 房地产LOF | 国泰国证房地产行业指数A | tradable | 行业指数 | Y | N | Y | Y | 8.00 | 93720.11 | inactive | true_rename_or_share_class_change | replace | venue=房地产LOF price=0.563 amount=59377.8; nav=国泰国证房地产行业指数A nav_date=2026-06-17; activity=inactive avg20=93720.11; name_compare=true_rename_or_share_class_change |
| 161706 | 招商优质成长混合(LOF) | 招商成长LOF | 招商优质成长混合(LOF) | tradable | 主动 | Y | N | Y | Y | 8.00 | 108167.57 | inactive | venue_nav_divergence | replace | venue=招商成长LOF price=3.891 amount=46845.9; nav=招商优质成长混合(LOF) nav_date=2026-06-17; activity=inactive avg20=108167.57; name_compare=venue_nav_divergence |
| 161903 | 万家行业优选混合(LOF) | 万家行业优选LOF | 万家行业优选混合(LOF) | tradable | 主动 | Y | N | Y | Y | 8.00 | 6587814.33 | active | multi_source_match | keep | venue=万家行业优选LOF price=1.714 amount=8414715.501; nav=万家行业优选混合(LOF) nav_date=2026-06-17; activity=active avg20=6587814.33; name_compare=multi_source_match |
| 160628 | 鹏华金融地产分级 | 地产LOF | 鹏华中证800地产指数(LOF)A | tradable | 行业指数 | Y | N | Y | Y | 6.00 | 77790.75 | inactive | true_rename_or_share_class_change | replace | venue=地产LOF price=0.465 amount=6322.8; nav=鹏华中证800地产指数(LOF)A nav_date=2026-06-17; activity=inactive avg20=77790.75; name_compare=true_rename_or_share_class_change |
| 160611 | 鹏华消费优选混合(LOF) | 鹏华优质治理LOF | 鹏华优质治理混合(LOF)A | tradable | 主动 | Y | N | Y | Y | 5.00 | 58480.42 | inactive | true_rename_or_share_class_change | replace | venue=鹏华优质治理LOF price=1.259 amount=14031.723; nav=鹏华优质治理混合(LOF)A nav_date=2026-06-17; activity=inactive avg20=58480.42; name_compare=true_rename_or_share_class_change |
| 161116 | 易方达黄金主题(LOF)A | 黄金主题LOF | 易方达黄金主题人民币A | tradable | QDII | Y | Y | Y | Y | 5.00 | 18010542.95 | active | multi_source_match | phase2_qdii | venue=黄金主题LOF price=1.6 amount=8294315.912; nav=易方达黄金主题人民币A nav_date=2026-06-16; activity=active avg20=18010542.95; name_compare=multi_source_match |
| 161610 | 融通行业景气混合(LOF) | 融通领先成长LOF | 融通领先成长混合(LOF)A | tradable | 主动 | Y | N | Y | Y | 5.00 | 443297.94 | inactive | true_rename_or_share_class_change | replace | venue=融通领先成长LOF price=2.254 amount=609038.659; nav=融通领先成长混合(LOF)A nav_date=2026-06-17; activity=inactive avg20=443297.94; name_compare=true_rename_or_share_class_change |
| 161226 | 国投瑞银新兴产业混合(LOF) | 国投白银LOF | - | tradable | 主动 | Y | N | N | Y | 5.00 | 276338398.16 | active | ping_share_class_or_mapping_diff | manual_review | venue=国投白银LOF price=1.998 amount=155889774.234; nav=- nav_date=-; activity=active avg20=276338398.16; name_compare=ping_share_class_or_mapping_diff |
| 160213 | 国泰estoxx50(LOF) | - | 国泰纳斯达克100指数 | not_tradable_or_suspended | QDII | Y | Y | Y | N | 4.00 | - | no_kline | ping_share_class_or_mapping_diff | phase2_qdii | venue=- price=- amount=-; nav=国泰纳斯达克100指数 nav_date=2026-06-16; activity=no_kline avg20=-; name_compare=ping_share_class_or_mapping_diff |
| 160212 | 国泰国证大宗商品(LOF) | 国泰估值LOF | 国泰估值优势混合(LOF)A | tradable | 行业指数 | Y | N | Y | Y | 4.00 | 410658.76 | inactive | true_rename_or_share_class_change | replace | venue=国泰估值LOF price=4.476 amount=323073.826; nav=国泰估值优势混合(LOF)A nav_date=2026-06-17; activity=inactive avg20=410658.76; name_compare=true_rename_or_share_class_change |
| 160416 | 海富通中证内地低碳经济主题(LOF) | 石油基金LOF | 华安标普全球石油指数(LOF)A | tradable | QDII | Y | Y | Y | Y | 3.00 | 63500701.05 | active | true_rename_or_share_class_change | phase2_qdii | venue=石油基金LOF price=1.968 amount=6068284.121; nav=华安标普全球石油指数(LOF)A nav_date=2026-06-16; activity=active avg20=63500701.05; name_compare=true_rename_or_share_class_change |
| 160220 | 国泰国证房地产行业指数(LOF) | 国泰民益LOF | 国泰民益混合(LOF)A | tradable | 行业指数 | Y | N | Y | Y | 3.00 | 3643141.13 | low_active | true_rename_or_share_class_change | rename | venue=国泰民益LOF price=5.771 amount=2549483.127; nav=国泰民益混合(LOF)A nav_date=2026-06-17; activity=low_active avg20=3643141.13; name_compare=true_rename_or_share_class_change |
| 161227 | 国投瑞银中证创业新动力(LOF) | 国投深证100LOF | 国投瑞银深证100指数 | tradable | 指数 | Y | N | Y | Y | 3.00 | 426141.25 | inactive | interface_mapping_suspect | replace | venue=国投深证100LOF price=1.826 amount=257199.148; nav=国投瑞银深证100指数 nav_date=2026-06-17; activity=inactive avg20=426141.25; name_compare=interface_mapping_suspect |

### 重点核查结论

- `501050`：场内行情名称为 `50AHLOF`，净值源名称为 `华夏上证50AH优选指数A`；原 watchlist 名称 `华夏中证500ETF联接(LOF)` 疑似资产清单误填，应进入 `rename/manual_review`，不是 pingzhongdata 单点错映射。
- `160516`：场内行情显示 `证券指数基金` 且 20 日 K 线为空，净值源为 `博时证券公司ETF联接A`；原 `诺安油气能源(LOF)` 疑似代码已不匹配，一期建议 `replace` 或人工确认。
- `160218`：场内行情为 `房地产LOF`，净值源为 `国泰国证房地产行业指数A`；原 `国泰国证医药卫生行业指数(LOF)` 疑似代码对应资产错误，且 20 日成交不活跃，建议 `replace/manual_review`。
- `161024`：有场内行情与净值，分级名称已转为 `军工LOF` / `富国中证军工指数(LOF)A`，建议 `rename` 后可保留观察。
- `161121 / 160628`：有场内行情与净值，但 20 日成交不活跃；如一期坚持成交额阈值，建议 `replace`，否则需人工降级保留。
- `399987`：benchmark 自动检测发现同数字不同后缀/名称冲突，详见 `benchmark mapping 冲突核查`；建议 dev-002/dev-001 复核，可能触发 benchmark CCR。


## benchmark mapping 冲突核查

| 数字代码 | 涉及 index_code | 组件名称 | 涉及 LOF | 结论 |
| --- | --- | --- | --- | --- |
| 399987 | 399987.CSI, 399987.SZ | 中证酒指数, 国证大宗商品指数 | 160212, 160632 | 同一数字代码映射到多个后缀或组件名称，需人工确认行情源代码 |

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

- 一阶段报告使用东方财富 `pingzhongdata/{code}.js` 校验基金名称，但该接口返回的多为场外基金份额名称，不能直接代表场内 LOF 代码名称。
- 二次验证以场内行情代码是否存在、是否有成交、是否可取净值为主，pingzhongdata 只作为辅助名称证据。
- 该报告不能单独证明基金是否已转型、合并或清盘；`manual_review` 条目仍需 dev-001/dev-002 做人工复核或公告确认。
- 本轮只输出验证报告，不修改 PRD 或 watchlist CSV。
