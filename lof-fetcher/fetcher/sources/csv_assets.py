from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from fetcher.engine.coverage import normalize_fund_type


@dataclass(frozen=True)
class LofMeta:
    code: str
    name: str
    type: str
    scale_yi: float
    benchmark_raw: str
    status: str


@dataclass(frozen=True)
class BenchmarkComponent:
    code: str
    name: str
    component_name: str
    index_code: str
    weight: float


def load_watchlist(path: str | Path) -> list[LofMeta]:
    rows: list[LofMeta] = []
    with Path(path).open("r", encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            rows.append(
                LofMeta(
                    code=str(row["code"]).zfill(6),
                    name=row["name"].strip(),
                    type=normalize_fund_type(row["type"]),
                    scale_yi=float(row["scale_yi"]),
                    benchmark_raw=row["benchmark_raw"].strip(),
                    status=row["status"].strip(),
                )
            )
    return rows


def load_benchmark_mapping(path: str | Path) -> dict[str, list[BenchmarkComponent]]:
    mapping: dict[str, list[BenchmarkComponent]] = {}
    with Path(path).open("r", encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            component = BenchmarkComponent(
                code=str(row["code"]).zfill(6),
                name=row["name"].strip(),
                component_name=row["component_name"].strip(),
                index_code=row["index_code"].strip(),
                weight=float(row["weight"]),
            )
            mapping.setdefault(component.code, []).append(component)
    return mapping


def benchmark_weights(components: list[BenchmarkComponent]) -> tuple[float, float]:
    assigned = 0.0
    cash = 0.0
    for component in components:
        if component.index_code.upper() == "CASH":
            cash += component.weight
        elif component.index_code:
            assigned += component.weight
    return round(assigned, 6), round(cash, 6)
