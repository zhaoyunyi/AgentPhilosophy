import re
from pathlib import Path

import pytest
import yaml


@pytest.fixture
def validate_skill_contract():
    """在干净 CI 环境中验证技能元数据，不依赖维护者的个人 Codex 安装。"""
    def validate(folder: Path, name: str) -> None:
        text = (folder / "SKILL.md").read_text(encoding="utf-8")
        assert text.startswith("---\n")
        metadata = yaml.safe_load(text.split("---", 2)[1])
        assert isinstance(metadata, dict)
        assert metadata["name"] == name
        assert len(name) <= 64 and re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name)
        description = metadata["description"]
        assert isinstance(description, str) and 0 < len(description.strip()) <= 1024
        assert "<" not in description and ">" not in description
    return validate
