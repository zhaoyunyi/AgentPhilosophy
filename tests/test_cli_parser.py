from __future__ import annotations

from agentphilosophy.cli import build_parser


def test_cli_parser_uses_explicit_program_name() -> None:
    parser = build_parser(prog="agentphilosophy-sync")

    assert parser.prog == "agentphilosophy-sync"
