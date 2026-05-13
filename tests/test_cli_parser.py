from __future__ import annotations

import pytest

from agentphilosophy.cli import build_parser, main


def test_cli_parser_uses_explicit_program_name() -> None:
    parser = build_parser(prog="agentphilosophy-sync")

    assert parser.prog == "agentphilosophy-sync"


def test_pull_is_not_exposed_as_a_cli_command(capsys) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["pull"])

    assert exc.value.code == 2
    assert "invalid choice" in capsys.readouterr().err
