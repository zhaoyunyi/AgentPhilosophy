from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .errors import Report, SyncError
from .yamlio import read_yaml

KNOWN_OUTPUT_TYPES = {"rendered_file", "fragment", "copy_file", "copy_tree"}
KNOWN_STRATEGIES = {"managed_replace", "layered", "init_only", "report_only"}
KNOWN_UNMANAGED_POLICIES = {"fail", "warn", "report_only"}
CONTENT_VERSION_PATTERN = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
UPSTREAM_REVISION_PATTERN = re.compile(r"^[0-9a-f]{40}$")


@dataclass(frozen=True)
class Module:
    name: str
    root: Path
    data: dict[str, Any]

    @property
    def version(self) -> str:
        return str(self.data.get("version", "0.0.0"))

    @property
    def outputs(self) -> list[dict[str, Any]]:
        outputs = self.data.get("outputs") or []
        return outputs if isinstance(outputs, list) else []


def load_modules(source_root: Path, report: Report | None = None) -> dict[str, Module]:
    modules_dir = source_root / "modules"
    modules: dict[str, Module] = {}
    if not modules_dir.is_dir():
        if report:
            report.error(f"missing modules directory: {modules_dir}")
            return {}
        raise SyncError(f"missing modules directory: {modules_dir}")

    for module_dir in sorted(path for path in modules_dir.iterdir() if path.is_dir()):
        module_yaml = module_dir / "module.yaml"
        if not module_yaml.exists():
            if report:
                report.error(f"missing module.yaml: {module_dir}")
                continue
            raise SyncError(f"missing module.yaml: {module_dir}")
        try:
            data = read_yaml(module_yaml)
        except SyncError as exc:
            if report:
                report.error(str(exc))
                continue
            raise
        name = str(data.get("name") or module_dir.name)
        if name in modules:
            if report:
                report.error(f"duplicate module name: {name}")
                continue
            raise SyncError(f"duplicate module name: {name}")
        modules[name] = Module(name=name, root=module_dir, data=data)
    return modules


def output_strategy(output: dict[str, Any], module: Module) -> str:
    return str(output.get("strategy") or module.data.get("default_strategy") or "managed_replace")


def unmanaged_policy(output: dict[str, Any]) -> str:
    return str(output.get("on_existing_unmanaged") or "fail")


def _source_inside_module(module: Module, value: str) -> Path | None:
    source_path = (module.root / value).resolve(strict=False)
    try:
        source_path.relative_to(module.root.resolve())
    except ValueError:
        return None
    return source_path


def validate_module_shape(module: Module, all_modules: set[str], report: Report) -> None:
    data = module.data
    if not data.get("name"):
        report.error(f"{module.root}/module.yaml missing name")
    validate_module_upstream(module, report)

    outputs = data.get("outputs")
    if outputs is None:
        outputs = []
    if not isinstance(outputs, list):
        report.error(f"module {module.name} outputs must be a list")
        return

    seen_output_ids: set[str] = set()
    for output in outputs:
        if not isinstance(output, dict):
            report.error(f"module {module.name} output must be a mapping")
            continue
        output_id = output.get("id")
        if not output_id:
            report.error(f"module {module.name} output missing id")
        elif str(output_id) in seen_output_ids:
            report.error(f"module {module.name} has duplicate output id: {output_id}")
        else:
            seen_output_ids.add(str(output_id))

        output_type = str(output.get("type") or "")
        if output_type not in KNOWN_OUTPUT_TYPES:
            report.error(f"module {module.name} output {output_id} has unknown type: {output_type}")

        strategy = output_strategy(output, module)
        if strategy not in KNOWN_STRATEGIES:
            report.error(f"module {module.name} output {output_id} has unknown strategy: {strategy}")

        policy = unmanaged_policy(output)
        if policy not in KNOWN_UNMANAGED_POLICIES:
            report.error(
                f"module {module.name} output {output_id} has unknown on_existing_unmanaged: {policy}"
            )

        if output_type in {"rendered_file", "fragment"}:
            template = output.get("template")
            if not template:
                report.error(f"module {module.name} output {output_id} missing template")
            elif not (module.root / str(template)).is_file():
                report.error(f"module {module.name} output {output_id} template not found: {template}")
        if output_type in {"copy_file", "copy_tree"}:
            source = output.get("source")
            if not source:
                report.error(f"module {module.name} output {output_id} missing source")
            else:
                source_path = _source_inside_module(module, str(source))
                if source_path is None:
                    report.error(
                        f"module {module.name} output {output_id} source escapes module: {source}"
                    )
                elif not source_path.exists():
                    report.error(
                        f"module {module.name} output {output_id} source not found: {source}"
                    )

    for required in data.get("requires") or []:
        if required not in all_modules:
            report.error(f"module {module.name} requires missing module: {required}")
    for conflict in data.get("conflicts") or []:
        if conflict not in all_modules:
            report.warn(f"module {module.name} conflict references unknown module: {conflict}")


def validate_module_upstream(module: Module, report: Report) -> None:
    upstream = module.data.get("upstream")
    if upstream is None:
        return
    if not isinstance(upstream, dict):
        report.error(f"module {module.name} upstream must be a mapping")
        return

    repository = upstream.get("repository")
    if not repository:
        report.error(f"module {module.name} upstream missing repository")
    elif not isinstance(repository, str):
        report.error(f"module {module.name} upstream repository must be a string")

    ref = upstream.get("ref")
    if not ref:
        report.error(f"module {module.name} upstream missing ref")
    elif not isinstance(ref, str):
        report.error(f"module {module.name} upstream ref must be a string")

    revision = upstream.get("revision")
    if not revision:
        report.error(f"module {module.name} upstream missing revision")
    elif not isinstance(revision, str) or not UPSTREAM_REVISION_PATTERN.fullmatch(revision):
        report.error(f"module {module.name} upstream revision must be a 40 character git SHA")

    tracked_paths = upstream.get("tracked_paths")
    if not isinstance(tracked_paths, list) or not tracked_paths:
        report.error(f"module {module.name} upstream tracked_paths must be a non-empty list")
    elif any(not isinstance(path, str) or not path for path in tracked_paths):
        report.error(f"module {module.name} upstream tracked_paths entries must be non-empty strings")


def validate_catalog(source_root: Path, modules: dict[str, Module], report: Report) -> None:
    catalog_path = source_root / "catalog.yaml"
    if not catalog_path.exists():
        report.warn("catalog.yaml not found")
        return
    try:
        catalog = read_yaml(catalog_path)
    except SyncError as exc:
        report.error(str(exc))
        return
    content_version = catalog.get("content_version")
    if content_version is None:
        report.error("catalog.yaml missing content_version")
    elif parse_content_version(str(content_version)) is None:
        report.error("catalog.yaml content_version must use MAJOR.MINOR.PATCH")
    declared: set[str] = set()
    catalog_modules = catalog.get("modules") or []
    if not isinstance(catalog_modules, list):
        report.error("catalog.yaml modules must be a list")
        return
    for item in catalog_modules:
        if not isinstance(item, dict) or not item.get("name"):
            report.error("catalog.yaml module entry must contain name")
            continue
        name = str(item["name"])
        declared.add(name)
        if name not in modules:
            report.error(f"catalog.yaml references missing module: {name}")
    for name in sorted(set(modules) - declared):
        report.warn(f"module exists but is not listed in catalog.yaml: {name}")


def source_content_version(source_root: Path) -> str:
    catalog_path = source_root / "catalog.yaml"
    if not catalog_path.exists():
        return "0.0.0"
    catalog = read_yaml(catalog_path)
    return str(catalog.get("content_version") or "0.0.0")


def parse_content_version(version: str) -> tuple[int, int, int] | None:
    match = CONTENT_VERSION_PATTERN.fullmatch(version)
    if not match:
        return None
    return tuple(int(part) for part in match.groups())


def compare_content_versions(left: str, right: str) -> int | None:
    left_parts = parse_content_version(left)
    right_parts = parse_content_version(right)
    if left_parts is None or right_parts is None:
        return None
    return (left_parts > right_parts) - (left_parts < right_parts)


def validate_presets(source_root: Path, modules: dict[str, Module], report: Report) -> None:
    presets_dir = source_root / "presets"
    if not presets_dir.exists():
        return
    for preset_path in sorted(presets_dir.glob("*.yaml")):
        try:
            preset = read_yaml(preset_path)
        except SyncError as exc:
            report.error(str(exc))
            continue
        for module_name in preset.get("modules") or []:
            if module_name not in modules:
                report.error(f"preset {preset_path.name} references missing module: {module_name}")


def validate_source(source_root: Path) -> Report:
    report = Report()
    modules = load_modules(source_root, report)
    names = set(modules)
    for module in modules.values():
        validate_module_shape(module, names, report)
    validate_catalog(source_root, modules, report)
    validate_presets(source_root, modules, report)
    return report
