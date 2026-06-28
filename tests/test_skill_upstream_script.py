from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path
from types import ModuleType

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check-skill-upstreams.py"
LOCKED_REVISION = "0123456789abcdef0123456789abcdef01234567"
LATEST_REVISION = "fedcba9876543210fedcba9876543210fedcba98"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_source(source: Path, upstream: str = "") -> None:
    write(
        source / "modules" / "skill-demo" / "module.yaml",
        f"""
name: skill-demo
description: Demo skill
version: 1.0.0
project_types: [fullstack]
requires: []
conflicts: []
{upstream}outputs: []
""".strip()
        + "\n",
    )


def write_upstream_source(source: Path, ref: str = "main", revision: str = LOCKED_REVISION) -> None:
    write_source(
        source,
        f"""
upstream:
  repository: https://github.com/example/demo
  ref: {ref}
  revision: {revision}
  tracked_paths:
    - skills/SKILL.md
""",
    )


def run_script(source: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--source",
            str(source),
            *args,
        ],
        text=True,
        capture_output=True,
        check=False,
    )


def run_script_with_env(source: Path, *args: str, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--source", str(source), *args],
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )


def write_fake_git(bin_dir: Path, body: str) -> None:
    fake_git = bin_dir / "git"
    write(fake_git, f"#!/usr/bin/env python3\n{body}")
    fake_git.chmod(0o755)


def load_script_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("check_skill_upstreams", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_upstream_refspec_preserves_head_and_full_refs() -> None:
    module = load_script_module()

    assert module.upstream_refspec("HEAD") == "HEAD"
    assert module.upstream_refspec("refs/tags/v1.0.0") == "refs/tags/v1.0.0"
    assert module.upstream_refspec("main") == "refs/heads/main"


def test_skill_upstream_script_lists_locked_revisions_offline(tmp_path: Path) -> None:
    source = tmp_path / "source"
    write_upstream_source(source)

    result = run_script(source, "--offline")

    assert result.returncode == 0, result.stderr + result.stdout
    assert "skill-demo" in result.stdout
    assert "https://github.com/example/demo" in result.stdout
    assert LOCKED_REVISION in result.stdout


def test_skill_upstream_script_accepts_modules_without_upstream(tmp_path: Path) -> None:
    source = tmp_path / "source"
    write_source(source)

    result = run_script(source, "--offline")

    assert result.returncode == 0, result.stderr + result.stdout
    assert "[info] no upstream metadata found" in result.stdout


def test_skill_upstream_script_rejects_malformed_upstream_without_traceback(tmp_path: Path) -> None:
    source = tmp_path / "source"
    write_source(
        source,
        """
upstream:
  repository: https://github.com/example/demo
  ref: main
  tracked_paths: []
""",
    )

    result = run_script(source, "--offline")

    assert result.returncode == 1
    assert "module skill-demo upstream missing revision" in result.stderr
    assert "module skill-demo upstream tracked_paths must be a non-empty list" in result.stderr
    assert "Traceback" not in result.stderr + result.stdout


def test_skill_upstream_script_reports_stale_revision_and_uses_branch_refspec(tmp_path: Path) -> None:
    source = tmp_path / "source"
    write_upstream_source(source)
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    ref_log = tmp_path / "ref.log"
    write_fake_git(
        fake_bin,
        """
import os
import sys
from pathlib import Path

Path(os.environ["FAKE_GIT_REF_LOG"]).write_text(sys.argv[-1], encoding="utf-8")
print("fedcba9876543210fedcba9876543210fedcba98\\t" + sys.argv[-1])
""",
    )
    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}{os.pathsep}{env['PATH']}"
    env["FAKE_GIT_REF_LOG"] = str(ref_log)

    result = run_script_with_env(source, env=env)

    assert result.returncode == 2, result.stderr + result.stdout
    assert (
        f"[stale] skill-demo: https://github.com/example/demo main {LOCKED_REVISION} -> {LATEST_REVISION}"
        in result.stdout
    )
    assert ref_log.read_text(encoding="utf-8") == "refs/heads/main"


def test_skill_upstream_script_reports_remote_errors(tmp_path: Path) -> None:
    source = tmp_path / "source"
    write_upstream_source(source)
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    write_fake_git(
        fake_bin,
        """
import sys

print("network unavailable", file=sys.stderr)
sys.exit(128)
""",
    )
    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}{os.pathsep}{env['PATH']}"

    result = run_script_with_env(source, env=env)

    assert result.returncode == 1
    assert "[error] skill-demo: network unavailable" in result.stderr


def test_skill_upstream_script_rejects_non_positive_timeout(tmp_path: Path) -> None:
    source = tmp_path / "source"
    write_upstream_source(source)

    result = run_script(source, "--timeout", "0")

    assert result.returncode == 1
    assert "[error] --timeout must be greater than 0" in result.stderr
