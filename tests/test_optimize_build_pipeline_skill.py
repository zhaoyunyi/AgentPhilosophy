from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from agentphilosophy.yamlio import read_yaml

ROOT = Path(__file__).resolve().parents[1]
MODULE_NAME = "skill-optimize-build-pipeline"
SKILL_NAME = "optimize-build-pipeline"
MODULE_ROOT = ROOT / "modules" / MODULE_NAME
SKILL_ROOT = MODULE_ROOT / SKILL_NAME


def test_optimize_build_pipeline_skill_passes_skill_creator_validation() -> None:
    validator = Path.home() / ".codex" / "skills" / ".system" / "skill-creator" / "scripts" / "quick_validate.py"
    result = subprocess.run(
        [sys.executable, str(validator), str(SKILL_ROOT)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr + result.stdout

    skill_text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert "TODO" not in skill_text
    assert "measurement-contract.md" in skill_text
    assert "optimization-playbook.md" in skill_text
    assert "product_image_refs_mutated=false" in skill_text
    assert "不要把预测值写成实测值" in skill_text

    openai = read_yaml(SKILL_ROOT / "agents" / "openai.yaml")
    assert openai["interface"]["display_name"] == "构建流水线调优"
    assert "$optimize-build-pipeline" in openai["interface"]["default_prompt"]


def test_optimize_build_pipeline_module_is_available_in_all_default_presets() -> None:
    module = read_yaml(MODULE_ROOT / "module.yaml")
    assert module["name"] == MODULE_NAME
    assert module["version"] == "1.0.0"
    assert module["provides"] == ["skill:optimize-build-pipeline"]
    assert len(module["outputs"]) == 2

    catalog = read_yaml(ROOT / "catalog.yaml")
    catalog_names = {item["name"] for item in catalog["modules"]}
    assert MODULE_NAME in catalog_names

    root_config = read_yaml(ROOT / ".agentphilosophy.yaml")
    assert MODULE_NAME in root_config["modules"]
    for preset_name in ("orchestrator", "fullstack", "frontend", "mobile-sdk"):
        preset = read_yaml(ROOT / "presets" / f"{preset_name}.yaml")
        assert MODULE_NAME in preset["modules"]


def test_timeline_analyzer_reports_wall_overlap_and_failure_gate(tmp_path: Path) -> None:
    timeline = tmp_path / "timeline.tsv"
    timeline.write_text(
        "stage\tstart_epoch\tend_epoch\tlane\tcategory\tstatus\n"
        "setup\t0\t10\tformal\tsetup\tpassed\n"
        "ci-wait\t10\t30\tcontroller\ttest\tpassed\n"
        "registry\t12\t22\tcontroller\tregistry\tpassed\n"
        "receipt\t30\t35\tcontroller\treceipt\tpassed\n",
        encoding="utf-8",
    )
    script = SKILL_ROOT / "scripts" / "analyze_timeline.py"
    result = subprocess.run(
        [sys.executable, str(script), str(timeline), "--format", "json", "--require-passed"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    summary = json.loads(result.stdout)
    assert summary["workflow_wall_seconds"] == 35
    assert summary["stage_duration_sum_seconds"] == 45
    assert summary["active_union_seconds"] == 35
    assert summary["concurrent_stage_seconds"] == 10
    assert summary["idle_gap_seconds"] == 0
    assert summary["peak_parallelism"] == 2
    assert summary["longest_stage"] == "ci-wait"

    failed_timeline = tmp_path / "failed.tsv"
    failed_timeline.write_text(
        timeline.read_text(encoding="utf-8").replace("registry\tpassed", "registry\tfailed"),
        encoding="utf-8",
    )
    failed = subprocess.run(
        [sys.executable, str(script), str(failed_timeline), "--format", "json", "--require-passed"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert failed.returncode == 1
    assert json.loads(failed.stdout)["status_counts"] == {"failed": 1, "passed": 3}


def test_timeline_analyzer_rejects_duplicate_stage(tmp_path: Path) -> None:
    timeline = tmp_path / "invalid.tsv"
    timeline.write_text(
        "stage\tstart_epoch\tend_epoch\tlane\tcategory\tstatus\n"
        "build\t10\t20\ta\tbuild\tpassed\n"
        "build\t20\t30\tb\tbuild\tpassed\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, str(SKILL_ROOT / "scripts" / "analyze_timeline.py"), str(timeline)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 2
    assert "duplicates stage" in result.stderr
