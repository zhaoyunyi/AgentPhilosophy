from __future__ import annotations

import difflib
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jinja2 import UndefinedError

from . import __version__ as agentphilosophy_version
from .errors import Report, SyncError
from .fileio import write_bytes_atomic
from .hashing import sha256_file, source_revision, source_tree_hash
from .paths import candidate_diff_file_for, candidate_file_for, relative_path, render_inline_template, resolve_inside
from .project import (
    DEFAULT_PATHS,
    DEFAULT_SKILL_TARGETS,
    load_preset,
    load_project_config,
    migration_config_path,
    project_config_path,
    selected_modules,
    validate_project_config_shape,
)
from .rendering import RenderedOutput, render_outputs
from .source import Module, compare_content_versions, load_modules, source_content_version, validate_source
from .state import load_state, state_file_map, write_state
from .yamlio import read_yaml, write_yaml


@dataclass
class PlannedAction:
    output: RenderedOutput
    action: str
    reason: str = ""


def command_validate(source_root: Path, project: Path | None = None) -> Report:
    report = validate_source(source_root)
    if report.ok:
        report.extend(validate_source_presets(source_root))
    if project is not None and report.ok:
        report.extend(validate_target(source_root, project))
    return report


def validate_source_presets(source_root: Path) -> Report:
    report = Report()
    try:
        modules = load_modules(source_root, report)
    except SyncError as exc:
        report.error(str(exc))
        return report
    presets_dir = source_root / "presets"
    if not presets_dir.exists():
        return report

    for preset_path in sorted(presets_dir.glob("*.yaml")):
        preset_name = preset_path.stem
        try:
            preset_data = load_preset(source_root, preset_name)
            config = {
                "project_name": f"{preset_name}-validation",
                "project_type": preset_data.get("name") or preset_name,
                "preset": preset_name,
                "description": preset_data.get("description", ""),
                "paths": preset_data.get("paths") if preset_data.get("paths") is not None else {},
                "skill_targets": (
                    preset_data.get("skill_targets") if preset_data.get("skill_targets") is not None else {}
                ),
                "modules": preset_data.get("modules") if preset_data.get("modules") is not None else [],
                "vars": preset_data.get("vars") if preset_data.get("vars") is not None else {},
            }
            shape = validate_project_config_shape(config, label=f"preset {preset_name}")
            report.extend(shape)
            if shape.errors:
                continue
            error_count = len(report.errors)
            selected = validate_config_modules(
                source_root,
                source_root / ".agentphilosophy-validate" / preset_name,
                config,
                modules,
                report,
                label=f"preset {preset_name}",
            )
            if len(report.errors) > error_count:
                continue
            rendered_outputs = render_outputs(
                source_root,
                source_root / ".agentphilosophy-validate" / preset_name,
                config,
                selected,
            )
            written_targets: dict[str, str] = {}
            for output in rendered_outputs:
                owner = f"{output.module}:{output.output_id}"
                previous = written_targets.get(output.rel_path)
                if previous:
                    report.error(
                        f"preset {preset_name} writes {output.rel_path} multiple times: {previous}, {owner}"
                    )
                written_targets[output.rel_path] = owner
        except (SyncError, UndefinedError) as exc:
            report.error(f"preset {preset_name} render invalid: {exc}")
    return report


def validate_target(source_root: Path, project_root: Path) -> Report:
    report = Report()
    try:
        modules = load_modules(source_root, report)
        config = load_project_config(project_root)
    except SyncError as exc:
        report.error(str(exc))
        return report

    shape = validate_project_config_shape(config)
    report.extend(shape)
    if shape.errors:
        return report

    preset = config.get("preset")
    if preset and not (source_root / "presets" / f"{preset}.yaml").is_file():
        report.error(f"project preset not found: {preset}")

    selected = validate_config_modules(source_root, project_root, config, modules, report)
    if report.errors:
        return report

    try:
        rendered_outputs = render_outputs(source_root, project_root, config, selected)
        written_targets: dict[str, str] = {}
        for output in rendered_outputs:
            owner = f"{output.module}:{output.output_id}"
            previous = written_targets.get(output.rel_path)
            if previous:
                report.error(f"multiple outputs write {output.rel_path}: {previous}, {owner}")
            written_targets[output.rel_path] = owner
    except (SyncError, UndefinedError) as exc:
        report.error(str(exc))
    return report


def validate_config_modules(
    source_root: Path,
    project_root: Path,
    config: dict[str, Any],
    modules: dict[str, Module],
    report: Report,
    *,
    label: str = "project",
) -> list[Module]:
    del source_root, project_root
    selected_names = list(config.get("modules") or [])
    selected_set = set(selected_names)
    selected: list[Module] = []
    error_count = len(report.errors)
    for name in selected_names:
        if name not in modules:
            report.error(f"{label} references missing module: {name}")
        else:
            selected.append(modules[name])
    if len(report.errors) > error_count:
        return selected

    for module in selected:
        for required in module.data.get("requires") or []:
            if required not in selected_set:
                report.error(f"{label} module {module.name} requires disabled module: {required}")
        for conflict in module.data.get("conflicts") or []:
            if conflict in selected_set:
                report.error(f"{label} module {module.name} conflicts with enabled module: {conflict}")
        project_types = module.data.get("project_types") or []
        if (
            project_types
            and config.get("project_type") not in project_types
            and not config.get("allow_project_type_mismatch", False)
        ):
            report.warn(f"{label} module {module.name} is not declared for project_type={config.get('project_type')}")
    return selected


def command_init(source_root: Path, project_root: Path, preset: str | None) -> Report:
    report = Report()
    try:
        project_root.mkdir(parents=True, exist_ok=True)
        config_path = project_config_path(project_root)
        if config_path.exists():
            raise SyncError(f"project config already exists: {config_path}")
        preset_data: dict[str, Any] = {}
        if preset:
            preset_data = load_preset(source_root, preset)
        config = {
            "project_name": project_root.name,
            "project_type": preset or preset_data.get("name") or "unknown",
            "preset": preset,
            "description": preset_data.get("description", ""),
            "paths": preset_data.get("paths") or {},
            "skill_targets": preset_data.get("skill_targets") or {},
            "modules": preset_data.get("modules") or [],
            "vars": preset_data.get("vars") or {},
        }
        write_yaml(config_path, config)
        report.info(f"created {config_path}")
    except SyncError as exc:
        report.error(str(exc))
    return report


def _prompt_value(input_fn: Callable[[str], str], label: str, default: str) -> str:
    suffix = f" [{default}]" if default else ""
    value = input_fn(f"{label}{suffix}: ").strip()
    return value or default


def command_init_interactive(
    source_root: Path,
    project_root: Path,
    preset: str | None,
    *,
    input_fn: Callable[[str], str] | None = None,
) -> Report:
    report = Report()
    try:
        if input_fn is None:
            input_fn = input
        project_root.mkdir(parents=True, exist_ok=True)
        config_path = project_config_path(project_root)
        if config_path.exists():
            raise SyncError(f"project config already exists: {config_path}")

        preset_names = sorted(path.stem for path in (source_root / "presets").glob("*.yaml"))
        if preset:
            default_preset = preset
        elif "fullstack" in preset_names:
            default_preset = "fullstack"
        else:
            default_preset = preset_names[0] if preset_names else ""
        selected_preset = _prompt_value(input_fn, "preset", default_preset)
        if selected_preset.lower() in {"none", "no", "skip"}:
            selected_preset = ""
        preset_data = load_preset(source_root, selected_preset) if selected_preset else {}

        project_name = _prompt_value(input_fn, "project_name", project_root.name)
        project_type = _prompt_value(
            input_fn,
            "project_type",
            selected_preset or preset_data.get("name") or "unknown",
        )
        description = _prompt_value(input_fn, "description", preset_data.get("description", ""))

        vars_data = dict(preset_data.get("vars") or {})
        test_command = _prompt_value(input_fn, "test_command", str(vars_data.get("test_command", "")))
        if test_command:
            vars_data["test_command"] = test_command

        config = {
            "project_name": project_name,
            "project_type": project_type,
            "preset": selected_preset or None,
            "description": description,
            "paths": preset_data.get("paths") or {},
            "skill_targets": preset_data.get("skill_targets") or {},
            "modules": preset_data.get("modules") or [],
            "vars": vars_data,
        }
        write_yaml(config_path, config)
        report.info(f"created {config_path}")
    except (EOFError, OSError, KeyboardInterrupt) as exc:
        report.error(f"interactive input unavailable: {exc}")
    except SyncError as exc:
        report.error(str(exc))
    return report


def build_push_plan(source_root: Path, project_root: Path) -> tuple[Report, list[PlannedAction]]:
    report = command_validate(source_root, project_root)
    if not report.ok:
        return report, []
    try:
        modules = load_modules(source_root)
        config = load_project_config(project_root)
        rendered = render_outputs(source_root, project_root, config, selected_modules(config, modules))
        state = load_state(project_root, source_root)
        state_map = state_file_map(state)
    except (SyncError, UndefinedError) as exc:
        report.error(str(exc))
        return report, []

    plan: list[PlannedAction] = []
    for output in rendered:
        target = project_root / output.rel_path
        record = state_map.get(output.rel_path)
        if output.strategy == "report_only":
            plan.append(PlannedAction(output, "report_only", "strategy is report_only"))
        elif not target.exists():
            plan.append(PlannedAction(output, "add"))
        elif record:
            if not target.is_file():
                plan.append(PlannedAction(output, "conflict", "managed file is not a regular file"))
            else:
                current_hash = sha256_file(target)
                if current_hash == output.rendered_hash:
                    plan.append(PlannedAction(output, "skip", "already up to date"))
                elif current_hash != record.get("last_written_hash"):
                    plan.append(PlannedAction(output, "conflict", "managed file was changed manually"))
                else:
                    plan.append(PlannedAction(output, "update"))
        elif output.strategy == "init_only":
            plan.append(PlannedAction(output, "skip", "target exists and strategy is init_only"))
        elif output.on_existing_unmanaged == "warn":
            plan.append(PlannedAction(output, "skip", "target exists unmanaged"))
        elif output.on_existing_unmanaged == "report_only":
            plan.append(PlannedAction(output, "conflict", "target exists but is unmanaged"))
        else:
            plan.append(PlannedAction(output, "conflict", "target exists but is unmanaged"))
    return report, plan


def command_push(source_root: Path, project_root: Path, *, apply: bool) -> Report:
    report, plan = build_push_plan(source_root, project_root)
    if not report.ok:
        return report

    conflicts = [item for item in plan if item.action == "conflict"]
    for item in plan:
        detail = f"{item.action}: {item.output.rel_path}"
        if item.reason:
            detail += f" ({item.reason})"
        report.info(detail)

    if not apply:
        return report

    migration_dir = project_root / DEFAULT_PATHS["migration_dir"]
    report_only = [item for item in plan if item.action == "report_only"]
    for item in [*report_only, *conflicts]:
        _write_candidate_artifacts(project_root, migration_dir, item, report)
        if item.action == "conflict":
            report.error(f"conflict: {item.output.rel_path} ({item.reason})")
    if conflicts:
        return report

    modules = load_modules(source_root)
    config = load_project_config(project_root)
    state = load_state(project_root, source_root)
    state["agentphilosophy_version"] = agentphilosophy_version
    state["source"] = str(source_root)
    state["source_content_version"] = source_content_version(source_root)
    state["source_revision"] = source_revision(source_root)
    state["source_tree_hash"] = source_tree_hash(source_root)
    state["last_synced"] = datetime.now(UTC).isoformat()
    state["modules"] = {
        module.name: module.version for module in selected_modules(config, modules)
    }
    state_files = state_file_map(state)

    for item in plan:
        if item.action not in {"add", "update", "skip"}:
            continue
        if item.action == "skip" and item.reason != "already up to date":
            continue
        if item.action in {"add", "update"}:
            target = project_root / item.output.rel_path
            write_bytes_atomic(target, item.output.content)
        state_files[item.output.rel_path] = {
            "path": item.output.rel_path,
            "module": item.output.module,
            "output_id": item.output.output_id,
            "strategy": item.output.strategy,
            "source_hash": item.output.source_hash,
            "rendered_hash": item.output.rendered_hash,
            "last_written_hash": item.output.rendered_hash,
        }

    state["files"] = [state_files[key] for key in sorted(state_files)]
    write_state(project_root, state)
    return report


def _write_candidate_artifacts(
    project_root: Path,
    migration_dir: Path,
    item: PlannedAction,
    report: Report,
) -> None:
    candidate = candidate_file_for(migration_dir, item.output.rel_path)
    write_bytes_atomic(candidate, item.output.content)
    diff_path = candidate_diff_file_for(migration_dir, item.output.rel_path)
    write_bytes_atomic(diff_path, _candidate_diff(project_root, item.output.rel_path, item.output.content))
    report.info(f"diff: {relative_path(project_root, diff_path)}")


def _candidate_diff(project_root: Path, rel_path: str, candidate_content: bytes) -> bytes:
    current_path = project_root / rel_path
    if current_path.exists() and not current_path.is_file():
        return f"Cannot diff existing non-file target: {rel_path}\n".encode()
    try:
        current_text = current_path.read_text(encoding="utf-8") if current_path.exists() else ""
        candidate_text = candidate_content.decode("utf-8")
    except OSError as exc:
        return f"Cannot read existing target for diff: {rel_path} ({exc})\n".encode()
    except UnicodeDecodeError:
        return f"Binary files differ: {rel_path}\n".encode()

    diff = difflib.unified_diff(
        current_text.splitlines(keepends=True),
        candidate_text.splitlines(keepends=True),
        fromfile=f"current/{rel_path}",
        tofile=f"candidate/{rel_path}",
    )
    return "".join(diff).encode("utf-8")


def command_prune_managed(source_root: Path, project_root: Path) -> Report:
    report = command_validate(source_root, project_root)
    if not report.ok:
        return report
    try:
        modules = load_modules(source_root)
        config = load_project_config(project_root)
        active_outputs = {
            output.rel_path
            for output in render_outputs(
                source_root,
                project_root,
                config,
                selected_modules(config, modules),
            )
        }
        state = load_state(project_root, source_root)
        state_files = state_file_map(state)

        prune_records = [
            record
            for rel_path, record in sorted(state_files.items())
            if rel_path not in active_outputs
        ]
        if not prune_records:
            report.info("no managed files to prune")
            return report

        for record in prune_records:
            rel_path = str(record.get("path"))
            target = resolve_inside(project_root, rel_path, label="managed file")
            if target.exists():
                if not target.is_file():
                    raise SyncError(f"refuse to prune managed path that is not a regular file: {rel_path}")
                if sha256_file(target) != record.get("last_written_hash"):
                    raise SyncError(f"refuse to prune changed managed file: {rel_path}")

        removed: set[str] = set()
        for record in prune_records:
            rel_path = str(record.get("path"))
            target = resolve_inside(project_root, rel_path, label="managed file")
            if target.exists():
                parent = target.parent
                target.unlink()
                _remove_empty_leaf_dir(project_root, parent)
                report.info(f"pruned {rel_path}")
            else:
                report.info(f"removed missing managed record: {rel_path}")
            removed.add(rel_path)

        state["files"] = [
            record
            for record in state.get("files") or []
            if isinstance(record, dict) and str(record.get("path")) not in removed
        ]
        state["agentphilosophy_version"] = agentphilosophy_version
        write_state(project_root, state)
    except (SyncError, UndefinedError) as exc:
        report.error(str(exc))
    return report


def _remove_empty_leaf_dir(project_root: Path, start: Path) -> None:
    project_root = project_root.resolve()
    agent_root = (project_root / DEFAULT_PATHS["agent_work_dir"]).resolve()
    target = start.resolve()
    if target in {project_root, agent_root}:
        return
    try:
        target.rmdir()
    except OSError:
        return


def command_push_all(source_root: Path, *, apply: bool) -> Report:
    report = Report()
    registry = source_root / "registry.yaml"
    try:
        data = read_yaml(registry)
    except SyncError as exc:
        report.error(str(exc))
        return report

    projects = data.get("projects") or []
    if not isinstance(projects, list):
        report.error("registry.yaml projects must be a list")
        return report
    for item in projects:
        if not isinstance(item, dict) or not item.get("path"):
            report.error("registry project entry must contain path")
            continue
        name = str(item.get("name") or Path(str(item["path"])).name)
        child = command_push(source_root, Path(str(item["path"])).expanduser().resolve(), apply=apply)
        for message in child.infos:
            report.info(f"{name}: {message}")
        for message in child.warnings:
            report.warn(f"{name}: {message}")
        for message in child.errors:
            report.error(f"{name}: {message}")
    return report


def command_migrate(source_root: Path, project_root: Path, *, write_config: bool = False) -> Report:
    report = Report()
    project_root.mkdir(parents=True, exist_ok=True)
    migration_dir = project_root / DEFAULT_PATHS["migration_dir"]
    migration_dir.mkdir(parents=True, exist_ok=True)

    interesting: list[Path] = []
    fixed = ["AGENTS.md", "CLAUDE.md"]
    for rel in fixed:
        path = project_root / rel
        if path.exists():
            interesting.append(path)
    for pattern in (
        "spec/**/*.md",
        "docs/guides/**/*.md",
        "docs/guide/**/*.md",
        ".codex/skills/**/SKILL.md",
        ".claude/skills/**/SKILL.md",
        "skills/**/SKILL.md",
    ):
        interesting.extend(path for path in project_root.glob(pattern) if path.is_file())
    interesting = sorted(set(interesting), key=lambda item: item.relative_to(project_root).as_posix())

    inventory_lines = ["# AgentPhilosophy 迁移盘点", ""]
    if interesting:
        for path in interesting:
            inventory_lines.append(f"- `{path.relative_to(project_root).as_posix()}`")
    else:
        inventory_lines.append("- 未发现既有 Agent/Spec/Skill 文件")
    write_bytes_atomic((migration_dir / "inventory.md"), ("\n".join(inventory_lines) + "\n").encode("utf-8"))

    modules = load_modules(source_root)
    preset_name = _default_preset_name(source_root)
    preset_data = load_preset(source_root, preset_name) if preset_name else {}
    proposed_modules = preset_data.get("modules") or list(modules)
    proposed = {
        "project_name": project_root.name,
        "project_type": preset_name or "unknown",
        "preset": preset_name,
        "description": f"{project_root.name} migrated by AgentPhilosophy",
        "paths": preset_data.get("paths") or {},
        "skill_targets": preset_data.get("skill_targets") or {},
        "modules": proposed_modules,
        "vars": preset_data.get("vars") or {},
    }
    write_yaml(migration_config_path(project_root), proposed)
    if write_config:
        config_path = project_config_path(project_root)
        if config_path.exists():
            report.error(f"project config already exists: {config_path}")
        else:
            write_yaml(config_path, proposed)
            report.info(f"created {config_path}")

    rendered_outputs = []
    try:
        rendered_outputs = render_outputs(
            source_root,
            project_root,
            proposed,
            selected_modules(proposed, modules),
        )
        for output in rendered_outputs:
            candidate = candidate_file_for(migration_dir, output.rel_path)
            write_bytes_atomic(candidate, output.content)
    except (SyncError, UndefinedError) as exc:
        report.warn(f"candidate generation skipped: {exc}")

    rendered_by_rel = {output.rel_path: (output.module, output.output_id) for output in rendered_outputs}
    adopt_files = []
    for path in interesting:
        rel = path.relative_to(project_root).as_posix()
        match = rendered_by_rel.get(rel) or _find_output_for_rel(modules, rel)
        if match:
            adopt_files.append({"path": rel, "module": match[0], "output_id": match[1]})
    write_yaml(migration_dir / "adopt-plan.yaml", {"files": adopt_files})
    report.info(f"wrote migration report to {migration_dir}")
    return report


def command_adopt(
    source_root: Path,
    project_root: Path,
    *,
    file: str | None,
    module: str | None,
    output: str | None,
    from_report: str | None,
) -> Report:
    report = Report()
    try:
        entries: list[dict[str, str]] = []
        if from_report:
            report_path = resolve_inside(project_root, from_report, label="adopt report")
            data = read_yaml(report_path)
            entries = [
                {
                    "path": str(item["path"]),
                    "module": str(item["module"]),
                    "output_id": str(item["output_id"]),
                }
                for item in data.get("files") or []
            ]
        elif file and module and output:
            entries = [{"path": file, "module": module, "output_id": output}]
        else:
            raise SyncError("adopt requires --file/--module/--output or --from-report")

        modules = load_modules(source_root)
        try:
            config = load_project_config(project_root, allow_migration_draft=True)
            valid_outputs = _adoptable_outputs(source_root, project_root, config, modules)
        except (SyncError, UndefinedError) as exc:
            raise SyncError(f"cannot validate adopt target: {exc}") from exc
        state = load_state(project_root, source_root)
        state_files = state_file_map(state)
        for entry in entries:
            target = resolve_inside(project_root, entry["path"], label="adopt file")
            if not target.exists():
                raise SyncError(f"adopt target does not exist: {entry['path']}")
            _assert_output_exists(modules, entry["module"], entry["output_id"])
            rel = relative_path(project_root, target)
            current_hash = sha256_file(target)
            if (rel, entry["module"], entry["output_id"]) not in valid_outputs:
                raise SyncError(
                    f"adopt file does not match output target: {rel} -> "
                    f"{entry['module']}:{entry['output_id']}"
                )
            existing = state_files.get(rel)
            if existing and existing.get("last_written_hash") != current_hash:
                raise SyncError(f"refuse to adopt changed managed file: {rel}")
            state_files[rel] = {
                "path": rel,
                "module": entry["module"],
                "output_id": entry["output_id"],
                "strategy": "managed_replace",
                "source_hash": current_hash,
                "rendered_hash": current_hash,
                "last_written_hash": current_hash,
            }
            state.setdefault("modules", {})[entry["module"]] = modules[entry["module"]].version
            report.info(f"adopted {rel}")
        state["source"] = str(source_root)
        state["agentphilosophy_version"] = agentphilosophy_version
        state["source_content_version"] = source_content_version(source_root)
        state["source_revision"] = source_revision(source_root)
        state["source_tree_hash"] = source_tree_hash(source_root)
        state["files"] = [state_files[key] for key in sorted(state_files)]
        write_state(project_root, state)
    except SyncError as exc:
        report.error(str(exc))
    return report


def command_status(source_root: Path, project_root: Path | None = None) -> Report:
    report = Report()
    if project_root is None:
        registry = source_root / "registry.yaml"
        if not registry.exists():
            report.warn("registry.yaml not found")
            return report
        try:
            data = read_yaml(registry)
        except SyncError as exc:
            report.error(str(exc))
            return report
        for project in data.get("projects") or []:
            if not isinstance(project, dict) or not project.get("path"):
                report.error("registry project entry must contain path")
                continue
            path = Path(str(project.get("path", ""))).expanduser().resolve()
            name = str(project.get("name") or path.name)
            if not path.exists():
                report.warn(f"{name}: missing")
                continue
            report.info(f"{name}: reachable")
            child = command_status(source_root, path)
            for message in child.errors:
                report.error(f"{name}: {message}")
            for message in child.warnings:
                report.warn(f"{name}: {message}")
            for message in child.infos:
                report.info(f"{name}: {message}")
        return report

    try:
        state = load_state(project_root, source_root)
        state_agentphilosophy_version = str(state.get("agentphilosophy_version") or "0.0.0")
        if state_agentphilosophy_version != agentphilosophy_version:
            comparison = compare_content_versions(state_agentphilosophy_version, agentphilosophy_version)
            if comparison is None:
                report.warn(
                    f"agentphilosophy_version differs: "
                    f"{state_agentphilosophy_version} -> {agentphilosophy_version}"
                )
            elif comparison < 0:
                report.warn(
                    f"agentphilosophy_version stale: "
                    f"{state_agentphilosophy_version} -> {agentphilosophy_version}"
                )
            else:
                report.warn(
                    f"agentphilosophy_version newer than current CLI: "
                    f"{state_agentphilosophy_version} -> {agentphilosophy_version}"
                )
        current_content_version = source_content_version(source_root)
        state_content_version = str(state.get("source_content_version") or "0.0.0")
        if state_content_version != current_content_version:
            comparison = compare_content_versions(state_content_version, current_content_version)
            if comparison is None:
                report.warn(f"source_content_version differs: {state_content_version} -> {current_content_version}")
            elif comparison < 0:
                report.warn(f"source_content_version stale: {state_content_version} -> {current_content_version}")
            else:
                report.warn(
                    f"source_content_version newer than current source: "
                    f"{state_content_version} -> {current_content_version}"
                )
        current_source_hash = source_tree_hash(source_root)
        current_revision = source_revision(source_root)
        source_hash_drifted = state.get("source_tree_hash") != current_source_hash
        if source_hash_drifted:
            report.warn("source_tree_hash differs from current source")
        if source_hash_drifted and state.get("source_revision") != current_revision:
            report.warn("source_revision differs from current source")

        modules = load_modules(source_root)
        state_modules = state.get("modules") or {}
        for name, version in state_modules.items():
            module = modules.get(str(name))
            if not module:
                report.warn(f"managed module missing from source: {name}")
            elif str(version) != module.version:
                report.warn(f"module version stale: {name}")

        active_outputs: set[str] | None = None
        if not project_config_path(project_root).exists():
            report.warn("project config missing")
        else:
            try:
                config = load_project_config(project_root)
                active_outputs = {
                    output.rel_path
                    for output in render_outputs(
                        source_root,
                        project_root,
                        config,
                        selected_modules(config, modules),
                    )
                }
            except (SyncError, UndefinedError) as exc:
                report.warn(f"project config status check failed: {exc}")

        for record in state.get("files") or []:
            path = project_root / str(record.get("path"))
            if not path.exists():
                report.warn(f"managed file missing: {record.get('path')}")
            elif not path.is_file():
                report.warn(f"managed file is not a regular file: {record.get('path')}")
            elif sha256_file(path) != record.get("last_written_hash"):
                report.warn(f"managed file changed manually: {record.get('path')}")
            elif active_outputs is not None and record.get("path") not in active_outputs:
                report.warn(f"managed file can be pruned: {record.get('path')}")
        report.info(f"status checked: {project_root}")
    except SyncError as exc:
        report.error(str(exc))
    return report


def _default_preset_name(source_root: Path) -> str | None:
    presets = sorted((source_root / "presets").glob("*.yaml"))
    if not presets:
        return None
    return presets[0].stem


def _find_output_for_rel(modules: dict[str, Module], rel_path: str) -> tuple[str, str] | None:
    for module in modules.values():
        context = {
            "project_name": "project",
            "project_type": "unknown",
            "description": "",
            "paths": DEFAULT_PATHS,
            "skill_targets": DEFAULT_SKILL_TARGETS,
            "modules": [],
            "vars": {},
        }
        for output in module.outputs:
            if output.get("type") == "fragment":
                continue
            target = str(output.get("target", ""))
            try:
                rendered = render_inline_template(target, context)
            except Exception:
                continue
            if rendered == rel_path:
                return module.name, str(output.get("id"))
    return None


def _assert_output_exists(modules: dict[str, Module], module_name: str, output_id: str) -> None:
    if module_name not in modules:
        raise SyncError(f"adopt module not found: {module_name}")
    for output in modules[module_name].outputs:
        base_id = str(output.get("id"))
        if base_id == output_id or output_id.startswith(f"{base_id}:"):
            return
    raise SyncError(f"adopt output not found: {module_name}:{output_id}")


def _adoptable_outputs(
    source_root: Path,
    project_root: Path,
    config: dict[str, Any],
    modules: dict[str, Module],
) -> set[tuple[str, str, str]]:
    rendered = render_outputs(source_root, project_root, config, selected_modules(config, modules))
    return {(output.rel_path, output.module, output.output_id) for output in rendered}
