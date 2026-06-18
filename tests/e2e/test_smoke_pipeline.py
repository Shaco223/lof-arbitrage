"""tests/e2e/test_smoke_pipeline.py — 端到端冒烟骨架。

链路: lof-fetcher 模拟运行一次 → ingest-realtime → uniCloud DB → api-lof-list 读取
通过条件:
  1) ingest-realtime 返回 accepted == 30
  2) api-lof-list 取到 30 行，coverage 与 ingest 提交值在容忍范围内一致
  3) 无字段缺失，无类型错误
依赖: dev-004 拉取器 + 云函数；dev-003 不参与本骨架
当前状态: pending（骨架阶段，等 ingest / list 真实可用后填实）
"""
from __future__ import annotations

import pytest


@pytest.mark.pending
def test_e2e_smoke_skeleton():
    """端到端冒烟骨架，仅占位。"""
    # TODO: 模块就绪后实现——
    #   - 启动拉取器一次性任务，将 30 只 LOF 当前快照通过 ingest-realtime 写入
    #   - 调 api-lof-list?sort=premium_desc 取 30 行
    #   - 比对 ingest 提交快照与 api 返回快照在 coverage / premium 上的偏差
    assert True
