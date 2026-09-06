"""构建制品的版本与来源回执；不执行远端发布。"""

import json
import re
import tarfile
import tomllib
import zipfile
from email.parser import Parser
from pathlib import Path

import yaml

from .errors import SyncError
from .hashing import sha256_file

SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


def artifact_names(version: str) -> tuple[str, str]:
    if not SEMVER.fullmatch(version):
        raise SyncError("release version must use MAJOR.MINOR.PATCH")
    return f"agentphilosophy-{version}-py3-none-any.whl", f"agentphilosophy-{version}.tar.gz"


def _runtime_version(text: str) -> str:
    match = re.search(r'^__version__\s*=\s*[\"\']([^\"\']+)', text, re.MULTILINE)
    if not match:
        raise SyncError("runtime version is missing")
    return match[1]


def _content_version(text: str) -> str:
    data = yaml.safe_load(text)
    version = str(data.get("content_version", "")) if isinstance(data, dict) else ""
    if not SEMVER.fullmatch(version):
        raise SyncError("content version is missing or invalid")
    return version


def _metadata(text: str, version: str) -> None:
    data = Parser().parsestr(text)
    if data["Name"] != "agentphilosophy" or data["Version"] != version:
        raise SyncError("package name or version differs from the release")


def validate_archives(dist: Path, version: str, content_version: str) -> None:
    wheel, sdist = artifact_names(version)
    try:
        with zipfile.ZipFile(dist / wheel) as archive:
            names = archive.namelist()
            if len(names) != len(set(names)) or archive.testzip() is not None:
                raise SyncError("wheel contains duplicate or corrupt members")
            _metadata(archive.read(f"agentphilosophy-{version}.dist-info/METADATA").decode(), version)
            runtime = archive.read("agentphilosophy/__init__.py").decode()
            catalog = archive.read("agentphilosophy/default_source/catalog.yaml").decode()
            if _runtime_version(runtime) != version or _content_version(catalog) != content_version:
                raise SyncError("wheel runtime/content version differs from the release")
        with tarfile.open(dist / sdist, "r:gz") as archive:
            names = archive.getnames()
            if len(names) != len(set(names)):
                raise SyncError("sdist contains duplicate members")

            def read(name: str) -> str:
                member = archive.getmember(f"agentphilosophy-{version}/{name}")
                if not member.isfile():
                    raise SyncError(f"sdist metadata is not a regular file: {name}")
                handle = archive.extractfile(member)
                if handle is None:
                    raise SyncError(f"sdist metadata missing: {name}")
                return handle.read().decode()

            _metadata(read("PKG-INFO"), version)
            if tomllib.loads(read("pyproject.toml"))["project"]["version"] != version:
                raise SyncError("sdist project version differs from the release")
            if _runtime_version(read("src/agentphilosophy/__init__.py")) != version:
                raise SyncError("sdist runtime version differs from the release")
            catalogs = ["src/agentphilosophy/default_source/catalog.yaml"]
            if f"agentphilosophy-{version}/catalog.yaml" in names:
                catalogs.append("catalog.yaml")
            for name in catalogs:
                if _content_version(read(name)) != content_version:
                    raise SyncError("sdist content version differs from the release")
    except (OSError, ValueError, KeyError, UnicodeError, zipfile.BadZipFile, tarfile.TarError, yaml.YAMLError) as exc:
        raise SyncError(f"invalid release archive: {exc}") from exc


def create_receipt(source: Path, dist: Path, version: str, revision: str) -> Path:
    names = artifact_names(version)
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise SyncError("source revision must be an immutable commit SHA")
    project_version = tomllib.loads((source / "pyproject.toml").read_text())["project"]["version"]
    runtime_version = _runtime_version((source / "src/agentphilosophy/__init__.py").read_text())
    if project_version != version or runtime_version != version:
        raise SyncError("source version differs from the requested release version")
    content_version = _content_version((source / "catalog.yaml").read_text())
    validate_archives(dist, version, content_version)
    payload = {
        "schema_version": 1,
        "source_revision": revision,
        "agentphilosophy_version": version,
        "content_version": content_version,
        "artifacts": {name: sha256_file(dist / name) for name in names},
    }
    receipt = dist / f"agentphilosophy-{version}.receipt.json"
    receipt.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    return receipt


def verify_receipt(receipt: Path, dist: Path, version: str, revision: str) -> dict:
    try:
        payload = json.loads(receipt.read_text())
        if not isinstance(payload, dict) or payload.get("schema_version") != 1:
            raise SyncError("unsupported release receipt schema")
        if payload.get("source_revision") != revision:
            raise SyncError("release receipt source revision differs from the selected commit")
        if payload.get("agentphilosophy_version") != version:
            raise SyncError("release receipt version differs from the requested release")
        names = artifact_names(version)
        artifacts = payload.get("artifacts")
        if not isinstance(artifacts, dict) or set(artifacts) != set(names):
            raise SyncError("release receipt has an unexpected artifact set")
        for name in names:
            if sha256_file(dist / name) != artifacts[name]:
                raise SyncError(f"release artifact digest differs from the build receipt: {name}")
        validate_archives(dist, version, str(payload.get("content_version", "")))
        return payload
    except (OSError, ValueError, TypeError) as exc:
        raise SyncError(f"invalid release receipt: {exc}") from exc
