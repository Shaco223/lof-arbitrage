"""AC-S2.test.py — AC-S2 验收脚本骨架。

AC 编号: AC-S2
依赖模块: both（dev-003 + dev-004）
样本范围: 全仓扫描
硬约束: 否

测试方法:
    静态扫描 frontend/ 不出现拉取器地址；ingest token 仅出现于 lof-fetcher/；执行 HBuilderX H5 构建脚本

通过条件:
    静态扫描 0 命中 + 构建产物存在

当前状态: pending（骨架阶段，待对应模块交付后填实）
"""
from __future__ import annotations

import pytest

from _lib import AC

META = AC.S2


@pytest.mark.ac_s
@pytest.mark.pending
def test_ac_s2_skeleton():
    """骨架: 仅校验 AC 元信息绑定，等模块到位后填实。"""
    assert META.code == "AC-S2"
    # TODO 模块就绪后填实——
    #   - 静态扫描 frontend/ 不出现拉取器地址
    #   - ingest token 仅出现于 lof-fetcher/
    #   - 执行 HBuilderX H5 构建脚本
    # 通过条件: 静态扫描 0 命中 + 构建产物存在

