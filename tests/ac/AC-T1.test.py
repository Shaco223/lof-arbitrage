"""AC-T1.test.py — AC-T1 验收脚本骨架。

AC 编号: AC-T1
依赖模块: dev-003（详情页）
样本范围: 5 只样本（含指数与主动）
硬约束: 是（任一不达标禁止放行）

测试方法:
    playwright 启动 H5；进入详情页；断言头部覆盖率标签可见 + hover/tap 弹三段明细

通过条件:
    标签数值 + 颜色按 §8 阈值正确；三段总和与 coverage_breakdown 字段一致

当前状态: pending（骨架阶段，待对应模块交付后填实）
"""
from __future__ import annotations

import pytest

from _lib import AC

META = AC.T1


@pytest.mark.ac_t
@pytest.mark.ac_hard
@pytest.mark.pending
def test_ac_t1_skeleton():
    """骨架: 仅校验 AC 元信息绑定，等模块到位后填实。"""
    assert META.code == "AC-T1"
    # TODO 模块就绪后填实——
    #   - playwright 启动 H5
    #   - 进入详情页
    #   - 断言头部覆盖率标签可见 + hover/tap 弹三段明细
    # 通过条件: 标签数值 + 颜色按 §8 阈值正确；三段总和与 coverage_breakdown 字段一致

