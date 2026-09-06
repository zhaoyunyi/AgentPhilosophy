# AgentPhilosophy 发版流程

本文档沉淀 AgentPhilosophy CLI 与中央内容源的发版流程。发版目标不是只打 tag，而是让依赖项目可以通过 `.agents/agentphilosophy-state.yaml` 判断自己是否需要升级 CLI 或同步新内容源。

## 版本口径

AgentPhilosophy 发版分别跟踪以下独立身份：

- `agentphilosophy_version`：CLI release 版本，来自 `pyproject.toml` 与 `src/agentphilosophy/__init__.py`。
- `source_content_version`：中央内容源版本，来自仓库根目录 `catalog.yaml` 与包内 `src/agentphilosophy/default_source/catalog.yaml`。
- module `version`：单个模块版本，来自各 `modules/*/module.yaml`。
- module `upstream.revision`：外部来源 skill 的上游 Git revision，来自各 `modules/*/module.yaml` 的 `upstream` 区块。

默认规则：

- CLI 行为、打包、release gate、状态 schema 或默认内容源发生变化时，发布新的 CLI release。
- 默认内容源发生变化时，同步提升 `content_version`，依赖项目用它判断是否需要重新 `push --dry-run` / `push --apply`。
- 只有单个模块语义发生变化时，也要考虑提升对应 `module.yaml` 的 `version`，让 `status` 能提示具体模块 stale。
- README 的 `uv tool install ...@vX.Y.Z` 只指向已经发布的稳定 tag。`prepare-release.sh` 不提前修改该链接；`main` 上准备中的 CLI 版本可以暂时高于稳定 tag。创建对应 GitHub Release 后，再单独更新 README 的稳定安装命令并提交。

## 本地准备

从干净 `main` 工作区开始：

```bash
jj status
jj bookmark list --all
```

检查外部来源 skill 是否有上游更新：

```bash
uv run python scripts/check-skill-upstreams.py
```

默认检查分别报告跟踪内容变化、ref 漂移和最新正式发布；`--format json` 输出结构化记录，`--refs-only` 只查引用、不能推断最新版本，`--offline` 不联网。`content_changed` 或 `release_available` 才进入采用审阅；`ref_changed` 且跟踪内容未变时不机械升级。先审查 `upstream.tracked_paths`，再更新模板、模块版本、revision、文档和测试。没有计划跟进的上游变化，需要在 release notes 或 change 描述里说明暂不更新的原因。

准备下一个版本，例如 `0.3.2`：

```bash
bash scripts/prepare-release.sh 0.3.2
```

如果 CLI release 版本和内容源版本需要不同步：

```bash
bash scripts/prepare-release.sh 0.3.2 --content-version 0.3.1
```

脚本会完成：

- 更新 `pyproject.toml`、`src/agentphilosophy/__init__.py`。
- 更新仓库内容源与包内默认内容源的 `content_version`。
- 运行 `uv lock`，并通过 `python3 scripts/sync-packaged-source.py --apply` 刷新镜像。
- 运行 `uv run sync.py push . --apply`，刷新本仓 state 中的 `agentphilosophy_version` 与 `source_content_version`。
- 运行 lint、测试、中央源校验、构建和安装后 smoke。
- 根据版本相关 diff、最近提交和模块版本变化生成 `release-notes/v<version>.md`，并更新 [发布说明索引](../release-notes/README.md)，供 GitHub Release 审阅、使用和长期追溯。

## 审查与提交

准备脚本完成后，检查 diff：

```bash
jj diff --summary
jj diff --stat
uv run sync.py status --project .
```

用中文描述当前 change：

```bash
jj describe -m "发布：AgentPhilosophy 0.3.2 更新发版内容"
```

推进并推送 `main`：

```bash
jj bookmark set main -r @
jj git push --bookmark main
```

推送后确认：

```bash
jj status
jj bookmark list --all
```

## 从固定提交构建发布制品

本地 prepare 的构建仅用于验证。发布 change 提交后，从确定的 jj revision 构建：

```bash
uv run --locked python scripts/release-artifacts.py build 0.11.0 --revision main
```

工具解析不可变 commit SHA，通过 `git archive` 建立临时快照，校验镜像与中央源、构建 wheel/sdist，并在中立目录验证安装结果。成功后写入 `dist/agentphilosophy-0.11.0.receipt.json`，绑定源码 SHA、CLI/content 版本和两个制品的 SHA-256。构建或版本检查失败时不会产生成功回执。

## 创建 GitHub Release

确认 `main` 已经推到远端，并且 `dist/` 中已有对应版本的 wheel 与 sdist 后：

```bash
bash scripts/publish-release.sh 0.3.2
```

脚本会检查：

- `dist/agentphilosophy-<version>-py3-none-any.whl` 存在。
- `dist/agentphilosophy-<version>.tar.gz` 和对应 `.receipt.json` 存在；包内版本、实际摘要和回执源码 SHA 与选定 main 一致。
- `v<version>` tag / release 尚未存在。
- 使用 `release-notes/v<version>.md` 作为 release notes；该文件应已随 release change 提交并出现在发布说明索引中。

脚本使用已核对的不可变 SHA 作为发布目标，上传回执；创建后重新读取远端 tag，并下载制品重新核对摘要。回读失败时返回失败，不宣称发布闭环完成。

发布后还可用以下命令确认：

```bash
gh release view v0.3.2 --json tagName,targetCommitish,url,name,isDraft,isPrerelease,assets
git ls-remote --tags origin refs/tags/v0.3.2
```

确认 release 和远端 tag 都存在后，把 README 的 `uv tool install` 版本更新为新 tag，按文档领域单独提交并推送。这样远端主分支不会出现指向尚未发布 tag 的安装命令。

## 依赖项目更新判断

发版后先只读查看 registry 中依赖项目状态：

```bash
uv run sync.py status
```

判断口径：

- `agentphilosophy_version stale: <old> -> <new>`：依赖项目上次同步使用的 CLI release 已落后。
- `source_content_version stale: <old> -> <new>`：依赖项目内容源已落后，需要先 `push --dry-run` 审查更新计划。
- `project config missing`：该项目尚未正式接入 `.agentphilosophy.yaml`，不能判断内容源差异。
- `module version stale: <name>`：具体模块版本落后，优先审查该模块输出影响。

对单个依赖项目更新时，先 dry-run：

```bash
uv run sync.py push /path/to/project --dry-run
```

确认计划合理后再 apply：

```bash
uv run sync.py push /path/to/project --apply
uv run sync.py status --project /path/to/project
```

## Release Notes 审阅

`prepare-release.sh` 会自动生成中文 release notes，不再保留需要手工补写的占位文案。审阅时重点看四块信息：

- `变更摘要`：确认 CLI 版本、内容源版本、比较基准和最近提交摘要是否匹配本次发布。
- `本次 diff 重点`：确认 CLI/脚本、中央内容源、文档和测试范围没有混入无关文件。
- `模块版本变化`：确认 `modules/*/module.yaml` 的 version bump 与模块语义变化一致。
- `依赖项目影响`：确认 stale 提示、dry-run 建议和需要优先审查的模块输出清楚。

如果摘要没有捕捉到发布语义，可以直接编辑 `release-notes/v<version>.md` 后再运行 `publish-release.sh`。不要把发布说明移回 `dist/`；`dist/` 只保存本地构建产物。
