#!/usr/bin/env python3
"""用临时仓库验证真实密钥扫描入口和本地凭据忽略规则，不访问任何凭据服务。"""

import os
import secrets
import shutil
import string
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(*args: str, cwd: Path, expected: int = 0) -> subprocess.CompletedProcess:
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=False)
    assert result.returncode == expected, f"command failed: {args[0]} exit={result.returncode}"
    return result


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="agentphilosophy-secret-scan-test-") as temporary:
        project = Path(temporary)
        run("git", "init", "-q", cwd=project)
        run("git", "config", "user.name", "Secret Scan Test", cwd=project)
        run("git", "config", "user.email", "test@example.test", cwd=project)
        shutil.copyfile(ROOT / ".gitignore", project / ".gitignore")
        # user Given 本地凭据与示例；When git 判断忽略；Then 凭据忽略、示例可提交。
        for name in (".env", ".env.local", "app/.env.production", "id_rsa", "id_ed25519", "credentials.json"):
            run("git", "check-ignore", "-q", name, cwd=project)
        for name in (".env.example", ".env.sample", ".env.template", "app/.env.example", "README.md"):
            run("git", "check-ignore", "-q", name, cwd=project, expected=1)
        (project / "README.md").write_text("# 无凭据的测试项目\n")
        run("git", "add", ".", cwd=project)
        run("git", "commit", "-qm", "clean example", cwd=project)
        # user Given 干净历史；When 扫描；Then 成功。
        scanner = str(ROOT / "scripts/check-secrets.sh")
        run("bash", scanner, str(project), cwd=project)
        # 离线合成格式样本，没有对应账号或权限；分段构造避免自身成为历史密钥命中。
        sample = "gh" + "p_" + "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(36))
        (project / "config.txt").write_text("access_token=" + sample + "\n")
        run("git", "add", "config.txt", cwd=project)
        run("git", "commit", "-qm", "synthetic detector fixture", cwd=project)
        # user Given 历史中的合成格式样本；When 扫描；Then 阻断且日志不回显值。
        result = run("bash", scanner, str(project), cwd=project, expected=1)
        assert sample not in result.stdout + result.stderr
        # user Given 最新树已移除样本但历史仍含样本；When 扫描；Then 仍阻断。
        (project / "config.txt").write_text("access_token_from_environment=true\n")
        run("git", "add", "config.txt", cwd=project)
        run("git", "commit", "-qm", "remove fixture from latest tree", cwd=project)
        result = run("bash", scanner, str(project), cwd=project, expected=1)
        assert sample not in result.stdout + result.stderr
        # user Given 工具不可用；When 扫描；Then 不得跳过并报成功。
        environment = dict(os.environ)
        environment["PATH"] = str(project / "empty-bin")
        missing = subprocess.run(["/bin/bash", scanner, str(project)], env=environment,
                                 capture_output=True, text=True, check=False)
        assert missing.returncode != 0
    print("凭据忽略、干净历史、合成泄露阻断和日志脱敏验证通过")


if __name__ == "__main__":
    main()
