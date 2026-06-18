# BUG-004 / AC-P1 NAV 反推真实溢价口径

## 目标

为 AC-P1 提供后端算法口径，避免测试在“官方 NAV / IOPV / 估算净值”之间混用。

## 名词口径

- `official_nav_t`：基金公司披露的 T 日单位净值，通常盘后发布，是 AC-P1 的真实净值锚点。
- `close_price_t`：T 日二级市场收盘价。
- `iopv_est_t_m`：T 日第 m 分钟由拉取器估算出的实时净值，写入 PRD §6 的 `iopv` 字段。
- `premium_realtime_t_m`：T 日第 m 分钟实时溢价，写入 PRD §6 的 `premium` 字段。
- `premium_truth_close_t`：用官方 NAV 反推的 T 日收盘真实溢价，写入 `lof_history.premium_close`。

## 反推公式

```text
premium_realtime_t_m = (price_t_m - iopv_est_t_m) / iopv_est_t_m
premium_truth_close_t = (close_price_t - official_nav_t) / official_nav_t
premium_error_t_m = abs(premium_realtime_t_m - premium_truth_close_t)
```

## 时间点对齐规则

1. 盘中实时样本只比较同一交易日 `t` 的分钟数据，不跨日比较。
2. AC-P1 盘后验证以 `official_nav_t` 为真实净值锚点，以 `close_price_t` 为二级市场价格锚点。
3. 若要验证全日每分钟误差，测试应优先使用 14:55–15:00 临近收盘窗口；其它分钟可作为趋势样本，不应把盘中指数波动全部归因于 NAV 误差。
4. 若某分钟 `source_quality = stale` 或缺少 `iopv`，该分钟不进入 AC-P1 有效样本。
5. 交易日、时区统一使用 `Asia/Shanghai`。

## 误差判定方法

- 指数型 LOF：`abs(premium_realtime_t_m - premium_truth_close_t) <= 0.005` 视为通过。
- 行业/主动型 LOF：一期只作为辅助观察，最终 AC-P1 随机样本限定 PRD 指定的指数型代码。
- 统计时同时输出样本数、跳过样本数与跳过原因，避免把缺失数据误判为算法误差。

## 后端实现边界

- 拉取器只写 `iopv` 与 `premium`，不新增 PRD §6 字段。
- 每日 18:00 校准任务负责写入 `official_nav`、`close_price`、`premium_close` 与 `premium_pctile_30d`。
- 如测试需要额外诊断字段，应通过测试 fixture 或日志生成，不进入 PRD §6 接口契约。
