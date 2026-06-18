"""AC-S3：前端 uniapp 工程不改源码可构建微信小程序。

测试方法：在 `frontend/` 执行 `npm run build:mp-weixin`。
通过条件：命令退出码为 0，且 `frontend/dist/build/mp-weixin` 目录存在。
依赖模块：dev-003（前端工程化）。
当前状态：已填实（硬约束）。
"""
from __future__ import annotations

import subprocess
import shutil

import pytest

from _lib import AC

META = AC.S3


def run_npm(frontend_dir, npm, *args, timeout=180):
    return subprocess.run(
        [npm, *args],
        cwd=frontend_dir,
        check=False,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
    )


@pytest.mark.ac_s
@pytest.mark.ac_hard
def test_ac_s3_build_mp_weixin_without_source_changes(project_root):
    """AC-S3 硬约束：微信小程序构建必须成功。"""
    assert META.code == "AC-S3"
    frontend_dir = project_root / "frontend"
    npm = shutil.which("npm.cmd") or shutil.which("npm")
    assert npm, "npm executable is required for AC-S3"

    if not (frontend_dir / "node_modules").is_dir():
        install = run_npm(frontend_dir, npm, "install", timeout=180)
        assert install.returncode == 0, install.stdout[-4000:]

    result = run_npm(frontend_dir, npm, "run", "build:mp-weixin", timeout=120)
    assert result.returncode == 0, result.stdout[-4000:]
    assert (frontend_dir / "dist" / "build" / "mp-weixin").is_dir()
