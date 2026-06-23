# IOPV data-source probe (POC, read-only; does NOT touch the real_watchlist main chain).
#
# Intraday-only meaningful (09:30-11:30 / 13:00-15:00). For a handful of
# representative LOFs it queries several free candidate sources in parallel and
# records, per source: whether a real exchange IOPV is available, the value +
# its timestamp lag vs now, field stability, and any rate-limit signal.
#
# Sources probed:
#   - fundgz (current baseline): gsz / gztime (estimated NAV, NOT exchange IOPV)
#   - eastmoney push2 (secid): f43 price + f92 net-asset field (IOPV candidate)
#   - eastmoney fundmobapi: GSZ/GZTIME estimated NAV
#   - tencent quote: scan for any NAV/IOPV-like field
#   - jisilu lof list: estimate_value / fund_nav / discount_rt (may need member)
#
# Output: outputs/backend-iopv-source-probe-v2.json (+ .md report).
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

DEFAULT_CODES = ["161725", "161005", "160706", "160632", "501203"]
UA = {"User-Agent": "Mozilla/5.0"}


def _now() -> datetime:
    return datetime.now().astimezone()


def _client() -> httpx.Client:
    return httpx.Client(timeout=6.0, headers=UA, follow_redirects=True, trust_env=False)


def _to_float(value: Any) -> float | None:
    try:
        if value in (None, "", "-", " "):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _secid(code: str) -> str:
    market = "1" if code.startswith(("50", "51", "52")) else "0"
    return f"{market}.{code}"


def _symbol(code: str) -> str:
    return f"sh{code}" if code.startswith(("50", "51", "52")) else f"sz{code}"


def probe_fundgz(client: httpx.Client, code: str) -> dict[str, Any]:
    start = time.perf_counter()
    try:
        r = client.get(f"https://fundgz.1234567.com.cn/js/{code}.js?rt={int(time.time()*1000)}")
        elapsed = int((time.perf_counter() - start) * 1000)
        r.raise_for_status()
        m = re.search(r"jsonpgz\((.*)\);?", r.text.strip())
        if not m:
            return {"source": "fundgz", "ok": False, "elapsed_ms": elapsed, "error": "no_payload"}
        d = json.loads(m.group(1))
        return {
            "source": "fundgz",
            "ok": True,
            "elapsed_ms": elapsed,
            "is_real_iopv": False,
            "iopv": _to_float(d.get("gsz")),
            "value_kind": "estimated_nav(gsz)",
            "value_time": d.get("gztime") or "",
            "nav_official": _to_float(d.get("dwjz")),
            "nav_date": d.get("jzrq") or "",
        }
    except Exception as exc:  # noqa: BLE001
        return {"source": "fundgz", "ok": False,
                "elapsed_ms": int((time.perf_counter() - start) * 1000),
                "error": type(exc).__name__}


def probe_eastmoney_push2(client: httpx.Client, code: str) -> dict[str, Any]:
    start = time.perf_counter()
    try:
        r = client.get(
            f"https://push2.eastmoney.com/api/qt/stock/get?secid={_secid(code)}"
            f"&fields=f43,f57,f58,f60,f92,f250,f251"
        )
        elapsed = int((time.perf_counter() - start) * 1000)
        r.raise_for_status()
        data = (r.json() or {}).get("data") or {}
        price = _to_float(data.get("f43"))
        net_asset = _to_float(data.get("f92"))
        return {
            "source": "eastmoney_push2",
            "ok": price is not None,
            "elapsed_ms": elapsed,
            "is_real_iopv": False,
            "price": round(price / 1000, 4) if price is not None else None,
            "f92_net_asset_per_share": net_asset,
            "value_kind": "f92_net_asset(usually 0 for LOF)",
        }
    except Exception as exc:  # noqa: BLE001
        return {"source": "eastmoney_push2", "ok": False,
                "elapsed_ms": int((time.perf_counter() - start) * 1000),
                "error": type(exc).__name__}


def probe_eastmoney_fundmob(client: httpx.Client, code: str) -> dict[str, Any]:
    start = time.perf_counter()
    try:
        r = client.get(
            "https://fundmobapi.eastmoney.com/FundMNewApi/FundMNFInfo"
            f"?pageIndex=1&pageSize=20&plat=Android&appType=ttjj&product=EFund&Version=1&deviceid=1&Fcodes={code}"
        )
        elapsed = int((time.perf_counter() - start) * 1000)
        r.raise_for_status()
        datas = (r.json() or {}).get("Datas") or []
        d = datas[0] if datas else {}
        gsz = _to_float(d.get("GSZ"))
        return {
            "source": "eastmoney_fundmob",
            "ok": gsz is not None,
            "elapsed_ms": elapsed,
            "is_real_iopv": False,
            "iopv": gsz,
            "value_kind": "estimated_nav(GSZ)",
            "value_time": d.get("GZTIME") or "",
            "nav_official": _to_float(d.get("NAV")),
            "nav_date": d.get("PDATE") or "",
        }
    except Exception as exc:  # noqa: BLE001
        return {"source": "eastmoney_fundmob", "ok": False,
                "elapsed_ms": int((time.perf_counter() - start) * 1000),
                "error": type(exc).__name__}


def probe_tencent(client: httpx.Client, code: str) -> dict[str, Any]:
    start = time.perf_counter()
    try:
        r = client.get(f"https://qt.gtimg.cn/q={_symbol(code)}")
        elapsed = int((time.perf_counter() - start) * 1000)
        r.raise_for_status()
        if '="' not in r.text:
            return {"source": "tencent_quote", "ok": False, "elapsed_ms": elapsed, "error": "no_payload"}
        fields = r.text.split('="', 1)[1].rsplit('"', 1)[0].split("~")
        price = _to_float(fields[3]) if len(fields) > 3 else None
        # field[81] is the official prior NAV for funds (NOT a live IOPV).
        prior_nav = _to_float(fields[81]) if len(fields) > 81 else None
        return {
            "source": "tencent_quote",
            "ok": price is not None,
            "elapsed_ms": elapsed,
            "is_real_iopv": False,
            "price": price,
            "f81_prior_nav": prior_nav,
            "value_kind": "no live IOPV field (f81=prior official NAV)",
        }
    except Exception as exc:  # noqa: BLE001
        return {"source": "tencent_quote", "ok": False,
                "elapsed_ms": int((time.perf_counter() - start) * 1000),
                "error": type(exc).__name__}


_JISILU_CACHE: dict[str, dict[str, Any]] = {}


def _load_jisilu(client: httpx.Client) -> dict[str, dict[str, Any]]:
    if _JISILU_CACHE:
        return _JISILU_CACHE
    headers = {**UA, "Referer": "https://www.jisilu.cn/data/lof/"}
    for kind in ("index_lof_list", "stock_lof_list"):
        try:
            url = f"https://www.jisilu.cn/data/lof/{kind}/?___jsl=LST___t={int(time.time()*1000)}"
            r = client.post(url, headers=headers, data={"rp": "50", "page": "1"})
            r.raise_for_status()
            for row in (r.json() or {}).get("rows", []):
                cell = row.get("cell") or {}
                fid = cell.get("fund_id")
                if fid:
                    _JISILU_CACHE[fid] = cell
        except Exception:  # noqa: BLE001
            continue
    return _JISILU_CACHE


def probe_jisilu(client: httpx.Client, code: str) -> dict[str, Any]:
    start = time.perf_counter()
    try:
        cells = _load_jisilu(client)
        elapsed = int((time.perf_counter() - start) * 1000)
        cell = cells.get(code)
        if not cell:
            return {"source": "jisilu", "ok": False, "elapsed_ms": elapsed,
                    "error": "code_not_in_free_list"}
        est = _to_float(cell.get("estimate_value"))
        return {
            "source": "jisilu",
            "ok": True,
            "elapsed_ms": elapsed,
            "is_real_iopv": est is not None,
            "iopv": est,
            "value_kind": "estimate_value(member-gated; '-' when not logged in)",
            "value_time": cell.get("est_val_dt") or cell.get("last_est_time") or "",
            "fund_nav": _to_float(cell.get("fund_nav")),
            "nav_date": cell.get("nav_dt") or "",
            "discount_rt": cell.get("discount_rt"),
            "index_increase_rt": cell.get("index_increase_rt"),
        }
    except Exception as exc:  # noqa: BLE001
        return {"source": "jisilu", "ok": False,
                "elapsed_ms": int((time.perf_counter() - start) * 1000),
                "error": type(exc).__name__}


PROBES = [probe_fundgz, probe_eastmoney_push2, probe_eastmoney_fundmob, probe_tencent, probe_jisilu]


def _lag_seconds(value_time: str, now: datetime) -> int | None:
    if not value_time:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%H:%M:%S", "%H:%M"):
        try:
            parsed = datetime.strptime(value_time, fmt)
            if parsed.year == 1900:
                parsed = parsed.replace(year=now.year, month=now.month, day=now.day)
            parsed = parsed.replace(tzinfo=now.tzinfo)
            return max(0, int((now - parsed).total_seconds()))
        except ValueError:
            continue
    return None


def probe_code(client: httpx.Client, code: str) -> dict[str, Any]:
    now = _now()
    results = []
    with ThreadPoolExecutor(max_workers=len(PROBES)) as pool:
        futures = [pool.submit(fn, client, code) for fn in PROBES]
        for fut in futures:
            res = fut.result()
            lag = _lag_seconds(res.get("value_time", ""), now)
            if lag is not None:
                res["lag_seconds"] = lag
            results.append(res)
    results.sort(key=lambda r: r["source"])
    return {"code": code, "ts": now.isoformat(timespec="seconds"), "sources": results}


def build_probe_report(codes: list[str]) -> dict[str, Any]:
    client = _client()
    try:
        per_code = [probe_code(client, c) for c in codes]
    finally:
        client.close()
    real_iopv_sources = sorted({
        s["source"]
        for c in per_code for s in c["sources"]
        if s.get("is_real_iopv")
    })
    return {
        "ts": _now().isoformat(timespec="seconds"),
        "codes": codes,
        "real_iopv_sources": real_iopv_sources,
        "note": "is_real_iopv=True means a live exchange-grade IOPV was actually returned this run.",
        "per_code": per_code,
    }


def write_report(report: dict[str, Any], output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "backend-iopv-source-probe-v2.json"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path = output_dir / "backend-iopv-source-probe-v2.md"
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return {"json": json_path, "md": md_path}


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# IOPV 数据源探测报告 (POC)",
        "",
        f"- 探测时间: {report['ts']}",
        f"- 标的: {', '.join(report['codes'])}",
        f"- 本轮返回真 IOPV 的源: {report['real_iopv_sources'] or '无'}",
        "",
        "## 标的 x 数据源对比",
        "",
        "| code | source | ok | 真IOPV | 值 | 值类型 | 值时间 | 滞后(s) | 耗时(ms) | error |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for c in report["per_code"]:
        for s in c["sources"]:
            val = s.get("iopv", s.get("price", ""))
            lines.append(
                f"| {c['code']} | {s['source']} | {s.get('ok')} | {s.get('is_real_iopv', False)} | "
                f"{val} | {s.get('value_kind','')} | {s.get('value_time','')} | "
                f"{s.get('lag_seconds','')} | {s.get('elapsed_ms','')} | {s.get('error','')} |"
            )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="IOPV data-source probe (POC, read-only)")
    parser.add_argument("--codes", nargs="*", default=DEFAULT_CODES)
    parser.add_argument("--output-dir", type=Path, default=Path("../outputs"))
    parser.add_argument("--repeat", type=int, default=1, help="probe N times (interval --interval-seconds)")
    parser.add_argument("--interval-seconds", type=float, default=60.0)
    args = parser.parse_args(argv)

    last = None
    for i in range(max(1, args.repeat)):
        report = build_probe_report(args.codes)
        files = write_report(report, args.output_dir)
        print(f"[{report['ts']}] probe #{i+1} real_iopv_sources={report['real_iopv_sources']} "
              f"-> {files['json']}")
        last = report
        if i + 1 < args.repeat:
            time.sleep(max(0.0, args.interval_seconds))
    return last


if __name__ == "__main__":
    main()
