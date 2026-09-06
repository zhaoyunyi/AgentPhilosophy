import io
import json
import os
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

import pytest

from agentphilosophy.errors import SyncError
from agentphilosophy.release import create_receipt, verify_receipt

REVISION = "a" * 40


def release_fixture(root: Path, version: str = "1.2.3") -> Path:
    files = {
        "pyproject.toml": f'[project]\nname = "agentphilosophy"\nversion = "{version}"\n',
        "src/agentphilosophy/__init__.py": f'__version__ = "{version}"\n',
        "catalog.yaml": "content_version: 1.2.0\n",
        "src/agentphilosophy/default_source/catalog.yaml": "content_version: 1.2.0\n",
    }
    for name, content in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    dist = root / "dist"
    dist.mkdir()
    metadata = f"Name: agentphilosophy\nVersion: {version}\n"
    with zipfile.ZipFile(dist / f"agentphilosophy-{version}-py3-none-any.whl", "w") as archive:
        archive.writestr(f"agentphilosophy-{version}.dist-info/METADATA", metadata)
        for name, content in files.items():
            if name.startswith("src/"):
                archive.writestr(name.removeprefix("src/"), content)
    with tarfile.open(dist / f"agentphilosophy-{version}.tar.gz", "w:gz") as archive:
        for name, content in {**files, "PKG-INFO": metadata}.items():
            data = content.encode()
            entry = tarfile.TarInfo(f"agentphilosophy-{version}/{name}")
            entry.size = len(data)
            archive.addfile(entry, io.BytesIO(data))
    return dist


def test_release_receipt_binds_versions_source_and_archives(tmp_path: Path) -> None:
    dist = release_fixture(tmp_path)
    receipt = create_receipt(tmp_path, dist, "1.2.3", REVISION)
    verified = verify_receipt(receipt, dist, "1.2.3", REVISION)
    assert verified["source_revision"] == REVISION
    assert verified["content_version"] == "1.2.0"
    assert len(verified["artifacts"]) == 2


@pytest.mark.parametrize("kind", ["wheel", "sdist"])
def test_release_rejects_corrupt_archives_before_receipt(tmp_path: Path, kind: str) -> None:
    dist = release_fixture(tmp_path)
    suffix = "-py3-none-any.whl" if kind == "wheel" else ".tar.gz"
    (dist / f"agentphilosophy-1.2.3{suffix}").write_text("not a package")
    with pytest.raises(SyncError):
        create_receipt(tmp_path, dist, "1.2.3", REVISION)
    assert not (dist / "agentphilosophy-1.2.3.receipt.json").exists()


def test_release_rejects_changed_artifacts_and_wrong_revision(tmp_path: Path) -> None:
    dist = release_fixture(tmp_path)
    receipt = create_receipt(tmp_path, dist, "1.2.3", REVISION)
    with pytest.raises(SyncError, match="revision"):
        verify_receipt(receipt, dist, "1.2.3", "b" * 40)
    wheel = dist / "agentphilosophy-1.2.3-py3-none-any.whl"
    wheel.write_bytes(wheel.read_bytes() + b"changed after validation")
    with pytest.raises(SyncError, match="digest"):
        verify_receipt(receipt, dist, "1.2.3", REVISION)


def test_release_rejects_renamed_packages_with_the_wrong_version(tmp_path: Path) -> None:
    dist = release_fixture(tmp_path)
    for path in list(dist.iterdir()):
        path.rename(path.with_name(path.name.replace("1.2.3", "9.9.9")))
    with pytest.raises(SyncError, match="version"):
        create_receipt(tmp_path, dist, "9.9.9", REVISION)


@pytest.mark.parametrize("failure", [None, "corrupt", "revision", "main", "tag", "download"])
def test_publish_verifies_before_creation_and_reads_back_the_frozen_release(
    tmp_path: Path, failure: str | None,
) -> None:
    dist = release_fixture(tmp_path)
    create_receipt(tmp_path, dist, "1.2.3", "b" * 40 if failure == "revision" else REVISION)
    if failure == "corrupt":
        (dist / "agentphilosophy-1.2.3-py3-none-any.whl").write_text("corrupt")
    (tmp_path / "release-notes").mkdir()
    (tmp_path / "release-notes/v1.2.3.md").write_text("测试发布说明\n")
    root = Path(__file__).resolve().parents[1]
    helper = str(root / "scripts/release-artifacts.py")
    commands = {
        "jj": "import sys\nprint('The working copy has no changes.' if sys.argv[1]=='status' else 'a'*40)\n",
        "git": """import os,sys
from pathlib import Path
args=sys.argv[1:]
if args[0]=='ls-remote':
    if '--tags' in args:
        if Path('published.json').exists():
            print(('b' if os.environ.get('FAILURE')=='tag' else 'a')*40+'\\trefs/tags/v1.2.3')
    else:
        print(('b' if os.environ.get('FAILURE')=='main' else 'a')*40+'\\trefs/heads/main')
""",
        "gh": """import json,os,shutil,sys
from pathlib import Path
args=sys.argv[1:]
marker=Path('published.json')
if args[:2]==['release','create']:marker.write_text(json.dumps(args))
elif args[:2]==['release','view']:sys.exit(0 if marker.exists() else 1)
elif args[:2]==['release','download']:
    destination=Path(args[args.index('--dir')+1])
    for path in Path('dist').iterdir():shutil.copy2(path,destination/path.name)
    if os.environ.get('FAILURE')=='download':
        next(destination.glob('*.whl')).write_text('changed download')
""",
        "uv": f"""import subprocess,sys
index=next(i for i,arg in enumerate(sys.argv) if arg.endswith('release-artifacts.py'))
sys.exit(subprocess.run([sys.executable, {helper!r}, *sys.argv[index+1:]]).returncode)
""",
    }
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    for name, body in commands.items():
        path = fake_bin / name
        path.write_text(f"#!{sys.executable}\n{body}")
        path.chmod(0o755)
    env = {**os.environ, "PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}", "FAILURE": failure or ""}
    result = subprocess.run(["bash", str(root / "scripts/publish-release.sh"), "1.2.3"],
                            cwd=tmp_path, env=env, capture_output=True, text=True)
    assert (result.returncode == 0) == (failure is None), result.stdout + result.stderr
    marker = tmp_path / "published.json"
    assert marker.exists() == (failure in {None, "tag", "download"})
    if marker.exists():
        args = json.loads(marker.read_text())
        assert args[args.index("--target") + 1] == REVISION
