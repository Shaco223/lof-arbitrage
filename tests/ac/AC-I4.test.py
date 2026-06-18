"""AC-I4.test.py — AC-I4 验收脚本骨架。

AC 编号: AC-I4
依赖模块: dev-004（云函数 ingest）
样本范围: 3 路径
硬约束: 否

测试方法:
    对 ingest-realtime 三条用例：错 token / 缺字段 / 正常体

通过条件:
    返回 code 分别为 4010 / 4001 / 0；正常时 accepted == 提交条数

当前状态: pending（骨架阶段，待对应模块交付后填实）
"""
from __future__ import annotations

import pytest

from _lib import AC

META = AC.I4


@pytest.mark.ac_i
@pytest.mark.pending
def test_ac_i4_skeleton():
    """骨架: 仅校验 AC 元信息绑定，等模块到位后填实。"""
    assert META.code == "AC-I4"
    # TODO 模块就绪后填实——
    #   - 对 ingest-realtime 三条用例：错 token / 缺字段 / 正常体
    # 通过条件: 返回 code 分别为 4010 / 4001 / 0；正常时 accepted == 提交条数

