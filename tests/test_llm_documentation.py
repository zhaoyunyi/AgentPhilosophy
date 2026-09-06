from pathlib import Path

from agentphilosophy.cli import main


def test_full_llm_usage_assembles_task_pages_in_order(tmp_path: Path, capsys) -> None:
    docs = tmp_path / "docs"
    (docs / "cli").mkdir(parents=True)
    (docs / "cli-usage-for-llm.md").write_text(
        "# Entry\n<!-- include: cli/runtime.md -->\n<!-- include: cli/safety.md -->\n"
    )
    (docs / "cli/runtime.md").write_text("# Runtime\nUse the selected project environment.\n")
    (docs / "cli/safety.md").write_text("# Safety\nPreview before apply.\n")
    assert main(["--source", str(tmp_path), "llm-usage"]) == 0
    output = capsys.readouterr().out
    assert output.index("# Runtime") < output.index("# Safety")
    assert "Preview before apply." in output


def test_llm_usage_refuses_a_missing_or_external_include(tmp_path: Path, capsys) -> None:
    docs = tmp_path / "docs"
    (docs / "cli").mkdir(parents=True)
    (tmp_path / "outside.md").write_text("DUMMY_NOT_TO_BE_DISCLOSED")
    entry = docs / "cli-usage-for-llm.md"
    for included in ("cli/missing.md", "cli/../../outside.md"):
        entry.write_text(f"# Entry\n<!-- include: {included} -->\n")
        assert main(["--source", str(tmp_path), "llm-usage"]) == 1
        assert "DUMMY_NOT_TO_BE_DISCLOSED" not in capsys.readouterr().out
