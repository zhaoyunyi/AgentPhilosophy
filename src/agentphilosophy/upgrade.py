"""外部项目升级合同：复用同步计划，保留项目选择与可恢复的变更边界。"""

from __future__ import annotations

import difflib
import json
from dataclasses import dataclass
from pathlib import Path

import yaml

from . import __version__
from .commands import PlannedAction, build_push_plan, command_validate, state_after_push
from .errors import SyncError
from .hashing import sha256_bytes, source_tree_hash
from .project import load_project_config, selected_modules
from .source import load_modules, source_content_version
from .state import load_state, state_file_map
from .upgrade_journal import CONFIG, STATE, apply_transaction, pending_upgrades, project_file, project_lock
from .upgrade_release import DIGEST, REPOSITORY, SHA, version_tuple


def read_target(path: Path) -> dict:
    try:
        data = json.loads(path.read_text())
        if not isinstance(data, dict) or data.get("format_version") != 1:
            raise ValueError("不支持的目标格式")
        if data.get("status") not in {"current", "update_available", "local_newer"}:
            raise ValueError("目标并非成功的发布检查结果")
        target = data["target"]
        if not isinstance(target, dict):
            raise ValueError("target 必须为对象")
        for name in ("version", "content_version"):
            version_tuple(target[name])
        if (target["tag"] != f"v{target['version']}"
                or target["release_url"] != f"{REPOSITORY}/releases/tag/{target['tag']}"
                or not SHA.fullmatch(target["source_revision"])
                or not DIGEST.fullmatch(target["source_tree_hash"])
                or not DIGEST.fullmatch(target["wheel_sha256"])):
            raise ValueError("发布身份不完整")
        return target
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise SyncError(f"升级目标文件无效，请重新 check-update：{exc}") from exc


@dataclass
class UpgradePlan:
    summary: dict
    actions: list[PlannedAction]
    retired: list[str]
    state: dict
    observed: dict[str, str | None]


def prepare_upgrade(source: Path, project: Path, target_file: Path, *, allow_breaking: bool = False,
                    active_id: str | None = None) -> UpgradePlan:
    target = read_target(target_file)
    if __version__ != target["version"]:
        raise SyncError(f"先安装固定目标 CLI：当前 {__version__}，目标 {target['version']}")
    if (source_content_version(source) != target["content_version"]
            or source_tree_hash(source) != target["source_tree_hash"]):
        raise SyncError("当前内容源与已核对的发布目标不一致，请检查安装包或 --source")
    for relative in (CONFIG, STATE):
        if not project_file(project, relative).is_file():
            raise SyncError(f"项目尚未完整接入：缺少 {relative}，请先完成接入")
    state = load_state(project, source)
    if state.get("schema_version") != 1 or not isinstance(state.get("files"), list):
        raise SyncError("不支持的项目 state，不能自动升级")
    if any(not isinstance(item, dict) or not isinstance(item.get("path"), str) for item in state["files"]):
        raise SyncError("项目 state 的托管文件登记无效")
    state_map = state_file_map(state)
    for relative in state_map:
        if relative in {CONFIG, STATE} or relative.startswith(".agents/upgrades/"):
            raise SyncError(f"state 不得把配置、状态或快照登记为托管输出：{relative}")
        project_file(project, relative)
    config = load_project_config(project)
    modules = load_modules(source)
    selected = selected_modules(config, modules)
    report, actions = build_push_plan(source, project, strict_paths=True)
    blockers = list(report.errors)
    blockers.extend(
        f"存在未完成升级，先检查 rollback --id {identifier}" for identifier in pending_upgrades(project, active_id)
    )
    breaking = []

    def compare(label: str, old: str, new: str):
        before, after = version_tuple(old), version_tuple(new)
        if after < before:
            blockers.append(f"{label} 不允许降级：{old} -> {new}；请使用 rollback 恢复已有升级")
        elif after[0] != before[0]:
            breaking.append(f"{label} 跨主版本：{old} -> {new}")

    compare("CLI", state.get("agentphilosophy_version", ""), target["version"])
    compare("内容源", state.get("source_content_version", ""), target["content_version"])
    previous_modules = state.get("modules")
    if not isinstance(previous_modules, dict):
        raise SyncError("项目 state 的 modules 无效")
    for module in selected:
        if module.name in previous_modules:
            compare(f"模块 {module.name}", str(previous_modules[module.name]), module.version)
    if set(previous_modules) != {module.name for module in selected}:
        breaking.append("项目配置的模块选择与上次同步不同，请先确认选择变更")
    active = {action.output.rel_path for action in actions}
    retired = sorted(set(state_map) - active)
    observed = {}
    for relative in sorted(active | set(state_map) | {CONFIG, STATE}):
        if relative == CONFIG and relative in active:
            raise SyncError("模块不能覆盖项目配置")
        if relative.startswith(".agents/upgrades/") or relative == ".agents/upgrade.lock":
            raise SyncError("模块不能覆盖升级快照或锁")
        if relative == STATE and relative in active:
            raise SyncError("模块不能覆盖同步 state")
        path = project_file(project, relative)
        observed[relative] = sha256_bytes(path.read_bytes()) if path.exists() else None
    for relative in retired:
        breaking.append(f"托管输出退役或改名：{relative}")
        if observed[relative] is not None and observed[relative] != state_map[relative].get("last_written_hash"):
            blockers.append(f"退役文件有手改：{relative}")
    changes = []
    for action in actions:
        if action.action == "conflict":
            blockers.append(f"文件冲突：{action.output.rel_path}（{action.reason}）")
        if action.action == "report_only":
            blockers.append(f"输出需要人工处理：{action.output.rel_path}（report_only）")
        if action.action != "skip":
            path = project_file(project, action.output.rel_path)
            before = path.read_bytes() if path.exists() else b""
            try:
                diff = "".join(difflib.unified_diff(
                    before.decode().splitlines(keepends=True),
                    action.output.content.decode().splitlines(keepends=True),
                    fromfile=f"a/{action.output.rel_path}", tofile=f"b/{action.output.rel_path}",
                ))
            except UnicodeError:
                diff = "二进制文件内容变化"
            changes.append({"path": action.output.rel_path, "action": action.action, "diff": diff})
    changes.extend({"path": name, "action": "remove", "diff": "托管输出退役"} for name in retired)
    if breaking and not allow_breaking:
        blockers.append("存在不兼容变化；评估迁移并获得用户决定后才能使用 --allow-breaking")
    return UpgradePlan({
        "format_version": 1, "status": "blocked" if blockers else "ready", "target": target,
        "changes": changes, "errors": blockers, "breaking_changes": breaking,
        "warnings": report.warnings,
        "optional_modules": sorted(set(modules) - {module.name for module in selected}),
    }, actions, retired, state, observed)


def upgrade(source: Path, project: Path, target_file: Path, *, apply: bool = False,
            allow_breaking: bool = False) -> dict:
    plan = prepare_upgrade(source, project, target_file, allow_breaking=allow_breaking)
    if not apply or plan.summary["status"] != "ready":
        return plan.summary
    with project_lock(project):
        plan = prepare_upgrade(source, project, target_file, allow_breaking=allow_breaking)
        if plan.summary["status"] != "ready":
            return plan.summary
        target = plan.summary["target"]
        state = state_after_push(source, project, plan.actions, revision="git:" + target["source_revision"])
        state["release_target"] = target
        state["files"] = [item for item in state["files"] if item["path"] not in plan.retired]
        writes = {
            item.output.rel_path: item.output.content for item in plan.actions if item.action in {"add", "update"}
        }
        writes.update(dict.fromkeys(plan.retired))
        if not writes and {k: v for k, v in state.items() if k != "last_synced"} == {
            k: v for k, v in plan.state.items() if k != "last_synced"
        }:
            return {**plan.summary, "status": "unchanged", "verification": "passed"}
        writes[STATE] = yaml.safe_dump(state, allow_unicode=True, sort_keys=False).encode()

        def preflight(identifier: str):
            current = prepare_upgrade(source, project, target_file, allow_breaking=allow_breaking, active_id=identifier)
            if current.observed != plan.observed or current.summary != plan.summary:
                raise SyncError("升级计划准备期间项目或内容源发生变化，请重新预览")

        def verify():
            report = command_validate(source, project)
            if not report.ok or source_tree_hash(source) != target["source_tree_hash"]:
                raise SyncError("升级后内容源或配置验证失败：" + "; ".join(report.errors))
            report, actions = build_push_plan(source, project, strict_paths=True)
            if not report.ok or any(action.action in {"add", "update", "conflict"} for action in actions):
                raise SyncError("升级后托管输出未达到目标状态")
            for relative, digest in plan.observed.items():
                if relative in writes:
                    continue
                path = project_file(project, relative)
                actual = sha256_bytes(path.read_bytes()) if path.exists() else None
                if actual != digest:
                    raise SyncError(f"升级期间其他输入文件发生变化：{relative}")

        return {**plan.summary, **apply_transaction(project, writes, target, preflight, verify)}
