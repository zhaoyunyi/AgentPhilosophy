from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from agentphilosophy.yamlio import read_yaml

ROOT = Path(__file__).resolve().parents[1]
MODULE_NAME = "skill-orchestrate-grok-cli"
SKILL_NAME = "orchestrate-grok-cli"
MODULE_ROOT = ROOT / "modules" / MODULE_NAME
SKILL_ROOT = MODULE_ROOT / SKILL_NAME


def test_orchestrate_grok_cli_skill_passes_skill_creator_validation() -> None:
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
    assert "grok agent headless" in skill_text
    assert "WebSocket relay" in skill_text
    assert "独立检查版本控制状态" in skill_text
    assert "Hooks 计数增加" in skill_text
    assert "references/headless-orchestration.md" in skill_text
    assert "scripts/grok-stop-hook.sh" in skill_text

    openai = read_yaml(SKILL_ROOT / "agents" / "openai.yaml")
    assert openai["interface"]["display_name"] == "Grok CLI 编排"
    assert "$orchestrate-grok-cli" in openai["interface"]["default_prompt"]


def test_orchestrate_grok_cli_module_is_available_in_all_default_presets() -> None:
    module = read_yaml(MODULE_ROOT / "module.yaml")
    assert module["name"] == MODULE_NAME
    assert module["version"] == "1.0.0"
    assert module["provides"] == ["skill:orchestrate-grok-cli"]
    assert len(module["outputs"]) == 2

    catalog = read_yaml(ROOT / "catalog.yaml")
    assert MODULE_NAME in {item["name"] for item in catalog["modules"]}

    root_config = read_yaml(ROOT / ".agentphilosophy.yaml")
    assert MODULE_NAME in root_config["modules"]
    for preset_name in ("orchestrator", "fullstack", "frontend", "mobile-sdk"):
        preset = read_yaml(ROOT / "presets" / f"{preset_name}.yaml")
        assert MODULE_NAME in preset["modules"]


def test_stop_hook_helper_installs_records_status_and_removes_owned_files(tmp_path: Path) -> None:
    hooks_dir = tmp_path / ".grok" / "hooks"
    runtime_dir = tmp_path / "runtime"

    script = SKILL_ROOT / "scripts" / "grok-stop-hook.sh"
    base_command = [
        "bash",
        str(script),
        "--hooks-dir",
        str(hooks_dir),
        "--runtime-dir",
        str(runtime_dir),
        "--name",
        "member-61",
    ]
    install = subprocess.run(
        [base_command[0], base_command[1], "install", *base_command[2:]],
        text=True,
        capture_output=True,
        check=False,
    )
    assert install.returncode == 0, install.stderr + install.stdout

    config = hooks_dir / "member-61.json"
    handler = runtime_dir / "member-61-stop-handler.sh"
    event_log = runtime_dir / "member-61-events.jsonl"
    assert config.is_file()
    assert handler.is_file()
    assert os.access(handler, os.X_OK)
    hook_config = json.loads(config.read_text(encoding="utf-8"))
    assert hook_config["hooks"]["Stop"][0]["hooks"][0]["type"] == "command"

    event = subprocess.run(
        [str(handler), str(event_log)],
        input=json.dumps(
            {
                "hookEventName": "stop",
                "sessionId": "session-123",
                "cwd": "/tmp/workspace",
                "reason": "completed",
                "timestamp": "2026-07-28T00:00:00Z",
                "prompt": "must-not-be-logged",
            }
        ),
        text=True,
        capture_output=True,
        check=False,
    )
    assert event.returncode == 0, event.stderr + event.stdout
    recorded = json.loads(event_log.read_text(encoding="utf-8"))
    assert recorded == {
        "hook_event_name": "stop",
        "session_id": "session-123",
        "cwd": "/tmp/workspace",
        "reason": "completed",
        "timestamp": "2026-07-28T00:00:00Z",
    }

    status = subprocess.run(
        [base_command[0], base_command[1], "status", *base_command[2:]],
        text=True,
        capture_output=True,
        check=False,
    )
    assert status.returncode == 0, status.stderr + status.stdout
    assert json.loads(status.stdout)["event_count"] == 1

    sentinel = runtime_dir / "keep.txt"
    sentinel.write_text("keep", encoding="utf-8")
    remove = subprocess.run(
        [base_command[0], base_command[1], "remove", *base_command[2:]],
        text=True,
        capture_output=True,
        check=False,
    )
    assert remove.returncode == 0, remove.stderr + remove.stdout
    assert not config.exists()
    assert not handler.exists()
    assert event_log.is_file()
    assert sentinel.read_text(encoding="utf-8") == "keep"
