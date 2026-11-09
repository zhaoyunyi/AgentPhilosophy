"""项目内有限文件集合的升级快照、进程锁和受保护恢复。"""

from __future__ import annotations

import base64
import json
import os
import re
import uuid
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path

from .errors import SyncError
from .fileio import write_bytes_atomic
from .hashing import sha256_bytes

JOURNALS = ".agents/upgrades"
STATE = ".agents/agentphilosophy-state.yaml"
CONFIG = ".agentphilosophy.yaml"


def project_file(project: Path, relative: str) -> Path:
    """只接受项目内普通路径，并拒绝任何符号链接祖先。"""
    path = Path(relative)
    if path.is_absolute() or not path.parts or ".." in path.parts or path.as_posix() != relative:
        raise SyncError(f"升级文件路径不安全：{relative}")
    if path.parts[0] in {".git", ".jj"}:
        raise SyncError(f"升级不得修改版本控制文件：{relative}")
    current = project
    for part in path.parts:
        current = current / part
        if current.is_symlink():
            raise SyncError(f"升级路径包含符号链接：{relative}")
    if current.exists() and not current.is_file():
        raise SyncError(f"升级目标不是普通文件：{relative}")
    return current


@contextmanager
def project_lock(project: Path) -> Iterator[None]:
    lock_path = project_file(project, f"{JOURNALS}/.lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    ignore = project_file(project, f"{JOURNALS}/.gitignore")
    if not ignore.exists():
        write_bytes_atomic(ignore, b"*\n")
    with lock_path.open("a+b") as handle:
        os.chmod(lock_path, 0o600)
        if os.name == "nt":
            import msvcrt

            if lock_path.stat().st_size == 0:
                handle.write(b"0")
                handle.flush()
            handle.seek(0)
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as exc:
                raise SyncError("本项目已有升级或回退正在运行") from exc
        else:
            import fcntl

            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                raise SyncError("本项目已有升级或回退正在运行") from exc
        try:
            yield
        finally:
            if os.name == "nt":
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle, fcntl.LOCK_UN)


def snapshot(path: Path) -> dict | None:
    if not path.exists():
        return None
    return encode_snapshot(path.read_bytes(), path.stat().st_mode & 0o777)


def encode_snapshot(data: bytes, mode: int) -> dict:
    return {"content": base64.b64encode(data).decode(), "sha256": sha256_bytes(data), "mode": mode}


def decode_snapshot(value: dict | None) -> bytes | None:
    if value is None:
        return None
    try:
        data = base64.b64decode(value["content"], validate=True)
        if (sha256_bytes(data) != value["sha256"] or type(value["mode"]) is not int
                or not 0 <= value["mode"] <= 0o777):
            raise ValueError("快照摘要或权限无效")
        return data
    except (KeyError, TypeError, ValueError) as exc:
        raise SyncError(f"快照完整性检查失败：{exc}") from exc


def save_journal(path: Path, journal: dict) -> None:
    write_bytes_atomic(path, (json.dumps(journal, ensure_ascii=False, indent=2) + "\n").encode())
    os.chmod(path, 0o600)


def pending_upgrades(project: Path, active_id: str | None = None) -> list[str]:
    project_file(project, f"{JOURNALS}/.lock")
    pending = []
    for path in sorted((project / JOURNALS).glob("*/receipt.json")):
        if path.parent.name == active_id:
            continue
        project_file(project, path.relative_to(project).as_posix())
        try:
            journal = json.loads(path.read_text())
            if not isinstance(journal, dict) or journal.get("status") not in {
                "applied", "rolled_back", "failed_recovered",
            }:
                pending.append(path.parent.name)
        except (OSError, ValueError):
            pending.append(path.parent.name)
    return pending


def restore(project: Path, entries: list[dict], *, partial: bool) -> None:
    # 整体预检完成前不恢复任何文件；防止后续手改被部分回退掩盖。
    conflicts = []
    for entry in entries:
        current = snapshot(project_file(project, entry["path"]))
        if current != entry["after"] and not (partial and current == entry["before"]):
            conflicts.append(entry["path"])
    if conflicts:
        raise SyncError("回退遇到后续修改，未覆盖：" + ", ".join(conflicts))
    for entry in reversed(entries):
        path = project_file(project, entry["path"])
        before = entry["before"]
        data = decode_snapshot(before)
        current = snapshot(path)
        if current == before:
            continue
        if current != entry["after"]:
            raise SyncError(f"回退期间文件发生变化：{entry['path']}")
        if data is None:
            path.unlink(missing_ok=True)
        else:
            write_bytes_atomic(path, data)
            os.chmod(path, before["mode"])
    for entry in entries:
        if snapshot(project_file(project, entry["path"])) != entry["before"]:
            raise SyncError(f"回退验证失败：{entry['path']}")


def apply_transaction(project: Path, writes: dict[str, bytes | None], target: dict,
                      preflight: Callable[[str], None], verify: Callable[[], None]) -> dict:
    identifier = uuid.uuid4().hex
    journal_path = project_file(project, f"{JOURNALS}/{identifier}/receipt.json")
    journal_path.parent.mkdir(mode=0o700)
    entries = []
    for relative, content in writes.items():
        path = project_file(project, relative)
        before = snapshot(path)
        entries.append({
            "path": relative, "before": before,
            "after": encode_snapshot(content, before["mode"] if before else 0o644) if content is not None else None,
        })
    journal = {
        "format_version": 1, "id": identifier, "project": str(project),
        "status": "pending", "target": target, "entries": entries,
    }
    save_journal(journal_path, journal)
    try:
        preflight(identifier)
        for entry in entries:
            path = project_file(project, entry["path"])
            if snapshot(path) != entry["before"]:
                raise SyncError(f"写入前文件发生变化：{entry['path']}")
            data = decode_snapshot(entry["after"])
            if data is None:
                path.unlink(missing_ok=True)
            else:
                write_bytes_atomic(path, data)
                os.chmod(path, entry["after"]["mode"])
        verify()
        for entry in entries:
            if snapshot(project_file(project, entry["path"])) != entry["after"]:
                raise SyncError(f"升级写入验证失败：{entry['path']}")
        journal["status"] = "applied"
        save_journal(journal_path, journal)
        return {"status": "upgraded", "upgrade_id": identifier, "verification": "passed"}
    except (OSError, SyncError, KeyboardInterrupt) as exc:
        errors = [f"升级未完成：{exc}"]
        try:
            restore(project, entries, partial=True)
            journal["status"] = "failed_recovered"
        except (OSError, SyncError) as recovery:
            journal["status"] = "recovery_required"
            errors.append(str(recovery))
        try:
            save_journal(journal_path, journal)
        except OSError as receipt_error:
            errors.append(f"回执更新失败，保留原 pending 快照供恢复：{receipt_error}")
        return {"status": "failed", "upgrade_id": identifier,
                "recovery": journal["status"], "errors": errors}


def rollback(project: Path, identifier: str, *, apply: bool = False) -> dict:
    if not re.fullmatch(r"[0-9a-f]{32}", identifier):
        raise SyncError("升级 ID 格式无效")
    path = project_file(project, f"{JOURNALS}/{identifier}/receipt.json")
    try:
        journal = json.loads(path.read_text())
        if (journal["format_version"] != 1 or journal["id"] != identifier or journal["project"] != str(project)
                or journal["status"] not in {
                    "pending", "applied", "rolled_back", "rolling_back", "failed_recovered", "recovery_required",
                } or not isinstance(journal["entries"], list) or not journal["entries"]):
            raise ValueError("快照身份或状态无效")
        names = set()
        for entry in journal["entries"]:
            name = entry["path"]
            project_file(project, name)
            if name == CONFIG or name.startswith(f"{JOURNALS}/") or name in names:
                raise ValueError("快照包含禁止恢复或重复的路径")
            names.add(name)
            decode_snapshot(entry["before"])
            decode_snapshot(entry["after"])
        if STATE not in names:
            raise ValueError("快照缺少同步 state")
    except (ValueError, TypeError, KeyError) as exc:
        raise SyncError(f"无效升级快照：{exc}") from exc
    result = {"format_version": 1, "upgrade_id": identifier, "errors": []}
    if journal["status"] in {"rolled_back", "failed_recovered"}:
        return {**result, "status": "already_rolled_back"}
    partial = journal["status"] != "applied"
    for entry in journal["entries"]:
        current = snapshot(project_file(project, entry["path"]))
        if current != entry["after"] and not (partial and current == entry["before"]):
            result["errors"].append(f"回退遇到后续修改：{entry['path']}")
    if result["errors"]:
        return {**result, "status": "blocked"}
    if not apply:
        return {**result, "status": "ready", "restore_paths": sorted(names)}
    with project_lock(project):
        # 获锁后重新读取，避免等待期间其他事务或用户修改快照。
        if json.loads(path.read_text()) != journal:
            raise SyncError("回退快照已变化，请重新检查")
        journal["status"] = "rolling_back"
        save_journal(path, journal)
        try:
            restore(project, journal["entries"], partial=partial)
            journal["status"] = "rolled_back"
        except (OSError, SyncError, KeyboardInterrupt) as exc:
            journal["status"] = "recovery_required"
            save_journal(path, journal)
            return {**result, "status": "failed", "errors": [str(exc)], "recovery": "recovery_required"}
        save_journal(path, journal)
    return {**result, "status": "rolled_back", "verification": "passed"}
