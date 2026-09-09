from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / (
    "modules/skill-optimize-build-pipeline/optimize-build-pipeline/scripts/compare_test_runs.py"
)
HEADER = "nodeid\tsetup_seconds\tcall_seconds\tteardown_seconds\toutcome\n"


def run(tmp_path: Path, baseline: str, *candidates: str) -> subprocess.CompletedProcess[str]:
    before = tmp_path / "before.tsv"
    before.write_text(HEADER + baseline)
    paths = []
    for index, content in enumerate(candidates):
        path = tmp_path / f"after-{index}.tsv"
        path.write_text(HEADER + content)
        paths.append(str(path))
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(before), *paths, "--require-preserved"],
        capture_output=True,
        text=True,
        check=False,
    )


def test_partition_preserves_tests_and_allows_new_coverage(tmp_path: Path) -> None:
    result = run(
        tmp_path,
        "a\t1\t2\t3\tpassed\nb\t0\t1\t0\tskipped\n",
        "b\t0\t2\t0\tskipped\n",
        "a\t.1\t.2\t.3\tpassed\nc\t0\t1\t0\tpassed\n",
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["preserved"] is True
    assert report["added"] == ["c"]
    assert report["candidate"]["count"] == 3
    assert report["candidate"]["phase_work_seconds"]["call"] == pytest.approx(3.2)
    assert "workflow_wall_seconds" not in report


@pytest.mark.parametrize(
    "candidate,problem",
    [
        ("", "removed"),
        ("a\t0\t0\t0\tskipped\n", "newly_skipped"),
        ("a\t0\t1\t0\tfailed\n", "failed_or_error"),
    ],
)
def test_missing_skipped_or_failed_cases_block_preservation(tmp_path: Path, candidate: str, problem: str) -> None:
    result = run(tmp_path, "a\t0\t1\t0\tpassed\n", candidate)
    assert result.returncode == 1
    assert json.loads(result.stdout)[problem] == ["a"]


@pytest.mark.parametrize("row", ["a\t0\tnan\t0\tpassed\n", "a\t0\t-1\t0\tpassed\n", "a\t0\t1\t0\tunknown\n"])
def test_invalid_metrics_are_rejected(tmp_path: Path, row: str) -> None:
    assert run(tmp_path, "a\t0\t1\t0\tpassed\n", row).returncode == 2


def test_duplicate_partitions_are_not_silently_summed(tmp_path: Path) -> None:
    row = "a\t0\t1\t0\tpassed\n"
    result = run(tmp_path, row, row, row)
    assert result.returncode == 2
    assert "duplicate" in result.stderr
