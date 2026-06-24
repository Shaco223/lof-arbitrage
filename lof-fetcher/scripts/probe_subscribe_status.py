# Subscribe/redeem status data-source probe (POC, read-only).
#
# Does NOT touch section-6 fields, the real_watchlist main chain, or any write
# path. It only queries free candidate sources for the subscribe/redeem status
# of representative LOFs and records, per source x per code: whether a structured
# status field exists, the raw returned value, whether login/membership is
# required, request latency, and any rate-limit / anti-scrape signal.
#
# Sources probed:
#   - eastmoney_fundmob_basic (FundMNBasicInformation): SGZT / SHZT / BUY /
#     ISSALES / MINSG / MAXSG  -> structured subscribe/redeem status (candidate
#     primary source).
#   - eastmoney_f10_html (fundf10 jbgk overview HTML): old 2026-06-19 baseline,
#     checked for contrast (no structured status field expected).
#   - jisilu_lof (jisilu LOF list): apply/redeem status-like fields, usually
#     member-gated (empty rows when not logged in).
#   - eastmoney_push2 (secid quote): scanned for any status-like field.
#
# Output: outputs/backend-subscribe-status-probe-v2.json (+ .md report).
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

# >=5 codes spanning index / active / sector + >=1 active_low_liquidity.
DEFAULT_CODES = ["161725", "161005", "160706", "160632", "501050", "501203", "501090"]
UA = {"User-Agent": "Mozilla/5.0"}
FUNDMOB_QS = "plat=Android&appType=ttjj&product=EFund&Version=1&deviceid=1"


def _now() -> datetime:
    return datetime.now().astimezone()


def _client() -> httpx.Client:
    return httpx.Client(timeout=8.0, headers=UA, follow_redirects=True, trust_env=False)


def _has(value: Any) -> bool:
    return value not in (None, "", "-", "--", " ")


def probe_eastmoney_fundmob_basic(client: httpx.Client, code: str) -> dict[str, Any]:
    start = time.perf_counter()
    try:
        r = client.get(
            "https://fundmobapi.eastmoney.com/FundMNewApi/FundMNBasicInformation"
            f"?FCODE={code}&{FUNDMOB_QS}"
        )
        elapsed = int((time.perf_counter() - start) * 1000)
        r.raise_for_status()
        d = (r.json() or {}).get("Datas") or {}
        if isinstance(d, list):
            d = d[0] if d else {}
        sgzt = d.get("SGZT")
        shzt = d.get("SHZT")
        mark = d.get("SGZTMARK")
        trademark_list = d.get("TRADEMARKLIST") or []
        max_sg = d.get("MAXSG")
        limit = parse_subscribe_limit(mark, trademark_list, max_sg)
        return {
            "source": "eastmoney_fundmob_basic",
            "ok": _has(sgzt) or _has(shzt),
            "elapsed_ms": elapsed,
            "needs_login": False,
            "has_subscribe_field": _has(sgzt),
            "has_redeem_field": _has(shzt),
            "subscribe_status_raw": sgzt,
            "redeem_status_raw": shzt,
            "subscribe_mark": mark,
            "min_subscribe": d.get("MINSG"),
            "max_subscribe": max_sg,
            "has_subscribe_limit_field": limit["has_limit"],
            "subscribe_limit_raw": limit["raw"],
            "subscribe_limit_amount": limit["amount"],
            "subscribe_limit_period": limit["period"],
            "buy_flag": d.get("BUY"),
            "is_sales": d.get("ISSALES"),
            "name": d.get("SHORTNAME"),
        }
    except Exception as exc:  # noqa: BLE001
        return {"source": "eastmoney_fundmob_basic", "ok": False,
                "elapsed_ms": int((time.perf_counter() - start) * 1000),
                "error": type(exc).__name__}


def probe_eastmoney_f10_html(client: httpx.Client, code: str) -> dict[str, Any]:
    start = time.perf_counter()
    try:
        r = client.get(f"https://fundf10.eastmoney.com/jbgk_{code}.html")
        elapsed = int((time.perf_counter() - start) * 1000)
        r.encoding = "utf-8"
        text = r.text if r.status_code == 200 else ""
        # jbgk overview HTML DOES carry a real value in a "trade-status" span
        # (e.g. "?????<span>???</span>" + a following "<span>????</span>").
        # The literal labels subscribe/redeem-status also appear as nav-menu anchor
        # text, so we parse the actual span value instead of just keyword presence.
        sub_raw = None
        red_raw = None
        m = re.search(r"\u4ea4\u6613\u72b6\u6001\uff1a\s*<span>([^<]+)</span>", text)
        if m:
            sub_raw = m.group(1).strip()
        for kw in ("\u5f00\u653e\u8d4e\u56de", "\u6682\u505c\u8d4e\u56de"):
            if kw in text:
                red_raw = kw
                break
        return {
            "source": "eastmoney_f10_html",
            "ok": _has(sub_raw) or _has(red_raw),
            "elapsed_ms": elapsed,
            "needs_login": False,
            "http_status": r.status_code,
            "has_subscribe_field": _has(sub_raw),
            "has_redeem_field": _has(red_raw),
            "subscribe_status_raw": sub_raw,
            "redeem_status_raw": red_raw,
            "note": "overview HTML baseline; status parsed from trade-status span (less structured, HTML-fragile)",
        }
    except Exception as exc:  # noqa: BLE001
        return {"source": "eastmoney_f10_html", "ok": False,
                "elapsed_ms": int((time.perf_counter() - start) * 1000),
                "error": type(exc).__name__}


def probe_eastmoney_push2(client: httpx.Client, code: str) -> dict[str, Any]:
    start = time.perf_counter()
    market = "1" if code.startswith(("50", "51", "52")) else "0"
    try:
        r = client.get(
            f"https://push2.eastmoney.com/api/qt/stock/get?secid={market}.{code}"
            "&fields=f43,f57,f58,f292,f111,f139"
        )
        elapsed = int((time.perf_counter() - start) * 1000)
        r.raise_for_status()
        data = (r.json() or {}).get("data") or {}
        return {
            "source": "eastmoney_push2",
            "ok": False,
            "elapsed_ms": elapsed,
            "needs_login": False,
            "has_subscribe_field": False,
            "has_redeem_field": False,
            "note": "quote endpoint carries no subscribe/redeem status field",
            "sample_keys": sorted(list(data.keys()))[:8],
        }
    except Exception as exc:  # noqa: BLE001
        return {"source": "eastmoney_push2", "ok": False,
                "elapsed_ms": int((time.perf_counter() - start) * 1000),
                "error": type(exc).__name__}


def probe_jisilu(client: httpx.Client, code: str) -> dict[str, Any]:
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
            if str(row.get("id")) == code or str((row.get("cell") or {}).get("fund_id")) == code:
                cell = row.get("cell") or {}
                break
        apply_status = cell.get("apply_status") or cell.get("fund_status")
        redeem_status = cell.get("redeem_status")
        needs_login = not bool(rows)
        return {
            "source": "jisilu_lof",
            "ok": _has(apply_status) or _has(redeem_status),
            "elapsed_ms": elapsed,
            "needs_login": needs_login,
            "has_subscribe_field": _has(apply_status),
            "has_redeem_field": _has(redeem_status),
            "subscribe_status_raw": apply_status,
            "redeem_status_raw": redeem_status,
            "rows_returned": len(rows),
            "note": "LOF list is member-gated; empty rows == not logged in",
        }
    except Exception as exc:  # noqa: BLE001
        return {"source": "jisilu_lof", "ok": False,
                "elapsed_ms": int((time.perf_counter() - start) * 1000),
                "needs_login": True,
                "error": type(exc).__name__}


PROBES = [
    probe_eastmoney_fundmob_basic,
    probe_eastmoney_f10_html,
    probe_eastmoney_push2,
    probe_jisilu,
]


def probe_code(client: httpx.Client, code: str) -> dict[str, Any]:
    now = _now()
    results = []
    with ThreadPoolExecutor(max_workers=len(PROBES)) as pool:
        futures = [pool.submit(fn, client, code) for fn in PROBES]
        for fut in futures:
            results.append(fut.result())
    results.sort(key=lambda r: r["source"])
    return {"code": code, "ts": now.isoformat(timespec="seconds"), "sources": results}


# Parse the subscribe-limit (purchase cap) into a structured amount+period.
# Free sources express the cap two ways: a structured numeric MAXSG (yuan) and
# a wording mark (SGZTMARK / TRADEMARKLIST). MAXSG can be an effectively-infinite
# sentinel (e.g. 1e11) meaning "no real cap"; we keep raw text and a parsed number.
_LIMIT_NO_CAP = 1_000_000_000.0  # >=1e9 yuan treated as effectively no cap
_UNIT_YI = "\u4ebf"   # 100,000,000
_UNIT_WAN = "\u4e07"  # 10,000
_LIMIT_RE = re.compile(r"([0-9]+(?:\.[0-9]+)?)\s*(\u4ebf|\u4e07)?\u5143?")
_PERIOD_DAY = "\u65e5"      # day (single-day cumulative cap)


def _to_yuan(num: float, unit: str | None) -> float:
    if unit == _UNIT_YI:
        return num * 1e8
    if unit == _UNIT_WAN:
        return num * 1e4
    return num


def parse_subscribe_limit(mark: Any, trademark_list: Any, max_sg: Any) -> dict[str, Any]:
    # Prefer the human wording (has explicit amount + period); fall back to MAXSG.
    texts = []
    if _has(mark):
        texts.append(str(mark))
    if isinstance(trademark_list, list):
        texts.extend(str(x) for x in trademark_list if _has(x))
    raw = texts[0] if texts else None
    amount = None
    period = None
    for t in texts:
        m = _LIMIT_RE.search(t)
        if m:
            amount = _to_yuan(float(m.group(1)), m.group(2))
            period = "day" if _PERIOD_DAY in t else None
            raw = t
            break
    # Numeric MAXSG fallback / cross-check when wording has no number.
    max_sg_num = None
    try:
        if _has(max_sg):
            max_sg_num = float(max_sg)
    except (TypeError, ValueError):
        max_sg_num = None
    if amount is None and max_sg_num is not None:
        if max_sg_num >= _LIMIT_NO_CAP:
            amount = None  # effectively no cap
        else:
            amount = max_sg_num
            period = "day"
    has_limit = bool(_has(raw)) or (max_sg_num is not None and max_sg_num < _LIMIT_NO_CAP)
    return {
        "has_limit": has_limit,
        "raw": raw,
        "amount": amount,
        "period": period,
        "max_sg_num": max_sg_num,
    }


# Proposed clean enum to normalize raw vendor wording into a stable set.
SUBSCRIBE_ENUM_MAP = {
    "\u5f00\u653e\u7533\u8d2d": "open",        # open subscription
    "\u9650\u5927\u989d": "limited",            # large-amount limited
    "\u6682\u505c\u7533\u8d2d": "suspended",    # suspended
    "\u5c01\u95ed\u671f": "closed",             # closed period
    "\u573a\u5185\u4e70\u5165": "open",         # on-exchange buy only
}
REDEEM_ENUM_MAP = {
    "\u5f00\u653e\u8d4e\u56de": "open",         # open redemption
    "\u6682\u505c\u8d4e\u56de": "suspended",    # suspended redemption
    "\u5c01\u95ed\u671f": "closed",             # closed period
}


def map_enum(raw: Any, table: dict[str, str]) -> str:
    if not _has(raw):
        return "unknown"
    text = str(raw)
    for key, val in table.items():
        if key in text:
            return val
    return "other"


def build_probe_report(codes: list[str]) -> dict[str, Any]:
    client = _client()
    try:
        per_code = [probe_code(client, c) for c in codes]
    finally:
        client.close()

    # Coverage per source: how many codes returned a usable status field.
    coverage: dict[str, dict[str, int]] = {}
    raw_subscribe_values: set[str] = set()
    raw_redeem_values: set[str] = set()
    raw_limit_values: set[str] = set()
    for c in per_code:
        for s in c["sources"]:
            src = s["source"]
            stat = coverage.setdefault(src, {"subscribe": 0, "redeem": 0, "limit": 0, "total": 0})
            stat["total"] += 1
            if s.get("has_subscribe_field"):
                stat["subscribe"] += 1
            if s.get("has_redeem_field"):
                stat["redeem"] += 1
            if s.get("has_subscribe_limit_field"):
                stat["limit"] += 1
            if _has(s.get("subscribe_status_raw")):
                raw_subscribe_values.add(str(s["subscribe_status_raw"]))
            if _has(s.get("redeem_status_raw")):
                raw_redeem_values.add(str(s["redeem_status_raw"]))
            if _has(s.get("subscribe_limit_raw")):
                raw_limit_values.add(str(s["subscribe_limit_raw"]))

    return {
        "ts": _now().isoformat(timespec="seconds"),
        "codes": codes,
        "coverage": coverage,
        "raw_subscribe_values": sorted(raw_subscribe_values),
        "raw_redeem_values": sorted(raw_redeem_values),
        "raw_subscribe_limit_values": sorted(raw_limit_values),
        "proposed_subscribe_enum": sorted(set(SUBSCRIBE_ENUM_MAP.values()) | {"unknown", "other"}),
        "proposed_redeem_enum": sorted(set(REDEEM_ENUM_MAP.values()) | {"unknown", "other"}),
        "per_code": per_code,
    }


def write_report(report: dict[str, Any], output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "backend-subscribe-status-probe-v2.json"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path = output_dir / "backend-subscribe-status-probe-v2.md"
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return {"json": json_path, "md": md_path}


_NONE_CN = "\u65e0"  # Chinese for "none"


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# \u7533\u8d2d/\u8d4e\u56de\u72b6\u6001\u6570\u636e\u6e90\u63a2\u6d4b\u62a5\u544a (POC)",
        "",
        f"- \u63a2\u6d4b\u65f6\u95f4: {report['ts']}",
        f"- \u6807\u7684: {', '.join(report['codes'])}",
        "",
        "## \u6e90\u8986\u76d6\u7387 (\u8fd4\u56de\u7ed3\u6784\u5316\u72b6\u6001\u5b57\u6bb5\u7684\u6807\u7684\u6570/\u603b\u6570)",
        "",
        "| source | subscribe | redeem | limit | total |",
        "|---|---|---|---|---|",
    ]
    for src, stat in report["coverage"].items():
        lines.append(f"| {src} | {stat['subscribe']} | {stat['redeem']} | {stat.get('limit', 0)} | {stat['total']} |")
    lines += [
        "",
        f"- \u539f\u59cb\u7533\u8d2d\u72b6\u6001\u6587\u6848: {report['raw_subscribe_values'] or _NONE_CN}",
        f"- \u539f\u59cb\u8d4e\u56de\u72b6\u6001\u6587\u6848: {report['raw_redeem_values'] or _NONE_CN}",
        f"- \u539f\u59cb\u7533\u8d2d\u989d\u5ea6\u6587\u6848: {report.get('raw_subscribe_limit_values') or _NONE_CN}",
        f"- \u5efa\u8bae\u7533\u8d2d\u679a\u4e3e: {report['proposed_subscribe_enum']}",
        f"- \u5efa\u8bae\u8d4e\u56de\u679a\u4e3e: {report['proposed_redeem_enum']}",
        "",
        "## \u6807\u7684 x \u6570\u636e\u6e90\u660e\u7ec6",
        "",
        "| code | source | ok | \u7533\u8d2d\u5b57\u6bb5 | \u8d4e\u56de\u5b57\u6bb5 | \u7533\u8d2d\u539f\u503c | \u8d4e\u56de\u539f\u503c | \u9700\u767b\u5f55 | \u8017\u65f6(ms) | error |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for c in report["per_code"]:
        for s in c["sources"]:
            lines.append(
                f"| {c['code']} | {s['source']} | {s.get('ok')} | "
                f"{s.get('has_subscribe_field', '')} | {s.get('has_redeem_field', '')} | "
                f"{s.get('subscribe_status_raw', '')} | {s.get('redeem_status_raw', '')} | "
                f"{s.get('needs_login', '')} | {s.get('elapsed_ms', '')} | {s.get('error', '')} |"
            )
    # Subscribe-limit (purchase cap) detail: keep separate from subscribe-STATUS;
    # a fund can be status=limited yet expose a concrete cap amount.
    lines += [
        "",
        "## \u7533\u8d2d\u989d\u5ea6 (\u8d2d\u4e70\u4e0a\u9650, \u4e0e\u7533\u8d2d\u72b6\u6001\u533a\u5206)",
        "",
        "| code | source | \u72b6\u6001 | \u6709\u989d\u5ea6\u5b57\u6bb5 | \u989d\u5ea6\u6587\u6848 | \u89e3\u6790\u91d1\u989d(\u5143) | \u5468\u671f | MAXSG\u539f\u503c |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for c in report["per_code"]:
        for s in c["sources"]:
            if "has_subscribe_limit_field" not in s and "subscribe_limit_raw" not in s:
                continue
            lines.append(
                f"| {c['code']} | {s['source']} | {s.get('subscribe_status_raw', '')} | "
                f"{s.get('has_subscribe_limit_field', '')} | {s.get('subscribe_limit_raw', '')} | "
                f"{s.get('subscribe_limit_amount', '')} | {s.get('subscribe_limit_period', '')} | "
                f"{s.get('max_subscribe', '')} |"
            )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> dict[str, Any]:
    parser = argparse.ArgumentParser(description="Subscribe/redeem status data-source probe (POC, read-only)")
    parser.add_argument("--codes", nargs="*", default=DEFAULT_CODES)
    parser.add_argument("--output-dir", type=Path, default=Path("../outputs"))
    parser.add_argument("--repeat", type=int, default=1, help="probe N times (interval --interval-seconds)")
    parser.add_argument("--interval-seconds", type=float, default=60.0)
    args = parser.parse_args(argv)

    last = None
    for i in range(max(1, args.repeat)):
        report = build_probe_report(args.codes)
        files = write_report(report, args.output_dir)
        print(f"[{report['ts']}] probe #{i+1} coverage={ {k: v['subscribe'] for k, v in report['coverage'].items()} } "
              f"-> {files['json']}")
        last = report
        if i + 1 < args.repeat:
            time.sleep(max(0.0, args.interval_seconds))
    return last


if __name__ == "__main__":
    main()
