from __future__ import annotations

import argparse
import json
import shlex
import sys
from collections.abc import Sequence
from pathlib import Path

from . import __version__
from .commands import (
    command_adopt,
    command_init,
    command_init_interactive,
    command_migrate,
    command_prune_managed,
    command_push,
    command_push_all,
    command_status,
    command_validate,
)
from .errors import Report, SyncError
from .resources import LLM_USAGE_MODE_REL_PATHS, llm_usage_path, read_llm_usage, resolve_source_root


def build_parser(*, prog: str | None = None) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=prog or "sync.py")
    parser.add_argument(
        "--source",
        help=(
            "AgentPhilosophy central source root. Defaults to the current "
            "directory when it is a central source, otherwise the packaged source."
        ),
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="Validate central source or target project.")
    validate.add_argument("project", nargs="?")

    init = subparsers.add_parser("init", help="Create a project configuration draft.")
    init.add_argument("project")
    init.add_argument("--preset", help="Preset name used to seed the project configuration.")
    init.add_argument(
        "--interactive",
        action="store_true",
        help="Prompt for preset, project metadata, and test command.",
    )

    migrate = subparsers.add_parser("migrate", help="Generate report-only migration artifacts.")
    migrate.add_argument("project")
    migrate.add_argument(
        "--write-config",
        action="store_true",
        help="Also write .agentphilosophy.yaml when the target does not already have one.",
    )

    adopt = subparsers.add_parser("adopt", help="Adopt existing files into managed state.")
    adopt.add_argument("project")
    adopt.add_argument("--file")
    adopt.add_argument("--module")
    adopt.add_argument("--output")
    adopt.add_argument("--from-report")

    push = subparsers.add_parser("push", help="Render and sync managed outputs.")
    push.add_argument("project", nargs="?")
    push.add_argument("--all", action="store_true", help="Run push for all projects declared in registry.yaml.")
    mode = push.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="preview without writing target files")
    mode.add_argument("--apply", action="store_true", help="write rendered outputs and managed state")
    push.add_argument(
        "--prune-managed",
        action="store_true",
        help="prune stale managed files whose current hash still matches state",
    )
    push.add_argument(
        "--update-docs",
        action="store_true",
        help="after batch apply, invoke an LLM command for configured project documentation",
    )
    push.add_argument(
        "--llm-command",
        help="sandboxed Codex exec command that reads the documentation task from standard input",
    )
    push.add_argument(
        "--llm-timeout",
        type=int,
        default=900,
        help="timeout in seconds for each LLM documentation update (default: 900)",
    )
    push.add_argument(
        "--project-name",
        action="append",
        dest="project_names",
        help="limit --all to a named registry project; repeat to select multiple projects",
    )

    llm_usage = subparsers.add_parser("llm-usage", help="Print an LLM usage document for the selected source.")
    llm_usage.add_argument(
        "--mode",
        choices=sorted(LLM_USAGE_MODE_REL_PATHS),
        default="full",
        help="Usage profile to print.",
    )
    llm_usage.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format. JSON is currently available for --mode user-breakpoints.",
    )

    status = subparsers.add_parser("status", help="Show registry or project status.")
    status.add_argument("--project")

    check_update = subparsers.add_parser("check-update", help="Discover and verify an official stable release.")
    check_update.add_argument("--project")
    check_update.add_argument("--version", help="Select a specific stable release instead of latest.")
    check_update.add_argument("--format", choices=["text", "json"], default="text")
    upgrade = subparsers.add_parser("upgrade", help="Preview or apply a verified release to one project.")
    upgrade.add_argument("project")
    upgrade.add_argument("--target", required=True, help="JSON captured from check-update --format json.")
    upgrade.add_argument("--allow-breaking", action="store_true", help="Apply a user-approved migration.")
    upgrade_mode = upgrade.add_mutually_exclusive_group()
    upgrade_mode.add_argument("--dry-run", action="store_true")
    upgrade_mode.add_argument("--apply", action="store_true")
    upgrade.add_argument("--format", choices=["text", "json"], default="text")
    rollback = subparsers.add_parser("rollback", help="Preview or restore one project upgrade snapshot.")
    rollback.add_argument("project")
    rollback.add_argument("--id", required=True, dest="upgrade_id")
    rollback_mode = rollback.add_mutually_exclusive_group()
    rollback_mode.add_argument("--dry-run", action="store_true")
    rollback_mode.add_argument("--apply", action="store_true")
    rollback.add_argument("--format", choices=["text", "json"], default="text")
    return parser


def format_upgrade(result: dict) -> str:
    lines = [result["status"]]
    if "upgrade_id" in result:
        lines.append(f"升级 ID：{result['upgrade_id']}")
    for field in ("errors", "warnings", "breaking_changes"):
        lines.extend(str(message) for message in result.get(field, []))
    for item in result.get("changes", []):
        lines.append(f"{item['action']}: {item['path']}")
        lines.append(item["diff"])
    if result.get("optional_modules"):
        lines.append("可选新增模块（未自动采用）：" + ", ".join(result["optional_modules"]))
    lines.extend(f"恢复：{path}" for path in result.get("restore_paths", []))
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser(prog=Path(sys.argv[0]).name)
    args = parser.parse_args(argv)

    if args.command in {"upgrade", "rollback"}:
        from .upgrade import upgrade
        from .upgrade_journal import rollback

        try:
            project = Path(args.project).expanduser().resolve()
            if args.command == "rollback":
                result = rollback(project, args.upgrade_id, apply=args.apply)
            else:
                with resolve_source_root(args.source) as source_root:
                    result = upgrade(source_root, project, Path(args.target).expanduser().resolve(),
                                     apply=args.apply, allow_breaking=args.allow_breaking)
        except (SyncError, OSError) as exc:
            result = {"format_version": 1, "status": "failed", "errors": [str(exc)]}
        print(json.dumps(result, ensure_ascii=False, indent=2) if args.format == "json" else format_upgrade(result))
        return 1 if result["status"] in {"failed", "blocked"} else 0

    if args.command == "check-update":
        from .upgrade_release import check_update

        try:
            result = check_update(Path(args.project).expanduser().resolve() if args.project else None, args.version)
        except (SyncError, OSError) as exc:
            result = {"format_version": 1, "status": "failed", "errors": [str(exc)]}
        if args.format == "json":
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif result["status"] == "failed":
            print("\n".join(result["errors"]))
        else:
            print(f"{result['status']}: {result['installed_version']} -> {result['target']['version']}")
            print(result["target"]["release_url"])
            print(shlex.join(result["install_command"]))
        return 1 if result["status"] == "failed" else 0

    with resolve_source_root(args.source) as source_root:
        if args.command == "llm-usage":
            path = llm_usage_path(source_root, args.mode, args.format)
            if path is None:
                report = Report()
                report.error(f"LLM usage format not supported: mode={args.mode} format={args.format}")
                print(report.format())
                return 1
            if not path.is_file():
                report = Report()
                report.error(f"LLM usage document not found: {path}")
                print(report.format())
                return 1
            try:
                text = read_llm_usage(path)
            except (OSError, SyncError) as exc:
                report = Report()
                report.error(str(exc))
                print(report.format())
                return 1
            print(text, end="")
            return 0

        if args.command == "validate":
            report = command_validate(
                source_root,
                Path(args.project).expanduser().resolve() if args.project else None,
            )
        elif args.command == "init":
            if args.interactive:
                report = command_init_interactive(
                    source_root,
                    Path(args.project).expanduser().resolve(),
                    args.preset,
                )
            else:
                report = command_init(source_root, Path(args.project).expanduser().resolve(), args.preset)
        elif args.command == "migrate":
            report = command_migrate(
                source_root,
                Path(args.project).expanduser().resolve(),
                write_config=bool(args.write_config),
            )
        elif args.command == "adopt":
            report = command_adopt(
                source_root,
                Path(args.project).expanduser().resolve(),
                file=args.file,
                module=args.module,
                output=args.output,
                from_report=args.from_report,
            )
        elif args.command == "push":
            if args.update_docs and (not args.all or not args.apply):
                report = Report()
                report.error("push --update-docs requires --all --apply")
                print(report.format())
                return 1
            if args.update_docs and not (args.llm_command or "").strip():
                report = Report()
                report.error("push --update-docs requires --llm-command")
                print(report.format())
                return 1
            if args.llm_command and not args.update_docs:
                report = Report()
                report.error("push --llm-command requires --update-docs")
                print(report.format())
                return 1
            if args.llm_timeout <= 0:
                report = Report()
                report.error("push --llm-timeout must be greater than zero")
                print(report.format())
                return 1
            if args.project_names and not args.all:
                report = Report()
                report.error("push --project-name requires --all")
                print(report.format())
                return 1
            if args.prune_managed:
                if args.dry_run or args.apply or args.all:
                    report = Report()
                    report.error("push --prune-managed cannot be combined with --dry-run, --apply, or --all")
                    print(report.format())
                    return 1
                if not args.project:
                    parser.error("push --prune-managed requires PROJECT")
                report = command_prune_managed(source_root, Path(args.project).expanduser().resolve())
            elif args.all:
                report = command_push_all(
                    source_root,
                    apply=bool(args.apply),
                    update_docs=bool(args.update_docs),
                    llm_command=args.llm_command,
                    llm_timeout=args.llm_timeout,
                    project_names=set(args.project_names or []),
                )
            elif not args.project:
                parser.error("push requires PROJECT unless --all is used")
            else:
                report = command_push(
                    source_root,
                    Path(args.project).expanduser().resolve(),
                    apply=bool(args.apply),
                )
        elif args.command == "status":
            report = command_status(
                source_root,
                Path(args.project).expanduser().resolve() if args.project else None,
            )
        else:
            parser.error(f"unknown command: {args.command}")

    print(report.format())
    return 0 if report.ok else 1
