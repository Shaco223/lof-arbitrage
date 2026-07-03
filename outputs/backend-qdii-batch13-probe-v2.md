# QDII 13 只 LOF 参考指数免费源批量 POC v2

- 探测时间: 2026-07-03T16:17:10+08:00
- 口径: 参考指数估算, 非交易所 IOPV (only reference-index estimate, NOT exchange IOPV)
- 范围: QDII 13 只 LOF 参考指数免费源批量 POC v2; 只读; 不接主链路; 不改 PRD §6 与 QDII_REFERENCE_MAPPINGS; 不写 uniCloud; v2 补测: E 类接口 + 混合口径复合指数拟合
- Cookie 模式: with_cookie
- 公式: `estimate_nav = fund_nav_t1 * (1 + index_change_pct) * (1 + fx_change_pct); estimate_premium = price / estimate_nav - 1`
- 样本量: 13
- 质量统计: {'high': 8, 'medium': 3, 'low': 2, 'unavailable': 0}
- v2 推荐 high 准入清单: ['501225', '161127', '161126', '161130', '161125', '161128', '160125', '501312']
- CCR: not_triggered_readonly_poc; 若后续把 qdii_reference_index_weights 或 E 类补测结论并入主链路, 需另立 PRD 1.6.2 CCR

## 任务一 - E 类接口补测

- 接口: `https://www.jisilu.cn/data/qdii/qdii_list/E?only_lof=y&only_etf=y&rp=300`
- 说明: v1 只抓默认类目, 501225 / 164824 / 501312 未命中; v2 追加 category=E 并按 fund_nav 存在性优先合并, 补齐 LOF 类 QDII 净值
- 通过 E 类恢复的代码: ['501225', '164824', '501312']

## 任务二 - 混合口径复合指数拟合

- 方法: 两因子 OLS (无截距): y_fund_daily = w_ref * ref_official_daily + w_hs * hkHSTECH_daily; 同时网格搜索 w_ref ∈ [0.3, 0.7] step 0.05, w_hs = 1 - w_ref
- 因子 ref 源: 集思录 detail_hists ref_increase_rt (官方参考指数日涨跌%); 免费替代 usKWEB 日 K 不可得的说明见 free_source_notes
- 因子 HSTECH 源: 腾讯 hkfqkline hkHSTECH 60 日 qfq 日 K
- 阈值: RMSE < 0.5% -> medium (仅在复合优于任一单因子时才提升); RMSE >= 1.0% -> 保持 low

### 164906 中概互联网LOF
- 样本 (对齐后交易日数): 47; 日期段: ['2026-04-16', '2026-06-30']
- 单因子 rmse: ref_only=0.002469, hstech_only=0.010079
- OLS 最优: w_ref=0.913906, w_hs=0.028539, rmse=0.002221 (n=47)
- 网格最优 (w_ref∈[0.3,0.7]): w_ref=0.7, w_hs=0.3, rmse=0.003581
- 复合质量判定: medium
- 备注: 腾讯 usfqkline qfqday 对美股 ETF 只回最新一帧(2017 后日 K 仅返回 1 行); 东财 push2his 106.KWEB 与 Yahoo v8 chart 当前断连; KWEB 免费日 K 30 日序列不可得

### 160644 港美互联网LOF
- 样本 (对齐后交易日数): 47; 日期段: ['2026-04-16', '2026-06-30']
- 单因子 rmse: ref_only=0.028371, hstech_only=0.027429
- OLS 最优: w_ref=-0.237362, w_hs=0.596474, rmse=0.025009 (n=47)
- 网格最优 (w_ref∈[0.3,0.7]): w_ref=0.3, w_hs=0.7, rmse=0.027317
- 复合质量判定: low
- 备注: 同 164906; usKWEB 免费日 K 不可得, 回归因子使用 H11136_ref(集思录官方参考指数)+HSTECH

## 免费源可得性备注
- usKWEB (KraneShares 中概互联网 ETF) 免费日 K 30 日序列不可得: 腾讯 usfqkline qfqday 对美股 ETF 仅回传最新 1 帧; 东财 push2his 106.KWEB 与 Yahoo v8 chart 当前断连
- 港股 hkHSTECH 通过腾讯 hkfqkline 可稳定拿 60 日 qfq 日 K
- H11136 官方参考指数日涨跌% 通过集思录 detail_hists 可得, 但需 Cookie

## 13 只质量矩阵 v1 vs v2

| code | v1 | v2 | delta | nav_source_v2 |
|---|---|---|---|---|
| 501225 | unavailable | high | upgraded | jisilu_qdii |
| 161127 | high | high | unchanged | jisilu_qdii |
| 161126 | high | high | unchanged | jisilu_qdii |
| 161130 | high | high | unchanged | jisilu_qdii |
| 161125 | high | high | unchanged | jisilu_qdii |
| 164906 | low | low | unchanged | jisilu_qdii |
| 161128 | high | high | unchanged | jisilu_qdii |
| 160140 | medium | medium | unchanged | jisilu_qdii |
| 164824 | unavailable | medium | upgraded | jisilu_qdii |
| 162415 | medium | medium | unchanged | jisilu_qdii |
| 160125 | high | high | unchanged | jisilu_qdii |
| 501312 | high | high | unchanged | jisilu_qdii |
| 160644 | low | low | unchanged | jisilu_qdii |

## 样本明细 (v2 单指数路径)

| code | name | corr | price | price_chg | fund_nav_t1 | nav_dt | nav_src | ref_idx | idx_chg | fx | fx_chg | est_nav | est_prem | quality |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 501225 | 全球芯片LOF | strong | 4.507 | 0.001778 | 3.5887 | 2026-07-01 | jisilu_qdii | usSOXX | -0.055661 | fx_susdcny | -0.001531 | 3.383761 | 0.33195 | high |
| 161127 | 标普生物科技LOF | strong | 2.16 | 0.038462 | 2.0839 | 2026-07-01 | jisilu_qdii | usXBI | 0.024976 | fx_susdcny | -0.001531 | 2.132677 | 0.012812 | high |
| 161126 | 标普医疗保健LOF | strong | 2.019 | 0.024353 | 1.9653 | 2026-07-01 | jisilu_qdii | usXLV | 0.026326 | fx_susdcny | -0.001531 | 2.01395 | 0.002508 | high |
| 161130 | 纳指100LOF | strong | 4.614 | 0.003262 | 4.504 | 2026-07-01 | jisilu_qdii | usNDX | -0.0161 | fx_susdcny | -0.001531 | 4.424701 | 0.042782 | high |
| 161125 | 标普500LOF | strong | 3.144 | 0.010932 | 3.0893 | 2026-07-01 | jisilu_qdii | usINX | 1e-06 | fx_susdcny | -0.001531 | 3.084573 | 0.019266 | high |
| 164906 | 中概互联网LOF | weak | 0.9 | 0.007839 | 0.8884 | 2026-07-01 | jisilu_qdii | usKWEB | -0.005175 | fx_susdcny | -0.001531 | 0.882449 | 0.019889 | low |
| 161128 | 标普信息科技LOF | strong | 6.658 | 0.006348 | 6.5366 | 2026-07-01 | jisilu_qdii | usXLK | -0.027098 | fx_susdcny | -0.001531 | 6.349735 | 0.048548 | high |
| 160140 | 美国REIT精选LOF | medium | 1.473 | 0.016563 | 1.4489 | 2026-07-01 | jisilu_qdii | usVNQ | 0.012394 | fx_susdcny | -0.001531 | 1.464612 | 0.005727 | medium |
| 164824 | 印度基金LOF | medium | 1.315 | 0.00921 | 1.3111 | 2026-07-01 | jisilu_qdii | usINDA | 0.007112 | fx_susdcny | -0.001531 | 1.318403 | -0.002581 | medium |
| 162415 | 美国消费LOF | medium | 2.886 | 0.0 | 2.912 | 2026-07-01 | jisilu_qdii | usXLY | -0.008214 | fx_susdcny | -0.001531 | 2.883659 | 0.000812 | medium |
| 160125 | 南方香港LOF | strong | 1.719 | 0.02139 | 1.7376 | 2026-07-01 | jisilu_qdii | hkHSI | 0.011938 | fx_shkdcny | -0.001314 | 1.756033 | -0.021089 | high |
| 501312 | 海外科技LOF | strong | 2.367 | 0.001693 | 2.4085 | 2026-07-01 | jisilu_qdii | usXLK | -0.027098 | fx_susdcny | -0.001531 | 2.339647 | 0.011691 | high |
| 160644 | 港美互联网LOF | weak | 1.972 | 0.001015 | 2.0735 | 2026-07-01 | jisilu_qdii | usKWEB | -0.005175 | fx_susdcny | -0.001531 | 2.059612 | -0.042538 | low |

## 结构性建议 (报告级, 不实装)
- 建议字段: `qdii_reference_index_weights` · 形状: `list[{symbol: str, weight: number}]`
- 用途: 支持 mixed-exposure QDII (如 164906 / 160644) 用两个以上参考指数加权拟合 estimate_nav; PRD 1.6 只支持单指数, 引入该结构属于结构性变更
- CCR: 需 PRD 1.6.2 · required=True
- 本轮 POC 影响: 本轮不实装, 仅在报告中建议

## 匿名 vs Cookie 对比

- 匿名模式质量: {'high': 7, 'medium': 3, 'low': 2, 'unavailable': 1}
- 匿名模式 high 清单: ['161127', '161126', '161130', '161125', '161128', '160125', '501312']
- Cookie 模式质量: {'high': 8, 'medium': 3, 'low': 2, 'unavailable': 0}
- Cookie 模式 high 清单: ['501225', '161127', '161126', '161130', '161125', '161128', '160125', '501312']

## 数据源稳定性判断
- market_price: tencent_quote 覆盖所有 13 只 A 股场内 LOF/ETF
- nav_t1: 集思录 qdii_list 需 Cookie 才能覆盖 267 条; 匿名仅前 20 条; fundgz 对 501225 / 164906 / 164824 / 160125 常返回空 jsonpgz()
- reference_index_us_broad: usINX / usNDX / usIXIC / usDJI 腾讯免费实时可得
- reference_index_us_sector_etf: 美股行业指数(SPSIBI / S5HLTH / S5INFT)免费源不可得; 用 SPDR/iShares ETF 代理: usXBI / usXLV / usXLK / usXLY / usVNQ / usSOXX / usIYW / usKWEB / usINDA
- reference_index_hk: hkHSI / hkHSCEI / hkHSTECH 腾讯免费实时可得
- fx: 新浪 fx_susdcny / fx_shkdcny 稳定可得; 涨跌幅字段为百分比数

