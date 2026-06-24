# LOF daily-shares-series + on-exchange settlement-rule probe (POC, read-only).
#
# Mirrors probe_iopv_sources.py / probe_subscribe_status.py: read-only, never
# touches section-6 fields, never touches the real_watchlist main chain, never
# writes to any data path, never hits the online uniCloud, never submits a token.
#
# Two probe points:
#   1) Daily shares series -> can we build a "new shares = today - yesterday"
#      column? Probe free sources for a per-trading-day share/scale series.
#        - eastmoney_f10_gmbd: FundArchivesDatas.aspx?type=gmbd (share-change
#          table). REALITY: only QUARTERLY report-date rows (qtr subscribe /
#          qtr redeem / end total shares), NOT a daily series.
#        - eastmoney_fundmob_ivinfo: FundMNIVInfoMultiple report-date list ->
#          confirms shares are disclosed only at quarter-end report dates.
#        - jisilu_lof: LOF list; member-gated (empty rows when not logged in).
#   2) On-exchange purchase T+N sellable rule (static settlement rule) -> can we
#      structurally read "purchased on-exchange shares are sellable after T+N
#      trading days"?
#        - eastmoney_f10_jjfl: jjfl_{code}.html trade-rule table exposes
#          buy/sell CONFIRM day (T+1), which is the OPEN-END subscription
#          confirm day (fund-contract wording), NOT the on-exchange purchased-
#          share sellable day. Coverage is also incomplete (some codes empty).
#
# Output: outputs/backend-shares-settlement-probe-v2.json (+ .md report).
from __future__ import annotations

import argparse
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

# >=7 codes spanning index / active / sector + active_low_liquidity.
DEFAULT_CODES = [
    "161725",  # index (white-liquor), high liquidity
    "161005",  # active (Fuguo Tianhui)
    "160632",  # sector index
    "501203",  # active_low_liquidity
    "501050",  # index (CSI medical / China-Merchants), mid liquidity
    "160706",  # index (Jiashi 300)
    "160216",  # active_low_liquidity (QDII-ish / commodity)
]
UA = {"User-Agent": "Mozilla/5.0"}
F10_REFERER = {"Referer": "https://fundf10.eastmoney.com/"}
FUNDMOB_QS = "plat=Android&appType=ttjj&product=EFund&Version=1&deviceid=1"


def _now() -> datetime:
    return datetime.now().astimezone()


def _client() -> httpx.Client:
    return httpx.Client(timeout=8.0, headers=UA, follow_redirects=True, trust_env=False)


def _has(value: Any) -> bool:
    return value not in (None, "", "-", "--", " ")

# ----------------------------------------------------------------------------
# Probe point 1: daily shares series
# ----------------------------------------------------------------------------

# East-money F10 gmbd ("规模变动") share-change table. Returns a JS blob
# 'var gmbd_apidata={ content:"<table>...</table>" ...}'. Columns:
#   日期 | 期间申购(亿份) | 期间赎回(亿份) | 期末总份额(亿份) | 期末净资产(亿元) | ...
# The dates are QUARTER-END report dates only (e.g. 2026-03-31), so there is NO
# daily share series here.
_GMBD_ROW = re.compile(
    r"<tr><td>(\d{4}-\d{2}-\d{2})</td>"
    r"<td[^>]*>([^<]*)</td><td[^>]*>([^<]*)</td>"
    r"<td[^>]*>([^<]*)</td><td[^>]*>([^<]*)</td>"
)


def probe_eastmoney_f10_gmbd(client: httpx.Client, code: str) -> dict[str, Any]:
    start = time.perf_counter()
    try:
        r = client.get(
            "https://fundf10.eastmoney.com/FundArchivesDatas.aspx"
            f"?type=gmbd&mode=cycle&code={code}",
            headers=F10_REFERER,
        )
        elapsed = int((time.perf_counter() - start) * 1000)
        r.encoding = "utf-8"
        rows = _GMBD_ROW.findall(r.text) if r.status_code == 200 else []
        dates = [row[0] for row in rows]
        # A daily series would have consecutive trading days; report dates jump
        # by ~3 months. Detect granularity from the first two date gaps.
        granularity = "none"
        if len(dates) >= 2:
            try:
                d0 = datetime.fromisoformat(dates[0])
                d1 = datetime.fromisoformat(dates[1])
                gap_days = abs((d0 - d1).days)
                granularity = "daily" if gap_days <= 5 else "quarterly_report"
            except ValueError:
                granularity = "unknown"
        sample = []
        for row in rows[:3]:
            sample.append({
                "date": row[0],
                "qtr_subscribe_yi": row[1],
                "qtr_redeem_yi": row[2],
                "end_total_shares_yi": row[3],
                "end_nav_assets_yi": row[4],
            })
        return {
            "source": "eastmoney_f10_gmbd",
            "ok": bool(rows),
            "elapsed_ms": elapsed,
            "needs_login": False,
            "http_status": r.status_code,
            "has_share_series": bool(rows),
            "series_granularity": granularity,
            "rows_returned": len(rows),
            "latest_date": dates[0] if dates else None,
            "sample": sample,
            "note": "share-change table; report-date rows only (qtr), end_total_shares is quarter-end",
        }
    except Exception as exc:  # noqa: BLE001
        return {"source": "eastmoney_f10_gmbd", "ok": False,
                "elapsed_ms": int((time.perf_counter() - start) * 1000),
                "error": type(exc).__name__}


def probe_eastmoney_fundmob_ivinfo(client: httpx.Client, code: str) -> dict[str, Any]:
    # FundMNIVInfoMultiple returns the list of report dates that carry holdings/
    # share disclosures -> a cross-check that shares disclose at quarter-end only.
    start = time.perf_counter()
    try:
        r = client.get(
            "https://fundmobapi.eastmoney.com/FundMNewApi/FundMNIVInfoMultiple"
            f"?FCODE={code}&{FUNDMOB_QS}"
        )
        elapsed = int((time.perf_counter() - start) * 1000)
        r.raise_for_status()
        dates = (r.json() or {}).get("Datas") or []
        if not isinstance(dates, list):
            dates = []
        granularity = "none"
        if len(dates) >= 2:
            try:
                gap = abs((datetime.fromisoformat(dates[0]) - datetime.fromisoformat(dates[1])).days)
                granularity = "daily" if gap <= 5 else "quarterly_report"
            except ValueError:
                granularity = "unknown"
        return {
            "source": "eastmoney_fundmob_ivinfo",
            "ok": bool(dates),
            "elapsed_ms": elapsed,
            "needs_login": False,
            "has_share_series": False,
            "series_granularity": granularity,
            "report_dates_returned": len(dates),
            "latest_date": dates[0] if dates else None,
            "note": "report-date list (holdings/shares disclosure cadence); confirms quarter-end disclosure",
        }
    except Exception as exc:  # noqa: BLE001
        return {"source": "eastmoney_fundmob_ivinfo", "ok": False,
                "elapsed_ms": int((time.perf_counter() - start) * 1000),
                "error": type(exc).__name__}


def probe_jisilu_shares(client: httpx.Client, code: str) -> dict[str, Any]:
    # jisilu LOF list MAY carry an "amount"/"fund_size" column but the per-day
    # series is member-gated; empty rows == not logged in.
    start = time.perf_counter()
    try:
        r = client.get(
            "https://www.jisilu.cn/data/lof/stock_lof_list/?___jsl=LST___t="
            f"{int(time.time()*1000)}&rp=50&page=1"
        )
        elapsed = int((time.perf_counter() - start) * 1000)
        r.raise_for_status()
        rows = (r.json() or {}).get("rows") or []
        cell = {}
        for row in rows:
            if str(row.get("id")) == code:
                cell = row.get("cell") or {}
                break
        amount = cell.get("amount") or cell.get("fund_size")
        return {
            "source": "jisilu_lof",
            "ok": _has(amount),
            "elapsed_ms": elapsed,
            "needs_login": not bool(rows),
            "has_share_series": False,
            "series_granularity": "snapshot_only" if _has(amount) else "none",
            "rows_returned": len(rows),
            "amount_field": amount,
            "note": "LOF list is member-gated; at best a single current snapshot, no daily series",
        }
    except Exception as exc:  # noqa: BLE001
        return {"source": "jisilu_lof", "ok": False,
                "elapsed_ms": int((time.perf_counter() - start) * 1000),
                "needs_login": True,
                "error": type(exc).__name__}

# ----------------------------------------------------------------------------
# Probe point 2: on-exchange purchase T+N sellable (settlement) rule
# ----------------------------------------------------------------------------

# jjfl_{code}.html trade-rule table exposes "买入确认日" / "卖出确认日"
# (buy/sell confirm day, usually T+1). IMPORTANT: this is the OPEN-END
# subscribe/redeem CONFIRM day from the fund contract, NOT the on-exchange
# purchased-share sellable day (an exchange-registration rule, e.g. subscribed
# shares listed/sellable on T+2). The two concepts differ.
_CONFIRM_ROW = re.compile(r"([\u4e00-\u9fa5]{2,8}\u786e\u8ba4\u65e5)</td><td[^>]*>([^<]+)</td>")
_TPLUSN = re.compile(r"T\s*\+\s*(\d+)")
_BUY_KEY = "买入确认日"
_SELL_KEY = "卖出确认日"


def _parse_tplusn(value: Any) -> int | None:
    if not _has(value):
        return None
    m = _TPLUSN.search(str(value))
    return int(m.group(1)) if m else None


def probe_eastmoney_f10_jjfl(client: httpx.Client, code: str) -> dict[str, Any]:
    start = time.perf_counter()
    try:
        r = client.get(f"https://fundf10.eastmoney.com/jjfl_{code}.html", headers=F10_REFERER)
        elapsed = int((time.perf_counter() - start) * 1000)
        r.encoding = "utf-8"
        text = r.text if r.status_code == 200 else ""
        pairs = dict(_CONFIRM_ROW.findall(text))
        buy_confirm = pairs.get(_BUY_KEY)
        sell_confirm = pairs.get(_SELL_KEY)
        has_onexch_sellable = any(kw in text for kw in ("上市可卖", "可卖出交易"))
        return {
            "source": "eastmoney_f10_jjfl",
            "ok": _has(buy_confirm) or _has(sell_confirm),
            "elapsed_ms": elapsed,
            "needs_login": False,
            "http_status": r.status_code,
            "has_confirm_day_field": _has(buy_confirm) or _has(sell_confirm),
            "buy_confirm_day_raw": buy_confirm,
            "sell_confirm_day_raw": sell_confirm,
            "buy_confirm_tplusn": _parse_tplusn(buy_confirm),
            "sell_confirm_tplusn": _parse_tplusn(sell_confirm),
            "has_onexchange_sellable_field": has_onexch_sellable,
            "settlement_days_structured": None,
            "note": "buy/sell CONFIRM day = open-end contract wording (T+1), NOT on-exchange purchased-share sellable day",
        }
    except Exception as exc:  # noqa: BLE001
        return {"source": "eastmoney_f10_jjfl", "ok": False,
                "elapsed_ms": int((time.perf_counter() - start) * 1000),
                "error": type(exc).__name__}

# ----------------------------------------------------------------------------
# Orchestration + report
# ----------------------------------------------------------------------------

SHARES_PROBES = [
    probe_eastmoney_f10_gmbd,
    probe_eastmoney_fundmob_ivinfo,
    probe_jisilu_shares,
]
SETTLEMENT_PROBES = [
    probe_eastmoney_f10_jjfl,
]


def probe_code(client: httpx.Client, code: str) -> dict[str, Any]:
    now = _now()
    shares: list[dict[str, Any]] = []
    settlement: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=len(SHARES_PROBES) + len(SETTLEMENT_PROBES)) as pool:
        sh_futs = [pool.submit(fn, client, code) for fn in SHARES_PROBES]
        st_futs = [pool.submit(fn, client, code) for fn in SETTLEMENT_PROBES]
        for fut in sh_futs:
            shares.append(fut.result())
        for fut in st_futs:
            settlement.append(fut.result())
    shares.sort(key=lambda r: r["source"])
    settlement.sort(key=lambda r: r["source"])
    return {"code": code, "ts": now.isoformat(timespec="seconds"),
            "shares_series": shares, "settlement_rule": settlement}


def build_probe_report(codes: list[str]) -> dict[str, Any]:
    client = _client()
    try:
        per_code = [probe_code(client, c) for c in codes]
    finally:
        client.close()

    # Point 1 coverage: any source with a true daily series?
    shares_cov: dict[str, dict[str, Any]] = {}
    daily_series_found = False
    for c in per_code:
        for s in c["shares_series"]:
            src = s["source"]
            st = shares_cov.setdefault(src, {"ok": 0, "total": 0, "granularities": {}})
            st["total"] += 1
            if s.get("ok"):
                st["ok"] += 1
            g = s.get("series_granularity", "none")
            st["granularities"][g] = st["granularities"].get(g, 0) + 1
            if s.get("has_share_series") and s.get("series_granularity") == "daily":
                daily_series_found = True

    # Point 2 coverage: confirm-day field coverage + any structured settlement.
    settle_cov: dict[str, dict[str, Any]] = {}
    structured_settlement_found = False
    confirm_values: set[str] = set()
    for c in per_code:
        for s in c["settlement_rule"]:
            src = s["source"]
            st = settle_cov.setdefault(src, {"confirm_field": 0, "onexch_sellable": 0, "total": 0})
            st["total"] += 1
            if s.get("has_confirm_day_field"):
                st["confirm_field"] += 1
            if s.get("has_onexchange_sellable_field"):
                st["onexch_sellable"] += 1
            if s.get("settlement_days_structured") is not None:
                structured_settlement_found = True
            for k in ("buy_confirm_day_raw", "sell_confirm_day_raw"):
                if _has(s.get(k)):
                    confirm_values.add(str(s[k]))

    return {
        "ts": _now().isoformat(timespec="seconds"),
        "codes": codes,
        "point1_daily_shares": {
            "coverage": shares_cov,
            "daily_series_found": daily_series_found,
            "conclusion": (
                "stable_free_daily_series_available" if daily_series_found
                else "no_free_daily_share_series; only quarter-end report disclosure"
            ),
            "proposed_fields_if_available": ["circulating_shares_daily", "shares_change_daily"],
        },
        "point2_settlement_rule": {
            "coverage": settle_cov,
            "structured_settlement_found": structured_settlement_found,
            "confirm_day_raw_values": sorted(confirm_values),
            "conclusion": (
                "structured_onexchange_settlement_available" if structured_settlement_found
                else "no_structured_onexchange_T+N_sellable; only open-end buy/sell CONFIRM day (T+1) which is a DIFFERENT concept"
            ),
            "proposed_field_if_available": "purchase_settlement_days",
        },
        "per_code": per_code,
    }

def write_report(report, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "backend-shares-settlement-probe-v2.json"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path = output_dir / "backend-shares-settlement-probe-v2.md"
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return {"json": json_path, "md": md_path}


def render_markdown(report):
    p1 = report["point1_daily_shares"]
    p2 = report["point2_settlement_rule"]
    codes_str = ", ".join(report["codes"])
    lines = []
    lines.append("# \u4efd\u989d\u5e8f\u5217 + \u573a\u5185\u7533\u8d2d\u5230\u8d26\u89c4\u5219\u63a2\u6d4b\u62a5\u544a (POC)")
    lines.append("")
    lines.append("- \u63a2\u6d4b\u65f6\u95f4: " + str(report["ts"]))
    lines.append("- \u6807\u7684: " + codes_str)
    lines.append("- \u7eaf\u53ea\u8bfb\u63a2\u6d4b\uff0c\u4e0d\u63a5\u5165\u4e3b\u94fe\u8def\uff0c\u4e0d\u52a8 \u00a76 \u5b57\u6bb5\uff0c\u4e0d\u6253\u7ebf\u4e0a\uff0c\u4e0d\u63d0\u4ea4 token")
    lines.append("")
    lines.append("## \u63a2\u6d4b\u70b9\u4e00\uff1a\u9010\u65e5\u4efd\u989d\u5e8f\u5217")
    lines.append("")
    lines.append("- \u7ed3\u8bba: **" + str(p1["conclusion"]) + "**")
    lines.append("- \u662f\u5426\u627e\u5230\u7a33\u5b9a\u514d\u8d39\u9010\u65e5\u4efd\u989d\u5e8f\u5217: " + str(p1["daily_series_found"]))
    lines.append("")
    lines.append("| source | ok/total | \u7c92\u5ea6\u5206\u5e03 |")
    lines.append("|---|---|---|")
    for src, st in p1["coverage"].items():
        g = ", ".join(str(k) + "=" + str(v) for k, v in st["granularities"].items())
        lines.append("| " + src + " | " + str(st["ok"]) + "/" + str(st["total"]) + " | " + g + " |")
    lines.append("")
    lines.append("### \u6807\u7684 x \u6e90 (\u4efd\u989d\u5e8f\u5217) \u660e\u7ec6")
    lines.append("")
    lines.append("| code | source | ok | \u6709\u9010\u65e5\u5e8f\u5217 | \u7c92\u5ea6 | \u884c\u6570 | \u6700\u65b0\u65e5\u671f | \u9700\u767b\u5f55 | \u8017\u65f6(ms) |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for c in report["per_code"]:
        for s in c["shares_series"]:
            rows = s.get("rows_returned", s.get("report_dates_returned", ""))
            lines.append(
                "| " + c["code"] + " | " + s["source"] + " | " + str(s.get("ok")) + " | "
                + str(s.get("has_share_series", "")) + " | " + str(s.get("series_granularity", "")) + " | "
                + str(rows) + " | " + str(s.get("latest_date", "")) + " | "
                + str(s.get("needs_login", "")) + " | " + str(s.get("elapsed_ms", "")) + " |"
            )
    lines.append("")
    lines.append("## \u63a2\u6d4b\u70b9\u4e8c\uff1a\u573a\u5185\u7533\u8d2d\u4efd\u989d T+N \u53ef\u5356\u89c4\u5219")
    lines.append("")
    lines.append("- \u7ed3\u8bba: **" + str(p2["conclusion"]) + "**")
    lines.append("- \u662f\u5426\u6709\u7ed3\u6784\u5316\u573a\u5185\u5230\u8d26\u5b57\u6bb5: " + str(p2["structured_settlement_found"]))
    lines.append("- \u539f\u59cb\u786e\u8ba4\u65e5\u6587\u6848(\u573a\u5916\u53e3\u5f84): " + str(p2["confirm_day_raw_values"]))
    lines.append("")
    lines.append("| code | source | \u6709\u786e\u8ba4\u65e5\u5b57\u6bb5 | \u4e70\u5165\u786e\u8ba4 | \u5356\u51fa\u786e\u8ba4 | \u573a\u5185\u53ef\u5356\u7ed3\u6784\u5316 | \u8017\u65f6(ms) |")
    lines.append("|---|---|---|---|---|---|---|")
    for c in report["per_code"]:
        for s in c["settlement_rule"]:
            lines.append(
                "| " + c["code"] + " | " + s["source"] + " | "
                + str(s.get("has_confirm_day_field", "")) + " | " + str(s.get("buy_confirm_day_raw", "")) + " | "
                + str(s.get("sell_confirm_day_raw", "")) + " | " + str(s.get("settlement_days_structured")) + " | "
                + str(s.get("elapsed_ms", "")) + " |"
            )
    lines.append("")
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description="LOF daily-shares-series + on-exchange settlement-rule probe (POC, read-only)")
    parser.add_argument("--codes", nargs="*", default=DEFAULT_CODES)
    parser.add_argument("--output-dir", type=Path, default=Path("../outputs"))
    args = parser.parse_args(argv)
    report = build_probe_report(args.codes)
    files = write_report(report, args.output_dir)
    print("[" + report["ts"] + "] shares.daily_found=" + str(report["point1_daily_shares"]["daily_series_found"])
          + " settlement.structured=" + str(report["point2_settlement_rule"]["structured_settlement_found"])
          + " -> " + str(files["json"]))
    return report


if __name__ == "__main__":
    main()
