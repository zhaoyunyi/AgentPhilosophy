#!/usr/bin/env python3
"""从不可变提交构建，或校验待发布制品的版本与摘要。"""

import argparse
import io
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agentphilosophy.errors import SyncError  # noqa: E402
from agentphilosophy.release import artifact_names, create_receipt, verify_receipt  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["build", "check"])
    parser.add_argument("version")
    parser.add_argument("--revision", required=True, help="build accepts a jj revision; check requires its commit SHA")
    parser.add_argument("--dist", type=Path, default=Path("dist"))
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    try:
        wheel, _ = artifact_names(args.version)
        dist = args.dist.resolve()
        if args.mode == "check":
            receipt = args.receipt or dist / f"agentphilosophy-{args.version}.receipt.json"
            verify_receipt(receipt, dist, args.version, args.revision)
            print("release artifacts verified")
            return 0
        revision = subprocess.check_output(
            ["jj", "log", "-r", args.revision, "--no-graph", "-T", "commit_id"], text=True,
        ).strip()
        with tempfile.TemporaryDirectory(prefix="agentphilosophy-release-build-") as temporary:
            checkout = Path(temporary) / "source"
            checkout.mkdir()
            data = subprocess.check_output(["git", "archive", revision])
            with tarfile.open(fileobj=io.BytesIO(data)) as archive:
                archive.extractall(checkout, filter="data")
            subprocess.run([
                "uv", "run", "--locked", "--project", str(checkout),
                str(checkout / "scripts/sync-packaged-source.py"), "--check",
            ], check=True)
            subprocess.run([
                "uv", "run", "--locked", "--project", str(checkout), str(checkout / "sync.py"),
                "--source", str(checkout), "validate",
            ], check=True)
            subprocess.run(["uv", "build", "--directory", str(checkout), "--out-dir", str(dist)], check=True)
            subprocess.run([
                "bash", str(checkout / "scripts/release-smoke.sh"), str(dist / wheel),
            ], cwd=temporary, check=True)
            print(create_receipt(checkout, dist, args.version, revision))
        return 0
    except (SyncError, OSError, subprocess.SubprocessError, tarfile.TarError) as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
