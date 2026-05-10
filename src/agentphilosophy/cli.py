from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from .commands import (
    command_adopt,
    command_init,
    command_migrate,
    command_pull,
    command_push,
    command_push_all,
    command_status,
    command_validate,
)
from .errors import Report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sync.py")
    parser.add_argument(
        "--source",
        default=".",
        help="AgentPhilosophy central source root. Defaults to current directory.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="Validate central source or target project.")
    validate.add_argument("project", nargs="?")

    init = subparsers.add_parser("init", help="Create a project configuration draft.")
    init.add_argument("project")
    init.add_argument("--preset")
    init.add_argument("--interactive", action="store_true")

    migrate = subparsers.add_parser("migrate", help="Generate report-only migration artifacts.")
    migrate.add_argument("project")

    adopt = subparsers.add_parser("adopt", help="Adopt existing files into managed state.")
    adopt.add_argument("project")
    adopt.add_argument("--file")
    adopt.add_argument("--module")
    adopt.add_argument("--output")
    adopt.add_argument("--from-report")

    push = subparsers.add_parser("push", help="Render and sync managed outputs.")
    push.add_argument("project", nargs="?")
    push.add_argument("--all", action="store_true")
    mode = push.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    push.add_argument("--prune-managed", action="store_true")

    subparsers.add_parser("pull", help="Reserved first-version command skeleton.")

    status = subparsers.add_parser("status", help="Show registry or project status.")
    status.add_argument("--project")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    source_root = Path(args.source).expanduser().resolve()

    if args.command == "validate":
        report = command_validate(
            source_root,
            Path(args.project).expanduser().resolve() if args.project else None,
        )
    elif args.command == "init":
        if args.interactive:
            report = Report()
            report.error("init --interactive is not implemented in the first version")
        else:
            report = command_init(source_root, Path(args.project).expanduser().resolve(), args.preset)
    elif args.command == "migrate":
        report = command_migrate(source_root, Path(args.project).expanduser().resolve())
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
            report = Report()
            report.error("push --prune-managed is not implemented in the first version")
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
    elif args.command == "pull":
        report = command_pull()
    elif args.command == "status":
        report = command_status(
            source_root,
            Path(args.project).expanduser().resolve() if args.project else None,
        )
    else:
        parser.error(f"unknown command: {args.command}")

    print(report.format())
    return 0 if report.ok else 1
