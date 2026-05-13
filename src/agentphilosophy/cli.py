from __future__ import annotations

import argparse
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
from .errors import Report
from .resources import llm_usage_path, resolve_source_root


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

    subparsers.add_parser("llm-usage", help="Print the LLM usage document for the selected source.")

    status = subparsers.add_parser("status", help="Show registry or project status.")
    status.add_argument("--project")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser(prog=Path(sys.argv[0]).name)
    args = parser.parse_args(argv)

    with resolve_source_root(args.source) as source_root:
        if args.command == "llm-usage":
            path = llm_usage_path(source_root)
            if not path.is_file():
                report = Report()
                report.error(f"LLM usage document not found: {path}")
                print(report.format())
                return 1
            print(path.read_text(encoding="utf-8"), end="")
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
                report = command_push_all(source_root, apply=bool(args.apply))
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
