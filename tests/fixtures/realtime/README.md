# tests/fixtures/realtime — 离线净值反推 / 模拟分钟流

## 文件
- `ac-p1-index-lof-samples.json`：AC-P1 指数 LOF 5 只样本占位（结构已定，数值待 dev-004 数据源就绪后由 dev-005 回填）。

## 数据来源（计划）
- 官方 NAV：天天基金 / 基金公司公告 → 次日 09:00 后落地一份
- 分钟价：东方财富 / 新浪 → 拉取器分钟级缓存 dump
- 落盘流程：tests/_lib 提供 `dump_realtime.py`（待实现）

## 字段对齐
- 与 `lof_realtime` 集合（PRD §5.3）字段一致：code / ts / price / iopv / premium / coverage / source_quality
