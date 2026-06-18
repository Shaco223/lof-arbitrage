# watchlist 元数据验证数据源说明

## 背景

一阶段验证把东方财富 `pingzhongdata/{code}.js` 的 `fS_name` 直接当成场内 LOF 官方名称，导致 `name_changed` 比例达到 25/30。二次验证确认该接口更偏向场外基金份额或基金主份额信息，不能单独用于判断场内 LOF 代码是否改名、失效或转型。

## 二次验证使用的数据源

| 数据源 | 用途 | 可靠性 | 局限 |
| --- | --- | --- | --- |
| 东方财富场内行情 `push2.eastmoney.com/api/qt/stock/get` | 判断场内代码是否存在、是否有当前价格/成交额、场内简称 | 高 | 简称可能是缩写，不等于基金全称 |
| 东方财富 20 日 K 线 `push2his.eastmoney.com/api/qt/stock/kline/get` | 判断近 20 日成交活跃度 | 高 | 停牌/转型后可能返回空数组 |
| 天天基金估值 `fundgz.1234567.com.cn/js/{code}.js` | 判断是否可取 NAV / 估算净值 / 场外份额名称 | 中 | 返回场外份额名称，不必然等于场内简称 |
| 东方财富 `pingzhongdata/{code}.js` | 辅助核对基金主份额名称 | 低-中 | 不适合单独判断场内 LOF 名称，可能造成“错映射”假阳性 |
| `benchmark-mapping-v1.csv` | 检测 index_code 数字冲突 | 高（静态资产） | 只能发现冲突，不能自动判断哪一个代码正确 |

## 判定原则

1. `是否仍可交易` 以场内行情与 20 日 K 线为主。
2. `是否 LOF` 以场内名称、净值名称、watchlist 名称综合判断。
3. `是否 QDII` 以当前场内/净值名称为主；只有场内名称不可用时，才参考 watchlist 原始名称和 benchmark。
4. `真实改名` 必须至少有场内行情或净值源支持；仅 `pingzhongdata` 不一致不判真实改名。
5. `接口代码映射疑似错误` 指场内名称与净值名称彼此也不一致，或 watchlist 名称与两者均无有效重叠。
6. `replace` 优先由不可交易、20 日不活跃、代码对应资产明显错误触发。
7. `phase2_qdii` 仅用于当前代码实际对应 QDII/跨境品种，不因旧 benchmark 文案单独触发。

## 建议枚举

| 建议 | 含义 |
| --- | --- |
| `keep` | 可进入 watchlist-v2，名称/类型暂不改 |
| `rename` | 代码可保留，但建议按场内/净值名称更新名称或状态 |
| `type_fix` | 代码可保留，但 PRD type 需要修正 |
| `replace` | 不适合一期 watchlist，建议替换 |
| `phase2_qdii` | 当前代码实际为 QDII/跨境品种，放二期 |
| `manual_review` | 自动源不足，需人工看公告、基金合同或交易所信息 |

## BUG-001 / 399987 说明

`benchmark-mapping-v1.csv` 中存在：

- `160632`：`399987.CSI` / 中证酒指数
- `160212`：`399987.SZ` / 国证大宗商品指数

两者数字相同但后缀与组件名称不同，行情源适配时容易误取。二次验证报告只标记冲突，不直接修改 `benchmark-mapping-v1.csv`；是否修正需 dev-001/dev-002 走 benchmark CCR。
