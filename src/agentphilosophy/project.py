from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import SyncError
from .source import Module
from .yamlio import read_yaml

DEFAULT_PATHS = {
    "agent_work_dir": ".agents",
    "spec_dir": "spec",
    "docs_guide_dir": "docs/guides",
    "custom_dir": ".agents/custom",
    "generated_dir": ".agents/generated",
    "migration_dir": ".agents/migration",
}

DEFAULT_SKILL_TARGETS = {
    "claude_project": ".claude/skills",
    "repo_skills": "skills",
}


def project_config_path(project_root: Path) -> Path:
    return project_root / ".agentphilosophy.yaml"


def migration_config_path(project_root: Path) -> Path:
    return project_root / ".agents" / "migration" / "proposed.agentphilosophy.yaml"


def load_project_config(project_root: Path, *, allow_migration_draft: bool = False) -> dict[str, Any]:
    config_path = project_config_path(project_root)
    if config_path.exists():
        config = read_yaml(config_path)
    elif allow_migration_draft and migration_config_path(project_root).exists():
        config = read_yaml(migration_config_path(project_root))
    else:
        raise SyncError(f"project config not found: {config_path}")
    config.setdefault("project_name", project_root.name)
    config.setdefault("project_type", "unknown")
    config.setdefault("paths", {})
    config.setdefault("skill_targets", {})
    config.setdefault("vars", {})
    config.setdefault("modules", [])
    return config


def preset_path(source_root: Path, name: str) -> Path:
    return source_root / "presets" / f"{name}.yaml"


def load_preset(source_root: Path, name: str) -> dict[str, Any]:
    path = preset_path(source_root, name)
    if not path.exists():
        raise SyncError(f"preset not found: {name}")
    return read_yaml(path)


def build_render_context(config: dict[str, Any], selected_modules: list[Module]) -> dict[str, Any]:
    paths = {**DEFAULT_PATHS, **(config.get("paths") or {})}
    skill_targets = {**DEFAULT_SKILL_TARGETS, **(config.get("skill_targets") or {})}
    merged_vars: dict[str, Any] = {}
    for module in selected_modules:
        default_vars = module.data.get("default_vars") or {}
        if isinstance(default_vars, dict):
            merged_vars.update(default_vars)
    project_vars = config.get("vars") or {}
    if isinstance(project_vars, dict):
        merged_vars.update(project_vars)

    context: dict[str, Any] = {
        "project_name": config.get("project_name"),
        "project_type": config.get("project_type"),
        "description": config.get("description", ""),
        "preset": config.get("preset"),
        "paths": paths,
        "skill_targets": skill_targets,
        "modules": config.get("modules") or [],
        "vars": merged_vars,
    }
    context.update(merged_vars)
    return context


def selected_modules(config: dict[str, Any], modules: dict[str, Module]) -> list[Module]:
    result: list[Module] = []
    for name in config.get("modules") or []:
        if name not in modules:
            raise SyncError(f"project references missing module: {name}")
        result.append(modules[name])
    return result
