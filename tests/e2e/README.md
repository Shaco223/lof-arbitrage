# tests/e2e — 端到端冒烟

## 当前
- `test_smoke_pipeline.py`：拉取器 → ingest → uniCloud → api-lof-list 全链路骨架（pending）

## 后续
- 接入 playwright，覆盖 AC-T1 的 H5 渲染验收
- 与 AC-S1 配额日志对接：每日跑一次冒烟，输出云函数调用次数样本
