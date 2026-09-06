import os
import shlex
import subprocess
from pathlib import Path


def test_documented_command_uses_the_central_python_environment(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    document = (root / "docs/cli/runtime.md").read_text()
    command = next(line for line in document.splitlines() if line.startswith("uv run ") and line.endswith(" validate"))
    args = [argument.replace("/path/to/AgentPhilosophy", str(root)) for argument in shlex.split(command)]
    args[2:2] = ["--locked", "--offline"]
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname="independent-target"\nversion="0.0.0"\nrequires-python=">=3.12"\ndependencies=[]\n'
    )
    env = os.environ.copy()
    env.pop("VIRTUAL_ENV", None)
    result = subprocess.run(args, cwd=tmp_path, env=env, capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "no issues found" in result.stdout
    assert not (tmp_path / ".venv").exists()
