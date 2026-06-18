from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from fetcher.sources.csv_assets import load_watchlist
from fetcher.sources.eastmoney import EastmoneyFundMetadataClient, validate_watchlist_rows


def render_report(results: list[dict[str, str]], source: str) -> str:
    now = datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(timespec="seconds")
    suspicious = [row for row in results if row["risk"] != "ok"]
    pending = [row for row in results if row["status"] == "pending_verify"]
    lines = [
        "# watchlist-v1 元数据验证报告",
        "",
        f"- 生成时间：{now}",
        f"- 数据源：{source}",
        f"- 验证范围：{len(results)} 只 LOF",
        f"- 需回推关注：{len(suspicious)} 只",
        f"- PRD pending_verify：{', '.join(row['code'] for row in pending) or '无'}",
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
            "- 使用东方财富 `pingzhongdata/{code}.js` 校验基金代码是否存在、官方名称是否可解析。",
            "- 该接口不能单独证明基金是否已转型、合并或清盘；`pending_verify` 条目仍需 dev-001/dev-002 做人工复核或引入公告/交易状态二次验证。",
            "- 本轮只输出验证报告，不修改 PRD 或 watchlist CSV。",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate LOF watchlist metadata")
    parser.add_argument("--watchlist", default="../assets/lof-watchlist-v1.csv")
    parser.add_argument("--output", default="../assets/watchlist-v1-validation.md")
    args = parser.parse_args()

    rows = load_watchlist(args.watchlist)
    client = EastmoneyFundMetadataClient()
    try:
        results = validate_watchlist_rows(rows, client)
    finally:
        client.close()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_report(results, "东方财富 pingzhongdata"), encoding="utf-8")
    print(f"wrote {output_path} ({len(results)} rows)")


if __name__ == "__main__":
    main()
