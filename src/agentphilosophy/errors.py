from __future__ import annotations

from dataclasses import dataclass, field


class SyncError(Exception):
    """Raised for expected user-facing sync errors."""


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    infos: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def info(self, message: str) -> None:
        self.infos.append(message)

    def extend(self, other: Report) -> None:
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        self.infos.extend(other.infos)

    def format(self) -> str:
        lines: list[str] = []
        lines.extend(f"[error] {message}" for message in self.errors)
        lines.extend(f"[warning] {message}" for message in self.warnings)
        lines.extend(f"[info] {message}" for message in self.infos)
        if not lines:
            lines.append("[ok] no issues found")
        return "\n".join(lines)
