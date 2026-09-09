#!/usr/bin/env python3
"""只读比较测试清单与阶段工作量；不把累计测试时间当完整流水线墙钟。"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import Counter
from pathlib import Path

PHASES = ("setup", "call", "teardown")
COLUMNS = ("nodeid", *(f"{phase}_seconds" for phase in PHASES), "outcome")
OUTCOMES = {"passed", "failed", "error", "skipped"}


def load_runs(paths: list[Path]) -> dict[str, dict]:
    records = {}
    for path in paths:
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            if reader.fieldnames is None or not set(COLUMNS).issubset(reader.fieldnames):
                raise ValueError(f"{path}: missing required columns")
            for line, row in enumerate(reader, 2):
                nodeid = (row.get("nodeid") or "").strip()
                outcome = (row.get("outcome") or "").strip()
                if not nodeid or outcome not in OUTCOMES:
                    raise ValueError(f"{path}:{line}: invalid nodeid/outcome")
                if nodeid in records:
                    raise ValueError(f"{path}:{line}: duplicate nodeid {nodeid}")
                durations = {}
                for phase in PHASES:
                    value = float(row.get(f"{phase}_seconds") or "nan")
                    if not math.isfinite(value) or value < 0:
                        raise ValueError(f"{path}:{line}: invalid {phase} duration")
                    durations[phase] = value
                records[nodeid] = {"outcome": outcome, "durations": durations}
    return records


def summarize(records: dict[str, dict]) -> dict:
    return {
        "count": len(records),
        "outcomes": dict(sorted(Counter(row["outcome"] for row in records.values()).items())),
        "phase_work_seconds": {
            phase: round(sum(row["durations"][phase] for row in records.values()), 6) for phase in PHASES
        },
    }


def compare(baseline: dict[str, dict], candidate: dict[str, dict]) -> dict:
    removed = sorted(baseline.keys() - candidate.keys())
    newly_skipped = sorted(
        name
        for name, row in candidate.items()
        if row["outcome"] == "skipped" and baseline.get(name, {}).get("outcome") != "skipped"
    )
    failed = sorted(name for name, row in candidate.items() if row["outcome"] in {"failed", "error"})
    return {
        "baseline": summarize(baseline),
        "candidate": summarize(candidate),
        "added": sorted(candidate.keys() - baseline.keys()),
        "removed": removed,
        "newly_skipped": newly_skipped,
        "failed_or_error": failed,
        "preserved": bool(baseline and candidate) and not (removed or newly_skipped or failed),
        "scope": "test inventory and outcomes only; not assertion, coverage or release verification",
        "timing_semantics": "sum of phase work; concurrent work and nested fixtures are not wall time",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path, nargs="+")
    parser.add_argument(
        "--require-preserved", action="store_true", help="候选丢用例、新增skip或含失败时退出1；允许增加通过用例"
    )
    args = parser.parse_args()
    try:
        report = compare(load_runs([args.baseline]), load_runs(args.candidate))
    except (OSError, ValueError, csv.Error) as error:
        print(f"test comparison: {error}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if args.require_preserved and not report["preserved"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
