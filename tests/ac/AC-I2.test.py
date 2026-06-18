"""AC-I2.test.py — AC-I2 验收脚本骨架。

AC 编号: AC-I2
依赖模块: dev-004（云函数）
样本范围: 5 只样本
硬约束: 否

测试方法:
    对 api-lof-detail?code=xxx 取 5 只样本，断言返回 6 块字段全在

通过条件:
    6 块齐：coverage_top10 / coverage_breakdown / benchmark_components / holdings_top10 / realtime / pctile_30d

当前状态: pending（骨架阶段，待对应模块交付后填实）
"""
from __future__ import annotations

import pytest

from _lib import AC

META = AC.I2


@pytest.mark.ac_i
@pytest.mark.pending
def test_ac_i2_skeleton():
    """骨架: 仅校验 AC 元信息绑定，等模块到位后填实。"""
    assert META.code == "AC-I2"
    # TODO 模块就绪后填实——
    #   - 对 api-lof-detail?code=xxx 取 5 只样本，断言返回 6 块字段全在
    # 通过条件: 6 块齐：coverage_top10 / coverage_breakdown / benchmark_components / holdings_top10 / realtime / pctile_30d

