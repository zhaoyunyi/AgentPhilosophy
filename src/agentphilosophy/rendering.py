from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, StrictUndefined

from .errors import SyncError
from .hashing import sha256_bytes
from .paths import relative_path, render_inline_template, resolve_inside
from .project import build_render_context
from .source import Module, output_strategy, unmanaged_policy


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


def template_env() -> Environment:
    return Environment(undefined=StrictUndefined, autoescape=False, keep_trailing_newline=True)


def render_template(path: Path, context: dict[str, Any]) -> str:
    return template_env().from_string(path.read_text(encoding="utf-8")).render(**context)


def default_custom_rel(paths: dict[str, str], target_rel: str) -> str:
    target = Path(target_rel)
    name = f"{target.stem}.custom{target.suffix}" if target.suffix else f"{target.name}.custom"
    return (Path(paths["custom_dir"]) / target.parent / name).as_posix()


def resolve_module_source(module: Module, value: str) -> Path:
    source = (module.root / value).resolve(strict=False)
    try:
        source.relative_to(module.root.resolve())
    except ValueError as exc:
        raise SyncError(f"{module.name} source escapes module: {value}") from exc
    return source


def render_outputs(
    source_root: Path,
    project_root: Path,
    config: dict[str, Any],
    modules: list[Module],
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
            resolve_inside(project_root, target_rel, label=f"{module.name}:{output.get('id')} target")
            section = str(output.get("section") or "")
            if not section:
                raise SyncError(f"fragment output missing section: {module.name}:{output.get('id')}")
            fragment_context = dict(context)
            fragment_context["section"] = lambda _name: ""
            rendered = render_template(module.root / str(output["template"]), fragment_context)
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
            target_abs = resolve_inside(project_root, target_rel, label=f"{module.name}:{output_id} target")
            target_rel = relative_path(project_root, target_abs)

            if output_type == "rendered_file":
                render_context = dict(context)

                def section(name: str, *, current_target: str = target_rel) -> str:
                    items = sorted(fragments.get((current_target, name), []))
                    return "\n".join(item[3].strip("\n") for item in items)

                render_context["section"] = section
                content_text = render_template(module.root / str(output["template"]), render_context)
                if strategy == "layered":
                    custom_rel = str(output.get("custom") or default_custom_rel(paths, target_rel))
                    custom_abs = resolve_inside(project_root, custom_rel, label=f"{module.name}:{output_id} custom")
                    if custom_abs.exists():
                        content_text = content_text.rstrip() + "\n\n" + custom_abs.read_text(encoding="utf-8")
                content = content_text.encode("utf-8")
                source_bytes = (module.root / str(output["template"])).read_bytes()
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
                if not source_dir.is_dir():
                    raise SyncError(f"copy_tree source is not a directory: {source_dir}")
                for source_file in sorted(path for path in source_dir.rglob("*") if path.is_file()):
                    child_rel = source_file.relative_to(source_dir).as_posix()
                    child_target = resolve_inside(
                        project_root,
                        f"{target_rel.rstrip('/')}/{child_rel}",
                        label=f"{module.name}:{output_id} copy_tree target",
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
