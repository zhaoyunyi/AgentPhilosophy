from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import StrictUndefined
from jinja2.sandbox import SandboxedEnvironment, SecurityError

from .errors import SyncError
from .hashing import sha256_bytes
from .paths import relative_path, render_inline_template, resolve_inside
from .project import build_render_context
from .source import Module, module_tree_files, output_strategy, resolve_module_source, unmanaged_policy


@dataclass(frozen=True)
class RenderedOutput:
    rel_path: str
    content: bytes
    module: str
    output_id: str
    strategy: str
    on_existing_unmanaged: str
    source_hash: str
    rendered_hash: str


def template_env() -> SandboxedEnvironment:
    return SandboxedEnvironment(undefined=StrictUndefined, autoescape=False, keep_trailing_newline=True)


def render_template(path: Path, context: dict[str, Any]) -> str:
    try:
        return template_env().from_string(path.read_text(encoding="utf-8")).render(**context)
    except SecurityError as exc:
        raise SyncError(f"unsafe template expression in {path}: {exc}") from exc


def default_custom_rel(paths: dict[str, str], target_rel: str) -> str:
    target = Path(target_rel)
    name = f"{target.stem}.custom{target.suffix}" if target.suffix else f"{target.name}.custom"
    return (Path(paths["custom_dir"]) / target.parent / name).as_posix()


def render_outputs(
    source_root: Path,
    project_root: Path,
    config: dict[str, Any],
    modules: list[Module],
    *,
    strict_paths: bool = False,
) -> list[RenderedOutput]:
    del source_root
    context = build_render_context(config, modules)
    paths = context["paths"]

    fragments: dict[tuple[str, str], list[tuple[int, str, str, str]]] = {}
    for module in modules:
        for output in module.outputs:
            if output.get("type") != "fragment":
                continue
            target_rel = render_inline_template(str(output.get("target", "")), context)
            resolve_inside(project_root, target_rel, label=f"{module.name}:{output.get('id')} target",
                           reject_symlinks=strict_paths)
            section = str(output.get("section") or "")
            if not section:
                raise SyncError(f"fragment output missing section: {module.name}:{output.get('id')}")
            fragment_context = dict(context)
            fragment_context["section"] = lambda _name: ""
            rendered = render_template(resolve_module_source(module, str(output["template"])), fragment_context)
            fragments.setdefault((target_rel, section), []).append(
                (int(output.get("order") or 0), module.name, str(output.get("id")), rendered)
            )

    outputs: list[RenderedOutput] = []
    for module in modules:
        for output in module.outputs:
            output_type = output.get("type")
            if output_type == "fragment":
                continue
            output_id = str(output.get("id"))
            strategy = output_strategy(output, module)
            policy = unmanaged_policy(output)
            target_rel = render_inline_template(str(output.get("target", "")), context)
            target_abs = resolve_inside(project_root, target_rel, label=f"{module.name}:{output_id} target",
                                        reject_symlinks=strict_paths)
            target_rel = relative_path(project_root, target_abs)

            if output_type == "rendered_file":
                render_context = dict(context)

                def section(name: str, *, current_target: str = target_rel) -> str:
                    items = sorted(fragments.get((current_target, name), []))
                    return "\n".join(item[3].strip("\n") for item in items)

                render_context["section"] = section
                template_path = resolve_module_source(module, str(output["template"]))
                content_text = render_template(template_path, render_context)
                if strategy == "layered":
                    custom_rel = str(output.get("custom") or default_custom_rel(paths, target_rel))
                    custom_abs = resolve_inside(project_root, custom_rel, label=f"{module.name}:{output_id} custom")
                    if custom_abs.exists():
                        content_text = content_text.rstrip() + "\n\n" + custom_abs.read_text(encoding="utf-8")
                content = content_text.encode("utf-8")
                source_bytes = template_path.read_bytes()
                outputs.append(
                    RenderedOutput(
                        rel_path=target_rel,
                        content=content,
                        module=module.name,
                        output_id=output_id,
                        strategy=strategy,
                        on_existing_unmanaged=policy,
                        source_hash=sha256_bytes(source_bytes),
                        rendered_hash=sha256_bytes(content),
                    )
                )
            elif output_type == "copy_file":
                source_abs = resolve_module_source(module, str(output["source"]))
                content = source_abs.read_bytes()
                outputs.append(
                    RenderedOutput(
                        rel_path=target_rel,
                        content=content,
                        module=module.name,
                        output_id=output_id,
                        strategy=strategy,
                        on_existing_unmanaged=policy,
                        source_hash=sha256_bytes(content),
                        rendered_hash=sha256_bytes(content),
                    )
                )
            elif output_type == "copy_tree":
                source_dir = resolve_module_source(module, str(output["source"]))
                for source_file in module_tree_files(module, source_dir):
                    child_rel = source_file.relative_to(source_dir).as_posix()
                    child_target = resolve_inside(
                        project_root,
                        f"{target_rel.rstrip('/')}/{child_rel}",
                        label=f"{module.name}:{output_id} copy_tree target",
                        reject_symlinks=strict_paths,
                    )
                    content = source_file.read_bytes()
                    outputs.append(
                        RenderedOutput(
                            rel_path=relative_path(project_root, child_target),
                            content=content,
                            module=module.name,
                            output_id=f"{output_id}:{child_rel}",
                            strategy=strategy,
                            on_existing_unmanaged=policy,
                            source_hash=sha256_bytes(content),
                            rendered_hash=sha256_bytes(content),
                        )
                    )
            else:
                raise SyncError(f"unsupported output type: {output_type}")
    return outputs
