# QDII 13 只 LOF 参考指数免费源批量 POC

- 探测时间: 2026-07-03T15:18:44+08:00
- 口径: 参考指数估算, 非交易所 IOPV (only reference-index estimate, NOT exchange IOPV)
- 范围: QDII 13 只 LOF 参考指数免费源批量 POC; 只读; 不接主链路; 不改 PRD §6 与 QDII_REFERENCE_MAPPINGS; 不写 uniCloud
- Cookie 模式: with_cookie
- 公式: `estimate_nav = fund_nav_t1 * (1 + index_change_pct) * (1 + fx_change_pct); estimate_premium = price / estimate_nav - 1`
- 样本量: 13
- 质量统计: {'high': 7, 'medium': 2, 'low': 2, 'unavailable': 2}
- 推荐 high 准入清单: ['161127', '161126', '161130', '161125', '161128', '160125', '501312']
- CCR: not_triggered_readonly_poc_no_prd6_change

## 样本明细

| code | name | region | corr | price | price_chg | fund_nav_t1 | nav_dt | nav_src | ref_idx | idx_chg | fx | fx_chg | est_nav | est_prem | quality | reasons |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 501225 | 全球芯片LOF | us | strong | 4.507 | 0.001778 | None |  | None | usSOXX | -0.055661 | fx_susdcny | -0.001104 | None | None | unavailable | jisilu_qdii_row_not_found_with_cookie;fundgz_empty_jsonpgz |
| 161127 | 标普生物科技LOF | us | strong | 2.16 | 0.038462 | 2.0839 | 2026-07-01 | jisilu_qdii | usXBI | 0.024976 | fx_susdcny | -0.001104 | 2.133589 | 0.012379 | high |  |
| 161126 | 标普医疗保健LOF | us | strong | 2.019 | 0.024353 | 1.9653 | 2026-07-01 | jisilu_qdii | usXLV | 0.026326 | fx_susdcny | -0.001104 | 2.014812 | 0.002079 | high |  |
| 161130 | 纳指100LOF | us | strong | 4.614 | 0.003262 | 4.504 | 2026-07-01 | jisilu_qdii | usNDX | -0.0161 | fx_susdcny | -0.001104 | 4.426593 | 0.042337 | high |  |
| 161125 | 标普500LOF | us | strong | 3.144 | 0.010932 | 3.0893 | 2026-07-01 | jisilu_qdii | usINX | 1e-06 | fx_susdcny | -0.001104 | 3.085892 | 0.01883 | high | 回归对照: 现有 QDII_REFERENCE_MAPPINGS high 标的 |
| 164906 | 中概互联网LOF | us_hk_mixed | weak | 0.9 | 0.007839 | 0.8884 | 2026-07-01 | jisilu_qdii | usKWEB | -0.005175 | fx_susdcny | -0.001104 | 0.882827 | 0.019452 | low | 混合口径: 美股中概 + 港股中概; 单一 KWEB 拟合误差偏大 |
| 161128 | 标普信息科技LOF | us | strong | 6.658 | 0.006348 | 6.5366 | 2026-07-01 | jisilu_qdii | usXLK | -0.027098 | fx_susdcny | -0.001104 | 6.35245 | 0.0481 | high |  |
| 160140 | 美国REIT精选LOF | us | medium | 1.473 | 0.016563 | 1.4489 | 2026-07-01 | jisilu_qdii | usVNQ | 0.012394 | fx_susdcny | -0.001104 | 1.465238 | 0.005297 | medium |  |
| 164824 | 印度基金LOF | india | medium | 1.315 | 0.00921 | None |  | None | usINDA | 0.007112 | fx_susdcny | -0.001104 | None | None | unavailable | jisilu_qdii_row_not_found_with_cookie;fundgz_empty_jsonpgz;POC v1 曾标 unavailable; 本次复测尝试 usINDA / gb_inda 代理 |
| 162415 | 美国消费LOF | us | medium | 2.886 | 0.0 | 2.912 | 2026-07-01 | jisilu_qdii | usXLY | -0.008214 | fx_susdcny | -0.001104 | 2.884892 | 0.000384 | medium |  |
| 160125 | 南方香港LOF | hong_kong | strong | 1.719 | 0.02139 | 1.7376 | 2026-07-01 | jisilu_qdii | hkHSI | 0.012808 | fx_shkdcny | -0.001219 | 1.75771 | -0.022023 | high |  |
| 501312 | 海外科技LOF | us | strong | 2.367 | 0.001693 | 2.4085 | 2026-07-01 | fundgz | usXLK | -0.027098 | fx_susdcny | -0.001104 | 2.340648 | 0.011258 | high |  |
| 160644 | 港美互联网LOF | us_hk_mixed | weak | 1.972 | 0.001015 | 2.0735 | 2026-07-01 | jisilu_qdii | usKWEB | -0.005175 | fx_susdcny | -0.001104 | 2.060492 | -0.042947 | low | 混合口径: 港股互联网 + 美股中概; 单一指数拟合误差大 |

## 每只候选指数源可得性

### 501225 全球芯片LOF
- [OK] usSOXX (tencent): change_pct=-0.055661 · 半导体宽基代理指数
- [OK] gb_soxx (sina_gb): change_pct=-0.0557
- [OK] usSMH (tencent): change_pct=-0.045402 · 备用半导体宽基代理

### 161127 标普生物科技LOF
- [OK] usXBI (tencent): change_pct=0.024976 · 跟踪 SPSIBI 的宽基 ETF 代理
- [OK] gb_xbi (sina_gb): change_pct=0.025
- [OK] usIBB (tencent): change_pct=0.02935 · 纳斯达克生物技术备用代理

### 161126 标普医疗保健LOF
- [OK] usXLV (tencent): change_pct=0.026326 · 标普医疗保健行业代理指数
- [OK] gb_xlv (sina_gb): change_pct=0.0263

### 161130 纳指100LOF
- [OK] usNDX (tencent): change_pct=-0.0161 · 直接跟踪指数
- [OK] gb_ndx (sina_gb): change_pct=-0.0161

### 161125 标普500LOF
- [OK] usINX (tencent): change_pct=1e-06 · 直接跟踪指数; 回归对照
- [OK] gb_inx (sina_gb): change_pct=0.0

### 164906 中概互联网LOF
- [OK] usKWEB (tencent): change_pct=-0.005175 · 单一美股中概 ETF 代理; 港股中概敞口未覆盖
- [OK] gb_kweb (sina_gb): change_pct=-0.0052

### 161128 标普信息科技LOF
- [OK] usXLK (tencent): change_pct=-0.027098 · 标普信息科技行业代理
- [OK] gb_xlk (sina_gb): change_pct=-0.0271
- [OK] usIYW (tencent): change_pct=-0.021186 · 备用美国科技代理

### 160140 美国REIT精选LOF
- [OK] usVNQ (tencent): change_pct=0.012394 · 美国 REIT 宽基代理; 与精选子集有跟踪误差
- [OK] gb_vnq (sina_gb): change_pct=0.0124

### 164824 印度基金LOF
- [OK] usINDA (tencent): change_pct=0.007112 · MSCI 印度宽基 ETF 代理; 与 SENSEX/NIFTY 高度相关
- [OK] gb_inda (sina_gb): change_pct=0.0071

### 162415 美国消费LOF
- [OK] usXLY (tencent): change_pct=-0.008214 · 消费行业宽基代理; 标普美国消费口径可能包含必需消费
- [OK] gb_xly (sina_gb): change_pct=-0.0082

### 160125 南方香港LOF
- [OK] hkHSI (tencent): change_pct=0.012808 · 恒生宽基指数
- [OK] hkHSCEI (tencent): change_pct=0.011521 · 国企指数备用

### 501312 海外科技LOF
- [OK] usXLK (tencent): change_pct=-0.027098 · 美国科技行业代理
- [OK] gb_xlk (sina_gb): change_pct=-0.0271
- [OK] usIYW (tencent): change_pct=-0.021186 · 备用美国科技代理

### 160644 港美互联网LOF
- [OK] usKWEB (tencent): change_pct=-0.005175 · 美股中概代理
- [OK] hkHSTECH (tencent): change_pct=0.011061 · 港股互联网科技代理

## 准入建议

- 501225 全球芯片LOF: unavailable · jisilu_qdii_row_not_found_with_cookie;fundgz_empty_jsonpgz
- 161127 标普生物科技LOF: high · 候选指数强相关免费源可得, 指数/汇率/净值三要素齐备
- 161126 标普医疗保健LOF: high · 候选指数强相关免费源可得, 指数/汇率/净值三要素齐备
- 161130 纳指100LOF: high · 候选指数强相关免费源可得, 指数/汇率/净值三要素齐备
- 161125 标普500LOF: high · 回归对照: 现有 QDII_REFERENCE_MAPPINGS high 标的
- 164906 中概互联网LOF: low · 混合口径: 美股中概 + 港股中概; 单一 KWEB 拟合误差偏大
- 161128 标普信息科技LOF: high · 候选指数强相关免费源可得, 指数/汇率/净值三要素齐备
- 160140 美国REIT精选LOF: medium · 
- 164824 印度基金LOF: unavailable · jisilu_qdii_row_not_found_with_cookie;fundgz_empty_jsonpgz;POC v1 曾标 unavailable; 本次复测尝试 usINDA / gb_inda 代理
- 162415 美国消费LOF: medium · 
- 160125 南方香港LOF: high · 候选指数强相关免费源可得, 指数/汇率/净值三要素齐备
- 501312 海外科技LOF: high · 候选指数强相关免费源可得, 指数/汇率/净值三要素齐备
- 160644 港美互联网LOF: low · 混合口径: 港股互联网 + 美股中概; 单一指数拟合误差大

## 匿名 vs Cookie 对比

- 匿名模式质量: {'high': 6, 'medium': 2, 'low': 1, 'unavailable': 4}
- 匿名模式 high 清单: ['161127', '161126', '161130', '161125', '161128', '501312']
- Cookie 模式质量: {'high': 7, 'medium': 2, 'low': 2, 'unavailable': 2}
- Cookie 模式 high 清单: ['161127', '161126', '161130', '161125', '161128', '160125', '501312']
- Cookie 相对匿名新增 high: ['160125']
- Cookie 相对匿名减少 high: []

## 数据源稳定性判断

- market_price: tencent_quote 覆盖所有 13 只 A 股场内 LOF/ETF
- nav_t1: 集思录 qdii_list 需 Cookie 才能覆盖 267 条; 匿名仅前 20 条; fundgz 对 501225 / 164906 / 164824 / 160125 常返回空 jsonpgz()
- reference_index_us_broad: usINX / usNDX / usIXIC / usDJI 腾讯免费实时可得
- reference_index_us_sector_etf: 美股行业指数(SPSIBI / S5HLTH / S5INFT)免费源不可得; 用 SPDR/iShares ETF 代理: usXBI / usXLV / usXLK / usXLY / usVNQ / usSOXX / usIYW / usKWEB / usINDA
- reference_index_hk: hkHSI / hkHSCEI / hkHSTECH 腾讯免费实时可得
- fx: 新浪 fx_susdcny / fx_shkdcny 稳定可得; 涨跌幅字段为百分比数

