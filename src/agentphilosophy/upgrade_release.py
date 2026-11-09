"""公开稳定 Release 的发现与不可变升级目标；不安装工具或写入目标项目。"""

from __future__ import annotations

import http.client
import io
import json
import re
import stat
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath

from . import __version__
from .errors import SyncError
from .hashing import sha256_bytes, source_tree_hash
from .release import artifact_names
from .source import source_content_version
from .yamlio import read_yaml

REPOSITORY = "https://github.com/zhaoyunyi/AgentPhilosophy"
API = "https://api.github.com/repos/zhaoyunyi/AgentPhilosophy"
SEMVER = re.compile(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)")
SHA = re.compile(r"[0-9a-f]{40}")
DIGEST = re.compile(r"sha256:[0-9a-f]{64}")
MAX_DOWNLOAD = 64 * 1024 * 1024
MIN_UPGRADE_VERSION = (1, 3, 0)


def version_tuple(value: str) -> tuple[int, ...]:
    if not isinstance(value, str) or not SEMVER.fullmatch(value):
        raise SyncError(f"无法判断兼容性：版本必须为 MAJOR.MINOR.PATCH：{value}")
    return tuple(int(part) for part in value.split("."))


def fetch(url: str, limit: int = MAX_DOWNLOAD) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "AgentPhilosophy", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = response.read(limit + 1)
    except (OSError, urllib.error.URLError, http.client.HTTPException) as exc:
        raise SyncError(f"无法读取正式发布信息，更新状态未知：{exc}") from exc
    if len(data) > limit:
        raise SyncError("发布响应超过允许大小")
    return data


def fetch_json(url: str) -> dict:
    try:
        data = json.loads(fetch(url, 2 * 1024 * 1024))
        if not isinstance(data, dict):
            raise ValueError("expected object")
        return data
    except (ValueError, UnicodeError) as exc:
        raise SyncError("发布响应不是有效 JSON 对象") from exc


def wheel_identity(data: bytes, version: str) -> tuple[str, str]:
    """不执行 wheel；校验包身份并用同步器相同的清单计算内容源指纹。"""
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive, tempfile.TemporaryDirectory() as temporary:
            names = archive.namelist()
            if len(names) != len(set(names)) or sum(item.file_size for item in archive.infolist()) > MAX_DOWNLOAD:
                raise SyncError("wheel 包含重复文件或解压大小超限")
            metadata = archive.read(f"agentphilosophy-{version}.dist-info/METADATA").decode()
            from email.parser import Parser

            headers = Parser().parsestr(metadata)
            runtime = archive.read("agentphilosophy/__init__.py").decode()
            if (headers["Name"] != "agentphilosophy" or headers["Version"] != version
                    or not re.search(rf'^__version__\s*=\s*[\"\']{re.escape(version)}[\"\']', runtime, re.M)):
                raise SyncError("wheel 版本与 Release 不一致")
            root = Path(temporary)
            prefix = "agentphilosophy/default_source/"
            for item in archive.infolist():
                if not item.filename.startswith(prefix) or item.is_dir():
                    continue
                rel = item.filename.removeprefix(prefix)
                path = PurePosixPath(rel)
                if (path.is_absolute() or ".." in path.parts or "\\" in rel
                        or str(path) != rel or stat.S_ISLNK(item.external_attr >> 16)):
                    raise SyncError("wheel 内容路径不安全")
                destination = root / rel
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(archive.read(item))
            content_version = source_content_version(root)
            version_tuple(content_version)
            return content_version, source_tree_hash(root)
    except (OSError, ValueError, KeyError, zipfile.BadZipFile, UnicodeError) as exc:
        raise SyncError(f"无效发布 wheel：{exc}") from exc


def discover_release(version: str | None = None) -> dict:
    if version:
        version = version.removeprefix("v")
        version_tuple(version)
    release = fetch_json(f"{API}/releases/" + (f"tags/v{version}" if version else "latest"))
    tag = str(release.get("tag_name", ""))
    selected = tag.removeprefix("v")
    version_tuple(selected)
    if (tag != f"v{selected}" or release.get("draft") is not False
            or release.get("prerelease") is not False or (version and version != selected)):
        raise SyncError("目标必须为指定仓库的正式稳定 Release")
    wheel_name, _ = artifact_names(selected)
    receipt_name = f"agentphilosophy-{selected}.receipt.json"
    assets = release.get("assets")
    if not isinstance(assets, list):
        raise SyncError("Release 缺少制品清单")
    urls = {}
    for name in (wheel_name, receipt_name):
        expected = f"{REPOSITORY}/releases/download/{tag}/{name}"
        matches = [item for item in assets if isinstance(item, dict) and item.get("name") == name]
        if len(matches) != 1 or matches[0].get("browser_download_url") != expected:
            raise SyncError(f"Release 缺少唯一的官方制品：{name}")
        urls[name] = expected
    receipt = fetch_json(urls[receipt_name])
    revision = receipt.get("source_revision", "")
    if (receipt.get("schema_version") != 1 or receipt.get("agentphilosophy_version") != selected
            or not isinstance(revision, str) or not SHA.fullmatch(revision)):
        raise SyncError("发布回执的版本或源码身份不正确")
    ref = fetch_json(f"{API}/git/ref/tags/{tag}").get("object", {})
    for _ in range(5):
        if not isinstance(ref, dict) or not SHA.fullmatch(str(ref.get("sha", ""))):
            raise SyncError("无法解析发布 tag 的源码提交")
        if ref.get("type") == "commit":
            break
        if ref.get("type") != "tag":
            raise SyncError("发布 tag 未指向源码提交")
        ref = fetch_json(f"{API}/git/tags/{ref['sha']}").get("object", {})
    if ref.get("type") != "commit" or ref.get("sha") != revision:
        raise SyncError("发布 tag 与回执源码身份不一致")
    artifacts = receipt.get("artifacts")
    digest = artifacts.get(wheel_name) if isinstance(artifacts, dict) else None
    if not isinstance(digest, str) or not DIGEST.fullmatch(digest):
        raise SyncError("发布回执缺少 wheel SHA-256")
    wheel = fetch(urls[wheel_name])
    if sha256_bytes(wheel) != digest:
        raise SyncError("下载 wheel 的摘要与发布回执不一致")
    content_version, content_hash = wheel_identity(wheel, selected)
    if content_version != receipt.get("content_version"):
        raise SyncError("wheel 内容版本与发布回执不一致")
    return {
        "version": selected, "tag": tag, "source_revision": revision,
        "content_version": content_version, "source_tree_hash": content_hash,
        "wheel_sha256": digest, "release_url": f"{REPOSITORY}/releases/tag/{tag}",
    }


def check_update(project: Path | None = None, version: str | None = None) -> dict:
    target = discover_release(version)
    current = __version__
    project_version = None
    if project is not None:
        state_file = project / ".agents/agentphilosophy-state.yaml"
        if not state_file.is_file():
            raise SyncError("项目尚未接入：缺少同步 state，请先按接入流程操作")
        project_version = str(read_yaml(state_file).get("agentphilosophy_version", ""))
        version_tuple(project_version)
        current = project_version
    comparison = (version_tuple(target["version"]) > version_tuple(current)) - (
        version_tuple(target["version"]) < version_tuple(current)
    )
    return {
        "format_version": 1,
        "status": {1: "update_available", 0: "current", -1: "local_newer"}[comparison],
        "installed_version": __version__, "project_version": project_version,
        "workflow_supported": version_tuple(target["version"]) >= MIN_UPGRADE_VERSION,
        "target": target,
        "install_command": ["uv", "tool", "install", "--force", f"git+{REPOSITORY}.git@{target['source_revision']}"],
    }
