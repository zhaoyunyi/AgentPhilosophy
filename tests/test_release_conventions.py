from __future__ import annotations

from pathlib import Path

from agentphilosophy.yamlio import read_yaml

ROOT = Path(__file__).resolve().parents[1]
MODULE_NAME = "release-conventions"


def test_release_conventions_module_is_available_in_all_default_presets() -> None:
    module = read_yaml(ROOT / "modules" / MODULE_NAME / "module.yaml")
    assert module["name"] == MODULE_NAME
    assert module["version"] == "1.1.0"
    assert module["requires"] == ["doc-templates"]
    assert {output["target"] for output in module["outputs"]} == {
        "AGENTS.md",
        "release-notes/README.md",
    }

    catalog = read_yaml(ROOT / "catalog.yaml")
    assert MODULE_NAME in {item["name"] for item in catalog["modules"]}

    root_config = read_yaml(ROOT / ".agentphilosophy.yaml")
    assert MODULE_NAME in root_config["modules"]
    for preset_name in ("orchestrator", "fullstack", "frontend", "mobile-sdk"):
        preset = read_yaml(ROOT / "presets" / f"{preset_name}.yaml")
        assert MODULE_NAME in preset["modules"]


def test_release_conventions_define_semver_notes_and_publication_receipts() -> None:
    module_root = ROOT / "modules" / MODULE_NAME
    rules = (module_root / "templates" / "release-rules.md.j2").read_text(encoding="utf-8")
    index = (module_root / "templates" / "release-notes-README.md.j2").read_text(encoding="utf-8")

    assert "MAJOR.MINOR.PATCH" in rules
    assert "release-notes/v<MAJOR>.<MINOR>.<PATCH>.md" in rules
    assert "发布回执" in rules
    assert "不能称为已发布" in rules
    assert ".agents/custom/release-notes/README.custom.md" in index
    assert "兼容性与迁移" in index
    assert "验证与发布回执" in index
