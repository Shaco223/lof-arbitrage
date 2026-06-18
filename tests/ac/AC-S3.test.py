"""AC-S3.test.py — AC-S3 验收脚本骨架。

AC 编号: AC-S3
依赖模块: dev-003（前端工程化）
样本范围: 一次构建
硬约束: 是（任一不达标禁止放行）

测试方法:
    在干净环境中 npm install + npm run build:mp-weixin；不允许修改源码

通过条件:
    构建退出码 0，产物目录存在 unpackage/dist/build/mp-weixin

当前状态: pending（骨架阶段，待对应模块交付后填实）
"""
from __future__ import annotations

import pytest

from _lib import AC

META = AC.S3


@pytest.mark.ac_s
@pytest.mark.ac_hard
@pytest.mark.pending
def test_ac_s3_skeleton():
    """骨架: 仅校验 AC 元信息绑定，等模块到位后填实。"""
    assert META.code == "AC-S3"
    # TODO 模块就绪后填实——
    #   - 在干净环境中 npm install + npm run build:mp-weixin
    #   - 不允许修改源码
    # 通过条件: 构建退出码 0，产物目录存在 unpackage/dist/build/mp-weixin

