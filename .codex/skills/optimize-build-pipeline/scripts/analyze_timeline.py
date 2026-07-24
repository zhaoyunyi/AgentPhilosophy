#!/usr/bin/env python3
"""Validate and summarize a build-stage TSV without double-counting overlap."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path

REQUIRED_COLUMNS = ("stage", "start_epoch", "end_epoch", "lane", "category", "status")


@dataclass(frozen=True)
class Stage:
    stage: str
    start_epoch: int
    end_epoch: int
    lane: str
    category: str
    status: str

    @property
    def duration_seconds(self) -> int:
        return self.end_epoch - self.start_epoch


def parse_timeline(path: Path) -> list[Stage]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError("timeline is missing a header")
        missing = [column for column in REQUIRED_COLUMNS if column not in reader.fieldnames]
        if missing:
            raise ValueError(f"timeline is missing columns: {', '.join(missing)}")

        stages: list[Stage] = []
        seen: set[str] = set()
        for line_number, row in enumerate(reader, start=2):
            values = {column: (row.get(column) or "").strip() for column in REQUIRED_COLUMNS}
            empty = [column for column, value in values.items() if not value]
            if empty:
                raise ValueError(f"line {line_number} has empty fields: {', '.join(empty)}")
            if values["stage"] in seen:
                raise ValueError(f"line {line_number} duplicates stage: {values['stage']}")
            seen.add(values["stage"])
            try:
                start_epoch = int(values["start_epoch"])
                end_epoch = int(values["end_epoch"])
            except ValueError as error:
                raise ValueError(f"line {line_number} has a non-integer epoch") from error
            if end_epoch < start_epoch:
                raise ValueError(f"line {line_number} ends before it starts")
            stages.append(
                Stage(
                    stage=values["stage"],
                    start_epoch=start_epoch,
                    end_epoch=end_epoch,
                    lane=values["lane"],
                    category=values["category"],
                    status=values["status"],
                )
            )
    if not stages:
        raise ValueError("timeline has no stages")
    return sorted(stages, key=lambda item: (item.start_epoch, item.end_epoch, item.stage))


def interval_union_seconds(stages: list[Stage]) -> int:
    intervals = sorted((stage.start_epoch, stage.end_epoch) for stage in stages if stage.end_epoch > stage.start_epoch)
    if not intervals:
        return 0
    total = 0
    current_start, current_end = intervals[0]
    for start, end in intervals[1:]:
        if start > current_end:
            total += current_end - current_start
            current_start, current_end = start, end
        else:
            current_end = max(current_end, end)
    return total + current_end - current_start


def peak_parallelism(stages: list[Stage]) -> int:
    events: list[tuple[int, int]] = []
    for stage in stages:
        if stage.end_epoch == stage.start_epoch:
            continue
        events.extend(((stage.start_epoch, 1), (stage.end_epoch, -1)))
    active = 0
    peak = 0
    for _, delta in sorted(events, key=lambda event: (event[0], event[1])):
        active += delta
        peak = max(peak, active)
    return peak


def summarize(stages: list[Stage]) -> dict[str, object]:
    workflow_start = min(stage.start_epoch for stage in stages)
    workflow_end = max(stage.end_epoch for stage in stages)
    wall_seconds = workflow_end - workflow_start
    stage_sum = sum(stage.duration_seconds for stage in stages)
    active_seconds = interval_union_seconds(stages)
    lanes: dict[str, int] = defaultdict(int)
    categories: dict[str, int] = defaultdict(int)
    for stage in stages:
        lanes[stage.lane] += stage.duration_seconds
        categories[stage.category] += stage.duration_seconds
    longest = max(stages, key=lambda stage: (stage.duration_seconds, stage.stage))
    return {
        "workflow_start_epoch": workflow_start,
        "workflow_end_epoch": workflow_end,
        "workflow_wall_seconds": wall_seconds,
        "stage_duration_sum_seconds": stage_sum,
        "active_union_seconds": active_seconds,
        "idle_gap_seconds": wall_seconds - active_seconds,
        "concurrent_stage_seconds": stage_sum - active_seconds,
        "peak_parallelism": peak_parallelism(stages),
        "longest_stage": longest.stage,
        "longest_stage_seconds": longest.duration_seconds,
        "status_counts": dict(sorted(Counter(stage.status for stage in stages).items())),
        "lane_duration_sum_seconds": dict(sorted(lanes.items())),
        "category_duration_sum_seconds": dict(sorted(categories.items())),
        "stages": [{**asdict(stage), "duration_seconds": stage.duration_seconds} for stage in stages],
    }


def escape_markdown(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_markdown(summary: dict[str, object]) -> str:
    lines = [
        "# 构建时间线摘要",
        "",
        f"- 完整墙钟：{summary['workflow_wall_seconds']} 秒",
        f"- 阶段时长合计：{summary['stage_duration_sum_seconds']} 秒",
        f"- 活跃区间并集：{summary['active_union_seconds']} 秒",
        f"- 并发重叠累计：{summary['concurrent_stage_seconds']} 秒",
        f"- 空闲间隙：{summary['idle_gap_seconds']} 秒",
        f"- 峰值并行度：{summary['peak_parallelism']}",
        f"- 最长单阶段：{escape_markdown(summary['longest_stage'])}（{summary['longest_stage_seconds']} 秒）",
        "",
        "| 阶段 | lane | category | start | end | 耗时 | status |",
        "|---|---|---|---:|---:|---:|---|",
    ]
    for stage in summary["stages"]:  # type: ignore[index]
        lines.append(
            "| {stage} | {lane} | {category} | {start_epoch} | {end_epoch} | {duration_seconds} | {status} |".format(
                **{key: escape_markdown(value) for key, value in stage.items()}
            )
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("timeline", type=Path, help="TSV with stage start/end epochs")
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    parser.add_argument("--require-passed", action="store_true", help="exit 1 when any stage status is not passed")
    args = parser.parse_args()

    try:
        stages = parse_timeline(args.timeline)
        summary = summarize(stages)
    except (OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(render_markdown(summary), end="")

    if args.require_passed and any(stage.status != "passed" for stage in stages):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
