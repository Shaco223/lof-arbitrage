"""
tests/_lib/real_api.py - local real API reader (127.0.0.1:8787).

Reads lof-list / lof-detail / lof-history only; defaults to local real API.
Online next.bspapp.com requires ALLOW_ONLINE_REAL_API=1. Returns None when
unavailable so callers can skip.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_LOCAL_API_BASE = "http://127.0.0.1:8787"
REAL_API_BASE = os.getenv("REAL_API_BASE", DEFAULT_LOCAL_API_BASE).rstrip("/")
FN_LIST = os.getenv("REAL_API_FN_LIST", "lof-list")
FN_DETAIL = os.getenv("REAL_API_FN_DETAIL", "lof-detail")
FN_HISTORY = os.getenv("REAL_API_FN_HISTORY", "lof-history")


def _online_blocked() -> bool:
    return "next.bspapp.com" in REAL_API_BASE and os.getenv("ALLOW_ONLINE_REAL_API") != "1"


def _get(path: str, params: dict | None = None):
    if _online_blocked():
        return None
    query = ("?" + urllib.parse.urlencode(params)) if params else ""
    url = f"{REAL_API_BASE}/{path}{query}"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except (OSError, urllib.error.URLError, TimeoutError, ValueError):
        return None


def fetch_list_items(sort: str = "code"):
    payload = _get(FN_LIST, {"sort": sort})
    if payload is None:
        return None
    return payload.get("data", {}).get("items")


def fetch_detail(code: str):
    payload = _get(FN_DETAIL, {"code": code})
    if payload is None:
        return None
    return payload.get("data")


def fetch_history(code: str, days: int = 30):
    payload = _get(FN_HISTORY, {"code": code, "days": days})
    if payload is None:
        return None
    return payload.get("data", {}).get("items")
