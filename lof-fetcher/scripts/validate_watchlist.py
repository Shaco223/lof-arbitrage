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
    secondary_results = secondary_results or []
    benchmark_conflicts = benchmark_conflicts or []
    recommendation_counts = _count_by_recommendation(secondary_results)

    lines = [
        "# watchlist-v2 元数据验证报告",
        "",
        f"- 生成时间：{now}",
        f"- 一阶段数据源：{source}",
        "- 二次验证数据源：东方财富场内行情 / 东方财富 20 日 K 线 / 天天基金估值净值 / pingzhongdata 辅助名称",
        f"- 验证范围：{len(results)} 只 LOF",
        f"- 一阶段需关注：{len(suspicious)} 只",
        f"- 二次建议统计：{_format_recommendation_counts(recommendation_counts)}",
        "",
        "## 结论摘要",
        "",
    ]
    if suspicious:
        lines.append("以下条目需 dev-001/dev-002 复核；本报告不直接修改 watchlist CSV。")
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
    if not suspicious:
        lines.append("| - | - | - | - | - | - | - | - |")

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
            "## 数据源局限",
            "",
            "- pingzhongdata 名称不能单独作为场内 LOF 替换依据。",
            "- manual_review 条目仍需 dev-001/dev-002 结合公告或交易规则复核。",
            "- 本脚本只输出验证报告，不修改 PRD 或 watchlist CSV。",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate LOF watchlist metadata")
    parser.add_argument("--watchlist", default="../assets/lof-watchlist-v2.csv")
    parser.add_argument("--benchmark", default="../assets/benchmark-mapping-v2.csv")
    parser.add_argument("--output", default="../outputs/watchlist-v2-validation-dryrun.md")
    args = parser.parse_args()

    rows = load_watchlist(args.watchlist)
    client = EastmoneyFundMetadataClient()
    try:
        results = validate_watchlist_rows(rows, client)
    finally:
        client.close()

    secondary_client = EastmoneySecondaryValidationClient()
    try:
        secondary_results = [
            classify_watchlist_row(
                row,
                secondary_client.fetch_venue_quote(row.code),
                secondary_client.fetch_nav(row.code),
                secondary_client.fetch_activity(row.code),
                secondary_client.fetch_pingzhong_name(row.code),
            )
            for row in rows
        ]
    finally:
        secondary_client.close()

    conflicts = detect_benchmark_conflicts(args.benchmark)
    report = render_report(results, "eastmoney pingzhongdata", secondary_results, conflicts)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")


def _render_secondary_section(rows: list[SecondaryValidationResult]) -> list[str]:
    lines = [
        "",
        "## 二次验证结果",
        "",
        "| code | 名称 | 交易 | 类型 | LOF | QDII | 净值 | 行情 | 20日成交额(万元) | 多源名称比对 | 建议 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | ---: | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {code} | {name} | {trading} | {fund_type} | {is_lof} | {is_qdii} | {has_nav} | {has_quote} | {amount} | {name_cmp} | {recommendation} |".format(
                code=row.code,
                name=row.watchlist_name,
                trading=_yes_no(row.trading),
                fund_type=row.fund_type,
                is_lof=_yes_no(row.is_lof),
                is_qdii=_yes_no(row.is_qdii),
                has_nav=_yes_no(row.has_nav),
                has_quote=_yes_no(row.has_venue_quote),
                amount=_format_number(row.avg_amount_20d_wan),
                name_cmp=row.name_compare,
                recommendation=row.recommendation,
            )
        )
    lines.extend(
        [
            "",
            "### 处理建议说明",
            "",
            "| 建议 | 含义 |",
            "| --- | --- |",
        ]
    )
    for recommendation in ["keep", "rename", "type_fix", "replace", "phase2_qdii", "manual_review"]:
        lines.append(f"| {recommendation} | {_recommendation_text(recommendation)} |")
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
                    "conclusion": "同一数字代码映射到多个后缀或组件名称，需人工确认行情源代码。",
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
        "keep": "保留原条目",
        "rename": "按场内/净值多源名称更新名称或状态",
        "type_fix": "修正 type",
        "replace": "不适合一期，建议替换",
        "phase2_qdii": "QDII 或跨境品种，建议二期处理",
        "manual_review": "需人工公告或交易规则复核",
    }[recommendation]


if __name__ == "__main__":
    main()
