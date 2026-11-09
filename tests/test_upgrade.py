from __future__ import annotations

import hashlib
import http.client
import io
import json
import os
import zipfile
from pathlib import Path

import pytest
import yaml

from agentphilosophy import __version__
from agentphilosophy.cli import main
from agentphilosophy.hashing import source_tree_hash


def release_api(monkeypatch, version="1.3.1"):
    """公开 HTTP seam 的离线 Release；不替换同步器或升级器内部行为。"""
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr("agentphilosophy/default_source/catalog.yaml", f"content_version: {version}\n")
        archive.writestr("agentphilosophy/default_source/modules/example/module.yaml", "name: example\n")
        archive.writestr("agentphilosophy/__init__.py", f'__version__ = "{version}"\n')
        archive.writestr(
            f"agentphilosophy-{version}.dist-info/METADATA",
            f"Name: agentphilosophy\nVersion: {version}\n",
        )
    wheel = output.getvalue()
    filename = f"agentphilosophy-{version}-py3-none-any.whl"
    base = "https://github.com/zhaoyunyi/AgentPhilosophy"
    download = f"{base}/releases/download/v{version}/"
    receipt = {
        "schema_version": 1,
        "agentphilosophy_version": version,
        "content_version": version,
        "source_revision": "a" * 40,
        "artifacts": {filename: "sha256:" + hashlib.sha256(wheel).hexdigest()},
    }
    release = {
        "tag_name": f"v{version}", "draft": False, "prerelease": False,
        "html_url": f"{base}/releases/tag/v{version}",
        "assets": [
            {"name": filename, "browser_download_url": download + filename},
            {"name": f"agentphilosophy-{version}.receipt.json",
             "browser_download_url": download + f"agentphilosophy-{version}.receipt.json"},
        ],
    }
    routes = {
        "https://api.github.com/repos/zhaoyunyi/AgentPhilosophy/releases/latest": json.dumps(release).encode(),
        f"https://api.github.com/repos/zhaoyunyi/AgentPhilosophy/git/ref/tags/v{version}":
            json.dumps({"object": {"type": "commit", "sha": "a" * 40}}).encode(),
        download + f"agentphilosophy-{version}.receipt.json": json.dumps(receipt).encode(),
        download + filename: wheel,
    }

    def urlopen(request, **kwargs):
        url = request if isinstance(request, str) else request.full_url
        return io.BytesIO(routes[url])

    monkeypatch.setattr("urllib.request.urlopen", urlopen)
    return routes, receipt, release


def test_user_discovers_stable_release_without_registry(monkeypatch, tmp_path: Path, capsys):
    """Given 无中央仓库；When 检查稳定版；Then 获得固定提交与内容身份。"""
    release_api(monkeypatch)
    monkeypatch.chdir(tmp_path)
    assert main(["check-update", "--format", "json"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "update_available"
    assert result["target"]["version"] == "1.3.1"
    assert result["target"]["source_revision"] == "a" * 40
    assert result["target"]["source_tree_hash"].startswith("sha256:")
    assert result["install_command"][-1] == (
        "git+https://github.com/zhaoyunyi/AgentPhilosophy.git@" + "a" * 40
    )
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("failure", ["offline", "truncated", "digest", "tag", "prerelease"])
def test_user_cannot_mistake_failed_discovery_for_current(monkeypatch, capsys, failure):
    """Given 无法核对正式发布；When 检查；Then 非零退出且明确失败。"""
    routes, _, release = release_api(monkeypatch)
    if failure in {"offline", "truncated"}:
        def offline(*args, **kwargs):
            if failure == "truncated":
                raise http.client.IncompleteRead(b"{", 100)
            raise OSError("offline")
        monkeypatch.setattr("urllib.request.urlopen", offline)
    elif failure == "digest":
        routes[next(url for url in routes if url.endswith(".whl"))] = b"corrupt"
    elif failure == "tag":
        url = next(url for url in routes if "/git/ref/" in url)
        routes[url] = json.dumps({"object": {"type": "commit", "sha": "b" * 40}}).encode()
    else:
        release["prerelease"] = True
        routes[next(url for url in routes if url.endswith("/latest"))] = json.dumps(release).encode()
    assert main(["check-update", "--format", "json"]) == 1
    assert json.loads(capsys.readouterr().out)["status"] == "failed"


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def prepared_project(tmp_path: Path, capsys):
    source, project = tmp_path / "source", tmp_path / "project"
    write(source / "catalog.yaml", "content_version: 1.2.1\nmodules:\n  - name: docs\n")
    write(source / "presets/fullstack.yaml", "name: fullstack\nmodules: [docs]\n")
    module = {
        "name": "docs", "version": "1.0.0", "project_types": ["fullstack"],
        "outputs": [{"id": "agents", "type": "rendered_file", "template": "templates/agents.j2",
                     "target": "AGENTS.md", "strategy": "layered", "on_existing_unmanaged": "report_only"}],
    }
    write(source / "modules/docs/module.yaml", yaml.safe_dump(module))
    write(source / "modules/docs/templates/agents.j2", "旧版规则\n")
    write(project / ".agents/custom/AGENTS.custom.md", "项目定制\n")
    write(project / "user.txt", "用户工作\n")
    assert main(["--source", str(source), "init", str(project), "--preset", "fullstack"]) == 0
    assert main(["--source", str(source), "push", str(project), "--apply"]) == 0
    state_path = project / ".agents/agentphilosophy-state.yaml"
    state = yaml.safe_load(state_path.read_text())
    state["agentphilosophy_version"] = "1.2.1"
    state_path.write_text(yaml.safe_dump(state))
    before = {p.relative_to(project).as_posix(): p.read_bytes() for p in project.rglob("*") if p.is_file()}
    write(source / "catalog.yaml", f"content_version: {__version__}\nmodules:\n  - name: docs\n  - name: extra\n")
    write(source / "modules/docs/templates/agents.j2", "新版规则\n")
    module["version"] = "1.0.1"
    module["outputs"].append({
        "id": "new", "type": "rendered_file", "template": "templates/agents.j2",
        "target": "guides/new.md", "strategy": "managed_replace", "on_existing_unmanaged": "report_only",
    })
    write(source / "modules/docs/module.yaml", yaml.safe_dump(module))
    write(source / "modules/extra/module.yaml", "name: extra\nversion: 1.0.0\noutputs: []\n")
    target = {
        "format_version": 1, "status": "update_available",
        "target": {
            "version": __version__, "tag": f"v{__version__}", "content_version": __version__,
            "source_revision": "a" * 40, "source_tree_hash": source_tree_hash(source),
            "wheel_sha256": "sha256:" + "b" * 64,
            "release_url": f"https://github.com/zhaoyunyi/AgentPhilosophy/releases/tag/v{__version__}",
        },
    }
    target_file = tmp_path / "target.json"
    write(target_file, json.dumps(target))
    capsys.readouterr()
    return source, project, target_file, before


def test_user_previews_upgrade_without_changing_project(tmp_path: Path, capsys):
    """Given 独立项目含定制；When 预览；Then 显示差异和可选模块且不写项目。"""
    source, project, target, before = prepared_project(tmp_path, capsys)
    assert main(["--source", str(source), "upgrade", str(project), "--target", str(target),
                 "--dry-run", "--format", "json"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "ready"
    assert result["optional_modules"] == ["extra"]
    changes = {item["path"]: item for item in result["changes"]}
    assert changes["AGENTS.md"]["action"] == "update"
    assert "+新版规则" in changes["AGENTS.md"]["diff"]
    assert changes["guides/new.md"]["action"] == "add"
    assert before == {p.relative_to(project).as_posix(): p.read_bytes() for p in project.rglob("*") if p.is_file()}


def test_user_upgrades_repeats_and_rolls_back_without_losing_work(tmp_path: Path, capsys):
    """Given 项目有自有文件；When 升级/重复/回退；Then 只还原本次变更。"""
    source, project, target, before = prepared_project(tmp_path, capsys)
    args = ["--source", str(source), "upgrade", str(project), "--target", str(target), "--apply", "--format", "json"]
    assert main(args) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "upgraded"
    upgrade_id = result["upgrade_id"]
    assert (project / "AGENTS.md").read_text() == "新版规则\n\n项目定制\n"
    assert (project / "guides/new.md").read_text() == "新版规则\n"
    assert (project / ".agentphilosophy.yaml").read_bytes() == before[".agentphilosophy.yaml"]
    state_path = project / ".agents/agentphilosophy-state.yaml"
    after_state = state_path.read_bytes()
    assert yaml.safe_load(after_state)["agentphilosophy_version"] == __version__
    assert main(args) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "unchanged"
    assert state_path.read_bytes() == after_state
    (project / "user.txt").write_text("升级后继续写的工作\n")
    rollback = ["rollback", str(project), "--id", upgrade_id, "--apply", "--format", "json"]
    assert main(rollback) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "rolled_back"
    for name, data in before.items():
        if name != "user.txt":
            assert (project / name).read_bytes() == data
    assert not (project / "guides/new.md").exists()
    assert (project / "user.txt").read_text() == "升级后继续写的工作\n"
    assert main(rollback) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "already_rolled_back"


@pytest.mark.parametrize("failure", ["manual", "identity", "downgrade", "major", "symlink"])
def test_user_blocks_unsafe_upgrade_before_any_project_write(tmp_path: Path, capsys, failure):
    """Given 身份/兼容性/手改异常；When apply；Then 整体拒绝且文件保持原样。"""
    source, project, target, _ = prepared_project(tmp_path, capsys)
    if failure == "manual":
        (project / "AGENTS.md").write_text("手改规则\n")
    elif failure == "identity":
        (source / "modules/docs/templates/agents.j2").write_text("准备后源码被改变\n")
    elif failure in {"downgrade", "major"}:
        path = project / ".agents/agentphilosophy-state.yaml"
        state = yaml.safe_load(path.read_text())
        state["agentphilosophy_version"] = "99.0.0" if failure == "downgrade" else "0.9.0"
        path.write_text(yaml.safe_dump(state))
    else:
        (project / "AGENTS.md").unlink()
        (project / "AGENTS.md").symlink_to(project / "user.txt")
    before = {p.relative_to(project).as_posix(): p.read_bytes() for p in project.rglob("*") if p.is_file()}
    assert main(["--source", str(source), "upgrade", str(project), "--target", str(target),
                 "--apply", "--format", "json"]) == 1
    assert json.loads(capsys.readouterr().out)["status"] in {"blocked", "failed"}
    assert before == {p.relative_to(project).as_posix(): p.read_bytes() for p in project.rglob("*") if p.is_file()}


def test_user_cannot_rollback_over_post_upgrade_edits(tmp_path: Path, capsys):
    """Given 升级后又编辑托管文件；When 回退；Then 整体拒绝且保留所有文件。"""
    source, project, target, _ = prepared_project(tmp_path, capsys)
    assert main(["--source", str(source), "upgrade", str(project), "--target", str(target),
                 "--apply", "--format", "json"]) == 0
    upgrade_id = json.loads(capsys.readouterr().out)["upgrade_id"]
    (project / "AGENTS.md").write_text("升级后手改\n")
    before = {p.relative_to(project).as_posix(): p.read_bytes() for p in project.rglob("*") if p.is_file()}
    assert main(["rollback", str(project), "--id", upgrade_id, "--apply", "--format", "json"]) == 1
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "blocked"
    assert "AGENTS.md" in " ".join(result["errors"])
    assert before == {p.relative_to(project).as_posix(): p.read_bytes() for p in project.rglob("*") if p.is_file()}


def test_user_recovers_from_interrupted_file_write(monkeypatch, tmp_path: Path, capsys):
    """Given 文件系统第二次写入失败；When 升级；Then 返回失败并恢复原文件。"""
    source, project, target, before = prepared_project(tmp_path, capsys)
    replace = os.replace
    failed = False

    def fail_once(src, dst, *args, **kwargs):
        nonlocal failed
        if Path(dst) == project / "guides/new.md" and not failed:
            failed = True
            raise OSError("模拟磁盘写入失败")
        return replace(src, dst, *args, **kwargs)

    monkeypatch.setattr(os, "replace", fail_once)
    assert main(["--source", str(source), "upgrade", str(project), "--target", str(target),
                 "--apply", "--format", "json"]) == 1
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "failed"
    assert result["recovery"] == "failed_recovered"
    for name, data in before.items():
        assert (project / name).read_bytes() == data
    assert not (project / "guides/new.md").exists()


def test_user_must_recover_pending_upgrade_before_starting_another(tmp_path: Path, capsys):
    """Given 上次升级中断且快照仍 pending；When 再次升级；Then 指向恢复入口。"""
    source, project, target, _ = prepared_project(tmp_path, capsys)
    identifier = "c" * 32
    write(project / f".agents/upgrades/{identifier}/receipt.json", json.dumps({
        "format_version": 1, "status": "pending", "id": identifier, "project": str(project),
    }))
    assert main(["--source", str(source), "upgrade", str(project), "--target", str(target),
                 "--apply", "--format", "json"]) == 1
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "blocked"
    assert identifier in " ".join(result["errors"])


def test_user_explicitly_migrates_retired_output_and_can_restore_it(tmp_path: Path, capsys):
    """Given 输出改名；When 先预览再显式允许迁移；Then 退役可恢复且定制保留。"""
    source, project, target, before = prepared_project(tmp_path, capsys)
    (project / "AGENTS.md").chmod(0o600)
    path = source / "modules/docs/module.yaml"
    module = yaml.safe_load(path.read_text())
    module["outputs"] = module["outputs"][1:]
    path.write_text(yaml.safe_dump(module))
    data = json.loads(target.read_text())
    data["target"]["source_tree_hash"] = source_tree_hash(source)
    target.write_text(json.dumps(data))
    args = ["--source", str(source), "upgrade", str(project), "--target", str(target), "--apply", "--format", "json"]
    assert main(args) == 1
    assert "AGENTS.md" in " ".join(json.loads(capsys.readouterr().out)["breaking_changes"])
    assert main([*args, "--allow-breaking"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert not (project / "AGENTS.md").exists()
    state = yaml.safe_load((project / ".agents/agentphilosophy-state.yaml").read_text())
    assert "AGENTS.md" not in {item["path"] for item in state["files"]}
    assert main(["rollback", str(project), "--id", result["upgrade_id"], "--apply", "--format", "json"]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "rolled_back"
    assert (project / "AGENTS.md").read_bytes() == before["AGENTS.md"]
    assert (project / "AGENTS.md").stat().st_mode & 0o777 == 0o600


def test_user_recovers_pending_journal_after_process_exit(monkeypatch, tmp_path: Path, capsys):
    """Given 进程在部分写入后退出；When 用 ID 回退；Then 无需旧内容源即可恢复。"""
    source, project, target, before = prepared_project(tmp_path, capsys)
    replace = os.replace

    def exit_during_write(src, dst, *args, **kwargs):
        if Path(dst) == project / "guides/new.md":
            raise SystemExit(99)
        return replace(src, dst, *args, **kwargs)

    monkeypatch.setattr(os, "replace", exit_during_write)
    with pytest.raises(SystemExit, match="99"):
        main(["--source", str(source), "upgrade", str(project), "--target", str(target), "--apply"])
    capsys.readouterr()
    monkeypatch.setattr(os, "replace", replace)
    receipts = list((project / ".agents/upgrades").glob("*/receipt.json"))
    assert len(receipts) == 1
    journal = json.loads(receipts[0].read_text())
    assert journal["status"] == "pending"
    assert (project / "AGENTS.md").read_bytes() != before["AGENTS.md"]
    assert main(["rollback", str(project), "--id", journal["id"], "--apply", "--format", "json"]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "rolled_back"
    for name, content in before.items():
        assert (project / name).read_bytes() == content


@pytest.mark.skipif(os.name == "nt", reason="POSIX 进程锁测试；Windows 使用 msvcrt")
def test_user_cannot_upgrade_while_another_process_owns_lock(tmp_path: Path, capsys):
    """Given 已有项目操作持有 OS 锁；When apply；Then 不并发写入。"""
    import fcntl

    source, project, target, before = prepared_project(tmp_path, capsys)
    lock = project / ".agents/upgrades/.lock"
    lock.parent.mkdir()
    with lock.open("wb") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert main(["--source", str(source), "upgrade", str(project), "--target", str(target),
                     "--apply", "--format", "json"]) == 1
        assert "正在运行" in " ".join(json.loads(capsys.readouterr().out)["errors"])
    for name, content in before.items():
        assert (project / name).read_bytes() == content


@pytest.mark.parametrize("tamper", ["../outside.txt", ".git/config", ".agentphilosophy.yaml", "digest"])
def test_user_rejects_invalid_recovery_snapshot(tmp_path: Path, capsys, tamper):
    """Given 恢复快照被损坏；When rollback；Then 不触碰任何项目文件。"""
    source, project, target, _ = prepared_project(tmp_path, capsys)
    assert main(["--source", str(source), "upgrade", str(project), "--target", str(target),
                 "--apply", "--format", "json"]) == 0
    identifier = json.loads(capsys.readouterr().out)["upgrade_id"]
    path = project / f".agents/upgrades/{identifier}/receipt.json"
    journal = json.loads(path.read_text())
    if tamper == "digest":
        journal["entries"][0]["before"]["sha256"] = "wrong"
    else:
        journal["entries"][0]["path"] = tamper
    path.write_text(json.dumps(journal))
    before = {p.relative_to(project).as_posix(): p.read_bytes() for p in project.rglob("*") if p.is_file()}
    assert main(["rollback", str(project), "--id", identifier, "--apply", "--format", "json"]) == 1
    assert json.loads(capsys.readouterr().out)["status"] == "failed"
    assert before == {p.relative_to(project).as_posix(): p.read_bytes() for p in project.rglob("*") if p.is_file()}


def test_user_rejects_renamed_output_through_project_symlink(tmp_path: Path, capsys):
    """Given 新输出经项目内 symlink 指回旧文件；When 升级；Then 拒绝隐藏的改名。"""
    source, project, target, before = prepared_project(tmp_path, capsys)
    (project / "alias").symlink_to(project, target_is_directory=True)
    path = source / "modules/docs/module.yaml"
    module = yaml.safe_load(path.read_text())
    module["outputs"][0]["target"] = "alias/AGENTS.md"
    path.write_text(yaml.safe_dump(module))
    data = json.loads(target.read_text())
    data["target"]["source_tree_hash"] = source_tree_hash(source)
    target.write_text(json.dumps(data))
    assert main(["--source", str(source), "upgrade", str(project), "--target", str(target),
                 "--apply", "--format", "json"]) == 1
    assert json.loads(capsys.readouterr().out)["status"] in {"blocked", "failed"}
    assert (project / "AGENTS.md").read_bytes() == before["AGENTS.md"]
    assert not (project / ".agents/upgrades").exists()
