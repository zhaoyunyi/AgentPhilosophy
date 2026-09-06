import shutil
import subprocess
import zipfile
from pathlib import Path


def test_wheel_excludes_unlisted_resources_and_local_caches(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    for name in ("pyproject.toml", "setup.py", "src/agentphilosophy/__init__.py",
                 "src/agentphilosophy/content.py", "src/agentphilosophy/errors.py"):
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root / name, target)
    (tmp_path / "README.md").write_text("# Packaging fixture\n")
    packaged = tmp_path / "src/agentphilosophy/default_source"
    packaged.mkdir()
    (packaged / "catalog.yaml").write_text("content_version: 0.1.0\n")
    for name in ("unlisted.txt", ".DS_Store", "__pycache__/internal.pyc"):
        path = packaged / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"MUST_NOT_BE_DISTRIBUTED")
    result = subprocess.run(
        ["uv", "build", "--offline", "--wheel", "--directory", str(tmp_path), "--out-dir", str(tmp_path / "dist")],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    with zipfile.ZipFile(next((tmp_path / "dist").glob("*.whl"))) as archive:
        resources = {name for name in archive.namelist() if "/default_source/" in name}
        assert resources == {"agentphilosophy/default_source/catalog.yaml"}
