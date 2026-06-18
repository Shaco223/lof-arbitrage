from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from fetcher.sources.csv_assets import load_benchmark_mapping, load_watchlist
from fetcher.sources.eastmoney import EastmoneyFundMetadataClient, validate_watchlist_rows
from fetcher.sources.secondary_validation import (
    EastmoneySecondaryValidationClient,
    SecondaryValidationResult,
    classify_watchlist_row,
)


def render_report(
    results: list[dict[str, str]],
    source: str,
    secondary_results: list[SecondaryValidationResult] | None = None,
    benchmark_conflicts: list[dict[str, str]] | None = None,
) -> str:
    now = datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(timespec="seconds")
    suspicious = [row for row in results if row["risk"] != "ok"]
    pending = [row for row in results if row["status"] == "pending_verify"]
    secondary_results = secondary_results or []
    benchmark_conflicts = benchmark_conflicts or []
    recommendation_counts = _count_by_recommendation(secondary_results)
    lines = [
        "# watchlist-v1 元数据验证报告",
        "",
        f"- 生成时间：{now}",
        f"- 一阶段数据源：{source}",
        "- 二次验证数据源：东方财富场内行情 / 东方财富 20 日 K 线 / 天天基金估值净值 / 东方财富 pingzhongdata 辅助名称",
        f"- 验证范围：{len(results)} 只 LOF",
        f"- 一阶段需回推关注：{len(suspicious)} 只",
        f"- PRD pending_verify：{', '.join(row['code'] for row in pending) or '无'}",
        f"- 二次建议统计：{_format_recommendation_counts(recommendation_counts)}",
        "",
        "## 结论摘要",
        "",
    ]
    if suspicious:
        lines.append("以下条目需 dev-001/dev-002 复核；本报告不直接修改 `assets/lof-watchlist-v1.csv`。")
    else:
        lines.append("未发现需回推条目。")
    lines.extend(
        [
            "",
            "## 需回推条目",
            "",
            "| code | 清单名称 | 官方名称 | type | scale_yi | status | 风险 | 说明 |",
            "| --- | --- | --- | --- | ---: | --- | --- | --- |",
        ]
    )
    for row in suspicious:
        lines.append(
            f"| {row['code']} | {row['watchlist_name']} | {row['official_name']} | {row['type']} | {row['scale_yi']} | {row['status']} | {row['risk']} | {row['reason']} |"
        )
    if secondary_results:
        lines.extend(_render_secondary_section(secondary_results))
    if benchmark_conflicts:
        lines.extend(_render_benchmark_conflicts(benchmark_conflicts))
    lines.extend(
        [
            "",
            "## 全量验证明细",
            "",
            "| code | 清单名称 | 官方名称 | type | status | 风险 |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in results:
        lines.append(
            f"| {row['code']} | {row['watchlist_name']} | {row['official_name']} | {row['type']} | {row['status']} | {row['risk']} |"
        )
    lines.extend(
        [
            "",
            "## 元数据来源与局限",
            "",
            "- 一阶段报告使用东方财富 `pingzhongdata/{code}.js` 校验基金名称，但该接口返回的多为场外基金份额名称，不能直接代表场内 LOF 代码名称。",
            "- 二次验证以场内行情代码是否存在、是否有成交、是否可取净值为主，pingzhongdata 只作为辅助名称证据。",
            "- 该报告不能单独证明基金是否已转型、合并或清盘；`manual_review` 条目仍需 dev-001/dev-002 做人工复核或公告确认。",
            "- 本轮只输出验证报告，不修改 PRD 或 watchlist CSV。",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate LOF watchlist metadata")
    parser.add_argument("--watchlist", default="../assets/lof-watchlist-v1.csv")
    parser.add_argument("--benchmark", default="../assets/benchmark-mapping-v1.csv")
    parser.add_argument("--output", default="../assets/watchlist-v1-validation.md")
    args = parser.parse_args()

    rows = load_watchlist(args.watchlist)
    client = EastmoneyFundMetadataClient()
    try:
        results = validate_watchlist_rows(rows, client)
    finally:
        client.close()

    secondary_client = EastmoneySecondaryValidationClient()
    try:
        secondary_results = []
        ping_by_code = {row["code"]: row.get("official_name", "") for row in results}
        for row in rows:
            secondary_results.append(
                classify_watchlist_row(
                    row=row,
                    venue=secondary_client.fetch_venue_quote(row.code),
                    nav=secondary_client.fetch_nav(row.code),
                    activity=secondary_client.fetch_activity(row.code),
                    ping_name=ping_by_code.get(row.code, ""),
                )
            )
    finally:
        secondary_client.close()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    benchmark_conflicts = detect_benchmark_conflicts(args.benchmark)
    output_path.write_text(
        render_report(results, "东方财富 pingzhongdata", secondary_results, benchmark_conflicts),
        encoding="utf-8",
    )
    print(f"wrote {output_path} ({len(results)} rows)")


def _render_secondary_section(results: list[SecondaryValidationResult]) -> list[str]:
    lines = [
        "",
        "## 二次验证结果",
        "",
        "### 处理建议汇总",
        "",
        "| 建议 | code | 说明 |",
        "| --- | --- | --- |",
    ]
    for recommendation in ["keep", "rename", "type_fix", "replace", "phase2_qdii", "manual_review"]:
        rows = [row for row in results if row.recommendation == recommendation]
        lines.append(f"| {recommendation} | {', '.join(row.code for row in rows) or '无'} | {_recommendation_text(recommendation)} |")
    lines.extend(
        [
            "",
            "### 二次验证明细",
            "",
            "| code | 清单名称 | 场内名称 | 净值名称 | 交易状态 | 类型 | LOF | QDII | 可取净值 | 可取场内行情 | 最新规模(亿) | 20日均成交额 | 活跃度 | 多源名称比对 | 建议 | 证据 |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: | --- | --- | --- | --- |",
        ]
    )
    for row in results:
        lines.append(
            "| "
            + " | ".join(
                [
                    row.code,
                    row.watchlist_name,
                    row.venue_name or "-",
                    row.nav_name or "-",
                    row.trading_status,
                    row.fund_type_verified,
                    _yes_no(row.is_lof),
                    _yes_no(row.is_qdii),
                    _yes_no(row.has_nav),
                    _yes_no(row.has_venue_quote),
                    _format_number(row.latest_scale_yi),
                    _format_number(row.avg_amount_20d),
                    row.activity_status,
                    row.name_compare,
                    row.recommendation,
                    row.evidence.replace("|", "/"),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "### 重点核查结论",
            "",
            "- `501050`：场内行情名称为 `50AHLOF`，净值源名称为 `华夏上证50AH优选指数A`；原 watchlist 名称 `华夏中证500ETF联接(LOF)` 疑似资产清单误填，应进入 `rename/manual_review`，不是 pingzhongdata 单点错映射。",
            "- `160516`：场内行情显示 `证券指数基金` 且 20 日 K 线为空，净值源为 `博时证券公司ETF联接A`；原 `诺安油气能源(LOF)` 疑似代码已不匹配，一期建议 `replace` 或人工确认。",
            "- `160218`：场内行情为 `房地产LOF`，净值源为 `国泰国证房地产行业指数A`；原 `国泰国证医药卫生行业指数(LOF)` 疑似代码对应资产错误，且 20 日成交不活跃，建议 `replace/manual_review`。",
            "- `161024`：有场内行情与净值，分级名称已转为 `军工LOF` / `富国中证军工指数(LOF)A`，建议 `rename` 后可保留观察。",
            "- `161121 / 160628`：有场内行情与净值，但 20 日成交不活跃；如一期坚持成交额阈值，建议 `replace`，否则需人工降级保留。",
            "- `399987`：benchmark 自动检测发现同数字不同后缀/名称冲突，详见 `benchmark mapping 冲突核查`；建议 dev-002/dev-001 复核，可能触发 benchmark CCR。",
            "",
        ]
    )
    return lines


def _render_benchmark_conflicts(conflicts: list[dict[str, str]]) -> list[str]:
    lines = [
        "",
        "## benchmark mapping 冲突核查",
        "",
        "| 数字代码 | 涉及 index_code | 组件名称 | 涉及 LOF | 结论 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for conflict in conflicts:
        lines.append(
            f"| {conflict['numeric_code']} | {conflict['index_codes']} | {conflict['component_names']} | {conflict['lof_codes']} | {conflict['conclusion']} |"
        )
    return lines


def detect_benchmark_conflicts(path: str) -> list[dict[str, str]]:
    mapping = load_benchmark_mapping(path)
    by_numeric: dict[str, list[tuple[str, str, str]]] = {}
    for code, components in mapping.items():
        for component in components:
            if component.index_code.upper() == "CASH":
                continue
            numeric = component.index_code.split(".", 1)[0]
            by_numeric.setdefault(numeric, []).append((component.index_code, component.component_name, code))
    conflicts = []
    for numeric, rows in sorted(by_numeric.items()):
        index_codes = sorted({row[0] for row in rows})
        component_names = sorted({row[1] for row in rows})
        if len(index_codes) > 1 or len(component_names) > 1:
            conflicts.append(
                {
                    "numeric_code": numeric,
                    "index_codes": ", ".join(index_codes),
                    "component_names": ", ".join(component_names),
                    "lof_codes": ", ".join(sorted({row[2] for row in rows})),
                    "conclusion": "同一数字代码映射到多个后缀或组件名称，需人工确认行情源代码",
                }
            )
    return conflicts


def _yes_no(value: bool) -> str:
    return "Y" if value else "N"


def _format_number(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.2f}"


def _count_by_recommendation(results: list[SecondaryValidationResult]) -> dict[str, int]:
    counts = {key: 0 for key in ["keep", "rename", "type_fix", "replace", "phase2_qdii", "manual_review"]}
    for row in results:
        counts[row.recommendation] = counts.get(row.recommendation, 0) + 1
    return counts


def _format_recommendation_counts(counts: dict[str, int]) -> str:
    return ", ".join(f"{key}={value}" for key, value in counts.items())


def _recommendation_text(recommendation: str) -> str:
    return {
        "keep": "可保留原条目",
        "rename": "建议按场内/净值多源名称更新名称或状态",
        "type_fix": "建议修正 type",
        "replace": "不适合一期，建议替换",
        "phase2_qdii": "QDII 或跨境品种，建议二期处理",
        "manual_review": "需人工公告/交易规则复核",
    }[recommendation]


if __name__ == "__main__":
    main()
