"""tests/_lib/ac_meta.py — AC 元信息常量与小工具。"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ACStatus(str, Enum):
    PENDING = "pending"
    PASS = "pass"
    FAIL = "fail"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class _ACDef:
    code: str
    title: str
    owner: str
    hard: bool = False


class AC:
    P1 = _ACDef("AC-P1", "5 只指数 LOF 实时溢价 vs 反推 ≤ 0.5%", "dev-004")
    P2 = _ACDef("AC-P2", "30 只整体覆盖率均值 ≥ 90%；个体 <70% ≤ 3", "dev-004")
    P3 = _ACDef("AC-P3", "估算误差 ≥1% 标 degraded；连续两分钟超阈升 stale", "dev-004")
    P4 = _ACDef("AC-P4", "premium_nav=(price-nav_official)/nav_official 误差 ≤ 1e-4", "dev-004")
    P5 = _ACDef("AC-P5", "选填字段 null/unknown 时兜底渲染，旧字段照常", "both")
    C1 = _ACDef("AC-C1", "盘中每分钟 30 行；缺失 ≤ 3 次/日", "dev-004")
    C2 = _ACDef("AC-C2", "单次失败 30 秒内重试 3 次；3 次仍失败写日志并跳过", "dev-004")
    H1 = _ACDef("AC-H1", "详情页 30 天溢价折线无断点（节假日除外）", "both")
    H2 = _ACDef("AC-H2", "premium_pctile_30d ∈ [0,1] 且与离线脚本误差 ≤ 0.01", "dev-004")
    A1 = _ACDef("AC-A1", "溢价 > 5% 持续 1 分钟，2 分钟内告警", "dev-004")
    A2 = _ACDef("AC-A2", "30 分钟冷却；alert_log 含 cooldown_blocked", "dev-004")
    A3 = _ACDef("AC-A3", "非交易时段告警被忽略", "dev-004")
    I1 = _ACDef("AC-I1", "api-lof-list p95 ≤ 800ms 且结构合规", "dev-004")
    I2 = _ACDef("AC-I2", "api-lof-detail 6 块齐全", "dev-004")
    I3 = _ACDef("AC-I3", "api-lof-history days=30 返回 ≥ 20 个交易日", "dev-004")
    I4 = _ACDef("AC-I4", "ingest-realtime 401/400/正常路径码值", "dev-004")
    S1 = _ACDef("AC-S1", "uniCloud 配额连续 3 个交易日达标", "dev-004", hard=True)
    S2 = _ACDef("AC-S2", "写入仅走 ingest；前端不直连拉取器；HBuilderX 一键 H5", "both")
    S3 = _ACDef("AC-S3", "uniapp 工程不改源码可 build:mp-weixin", "dev-003", hard=True)
    T1 = _ACDef("AC-T1", "详情页头部固定显示三段式覆盖率", "dev-003", hard=True)


__all__ = ["AC", "ACStatus", "_ACDef"]
