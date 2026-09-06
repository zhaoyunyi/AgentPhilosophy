from pathlib import Path

import pytest
import yaml

from agentphilosophy.cli import main


def seed_module(source: Path, target: Path, output: dict[str, str]) -> Path:
    module = source / "modules" / "probe"
    module.mkdir(parents=True)
    (module / "module.yaml").write_text(yaml.safe_dump({
        "name": "probe", "version": "1.0.0", "outputs": [output],
    }))
    (source / "catalog.yaml").write_text(
        "schema_version: 1\ncontent_version: 0.1.0\nmodules:\n  - name: probe\n"
    )
    target.mkdir()
    (target / ".agentphilosophy.yaml").write_text("project_name: Probe\nmodules: [probe]\n")
    return module


@pytest.mark.parametrize("output_type", ["rendered_file", "fragment"])
@pytest.mark.parametrize("via_symlink", [False, True])
def test_cli_rejects_templates_outside_the_module(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], output_type: str, via_symlink: bool,
) -> None:
    source, target = tmp_path / "source", tmp_path / "target"
    outside = tmp_path / "outside.txt"
    outside.write_text("AUDIT_DUMMY_DATA_ONLY")
    template = "template.md" if via_symlink else "../../../outside.txt"
    module = seed_module(source, target, {
        "id": "probe", "type": output_type, "template": template,
        "target": "AGENTS.md", "section": "probe",
    })
    if via_symlink:
        (module / template).symlink_to(outside)

    assert main(["--source", str(source), "validate"]) == 1
    assert "escapes" in capsys.readouterr().out
    assert main(["--source", str(source), "push", str(target), "--apply"]) == 1
    assert not (target / "AGENTS.md").exists()
    assert not (target / ".agents/agentphilosophy-state.yaml").exists()


@pytest.mark.parametrize("directory_link", [False, True])
def test_cli_rejects_copy_tree_children_linked_outside_the_module(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], directory_link: bool,
) -> None:
    source, target = tmp_path / "source", tmp_path / "target"
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "dummy.md").write_text("AUDIT_DUMMY_DATA_ONLY")
    module = seed_module(source, target, {
        "id": "probe", "type": "copy_tree", "source": "files", "target": "skills/probe",
    })
    (module / "files").mkdir()
    (module / "files/SKILL.md").write_text("# Valid entry\n")
    (module / "files/reference").symlink_to(outside if directory_link else outside / "dummy.md")

    assert main(["--source", str(source), "validate"]) == 1
    message = capsys.readouterr().out
    assert "escapes" in message or "directory symlink" in message
    assert main(["--source", str(source), "push", str(target), "--apply"]) == 1
    assert not (target / "skills").exists()


def test_cli_keeps_valid_references_inside_the_module(tmp_path: Path) -> None:
    source, target = tmp_path / "source", tmp_path / "target"
    module = seed_module(source, target, {
        "id": "probe", "type": "copy_tree", "source": "files", "target": "skills/probe",
    })
    (module / "files").mkdir()
    (module / "reference.md").write_text("Shared module reference\n")
    (module / "files/reference.md").symlink_to(module / "reference.md")

    assert main(["--source", str(source), "push", str(target), "--apply"]) == 0
    assert (target / "skills/probe/reference.md").read_text() == "Shared module reference\n"


def test_template_expressions_cannot_read_arbitrary_local_files(tmp_path: Path, capsys) -> None:
    source, target = tmp_path / "source", tmp_path / "target"
    outside = tmp_path / "outside.txt"
    outside.write_text("DUMMY_NOT_TO_BE_DISCLOSED")
    module = seed_module(source, target, {
        "id": "probe", "type": "rendered_file", "template": "template.md", "target": "AGENTS.md",
    })
    (module / "template.md").write_text(
        "{{ cycler.__init__.__globals__.__builtins__.open(" + repr(str(outside)) + ").read() }}"
    )
    assert main(["--source", str(source), "push", str(target), "--apply"]) == 1
    assert "DUMMY_NOT_TO_BE_DISCLOSED" not in capsys.readouterr().out
    assert not (target / "AGENTS.md").exists()


def test_copy_file_rejects_a_directory_without_writing(tmp_path: Path) -> None:
    source, target = tmp_path / "source", tmp_path / "target"
    module = seed_module(source, target, {
        "id": "probe", "type": "copy_file", "source": "directory", "target": "AGENTS.md",
    })
    (module / "directory").mkdir()
    assert main(["--source", str(source), "validate"]) == 1
    assert main(["--source", str(source), "push", str(target), "--apply"]) == 1
    assert not (target / "AGENTS.md").exists()


def test_external_module_manifest_cannot_leak_into_conflict_candidates(tmp_path: Path) -> None:
    source, target = tmp_path / "source", tmp_path / "target"
    module = seed_module(source, target, {
        "id": "probe", "type": "rendered_file", "template": "template.md", "target": "AGENTS.md",
    })
    (module / "template.md").write_text("{{ dummy }}")
    manifest = module / "module.yaml"
    data = yaml.safe_load(manifest.read_text())
    data["default_vars"] = {"dummy": "DUMMY_NOT_TO_BE_DISCLOSED"}
    outside = tmp_path / "outside.yaml"
    outside.write_text(yaml.safe_dump(data))
    manifest.unlink()
    manifest.symlink_to(outside)
    (target / "AGENTS.md").write_text("User content\n")
    state = target / ".agents/agentphilosophy-state.yaml"
    state.parent.mkdir()
    state.write_text("schema_version: 1\nfiles: []\n")
    assert main(["--source", str(source), "push", str(target), "--apply"]) == 1
    assert (target / "AGENTS.md").read_text() == "User content\n"
    assert not (target / ".agents/migration").exists()


@pytest.mark.parametrize("kind,field", [("copy_file", "source"), ("rendered_file", "template")])
def test_outputs_cannot_reference_files_excluded_from_content_identity(tmp_path: Path, kind: str, field: str) -> None:
    source, target = tmp_path / "source", tmp_path / "target"
    module = seed_module(source, target, {
        "id": "probe", "type": kind, field: "payload.pyc", "target": "AGENTS.md",
    })
    (module / "payload.pyc").write_text("ignored cache")
    assert main(["--source", str(source), "validate"]) == 1
    assert main(["--source", str(source), "push", str(target), "--apply"]) == 1
    assert not (target / "AGENTS.md").exists()
