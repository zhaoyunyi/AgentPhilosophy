from __future__ import annotations

import pytest

from agentphilosophy import __version__
from agentphilosophy.cli import build_parser, main


def test_cli_parser_uses_explicit_program_name() -> None:
    parser = build_parser(prog="agentphilosophy-sync")

    assert parser.prog == "agentphilosophy-sync"


def test_pull_is_not_exposed_as_a_cli_command(capsys) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["pull"])

    assert exc.value.code == 2
    assert "invalid choice" in capsys.readouterr().err


def test_cli_version_reports_installed_agentphilosophy_version(capsys) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--version"])

    assert exc.value.code == 0
    assert __version__ in capsys.readouterr().out


@pytest.mark.parametrize(
    ("argv", "message"),
    [
        (["push", "--all", "--update-docs", "--llm-command", "model -"], "requires --all --apply"),
        (["push", "--all", "--apply", "--update-docs"], "requires --llm-command"),
        (["push", "--all", "--apply", "--llm-command", "model -"], "requires --update-docs"),
        (
            [
                "push",
                "--all",
                "--apply",
                "--update-docs",
                "--llm-command",
                "model -",
                "--llm-timeout",
                "0",
            ],
            "must be greater than zero",
        ),
        (["push", "/tmp/project", "--project-name", "demo"], "requires --all"),
    ],
)
def test_push_documentation_flags_require_safe_batch_apply_combinations(
    argv: list[str],
    message: str,
    capsys,
) -> None:
    assert main(argv) == 1
    assert message in capsys.readouterr().out
