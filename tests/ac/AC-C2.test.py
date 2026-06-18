"""AC-C2.test.py — AC-C2 验收脚本骨架。

AC 编号: AC-C2
依赖模块: dev-004（拉取器 sources）
样本范围: 单源 mock
硬约束: 否

测试方法:
    httpx mock 让某数据源前 2 次失败、第 3 次成功；记录用时与重试次数

通过条件:
    3 次重试在 30 秒内完成；3 次仍失败写日志且不污染历史

当前状态: pending（骨架阶段，待对应模块交付后填实）
"""
from __future__ import annotations

import pytest

from _lib import AC

META = AC.C2


@pytest.mark.ac_c
@pytest.mark.pending
def test_ac_c2_skeleton():
    """骨架: 仅校验 AC 元信息绑定，等模块到位后填实。"""
    assert META.code == "AC-C2"
    # TODO 模块就绪后填实——
    #   - httpx mock 让某数据源前 2 次失败、第 3 次成功
    #   - 记录用时与重试次数
    # 通过条件: 3 次重试在 30 秒内完成；3 次仍失败写日志且不污染历史

