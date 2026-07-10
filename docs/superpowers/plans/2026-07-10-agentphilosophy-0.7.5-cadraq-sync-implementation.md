# AgentPhilosophy 0.7.5 与 cadraq 同步 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 发布包含当前模板升级和可配置验证指南入口的 AgentPhilosophy `0.7.5`，再将 cadraq 无漂移同步到该版本及默认 preset skill 输出。

**Architecture:** AgentPhilosophy 根目录模块是开发事实源，`src/agentphilosophy/default_source/` 是发布包镜像；所有模板能力必须在两处保持一致并由 packaged-source e2e 覆盖。cadraq 只在 `.agentphilosophy.yaml` 声明项目变量，其他规范与 skill 输出由同步器生成，避免直接修改托管 state 或生成物。

**Tech Stack:** Python 3.12、Jinja2、PyYAML、pytest、ruff、uv、Jujutsu、pnpm、Vitest、OpenSpec、GitHub CLI。

## Global Constraints

- AgentPhilosophy CLI version 与 content version 统一发布为 `0.7.5`。
- cadraq 保持 `preset: orchestrator` 和 `source: /Users/zhaoyunyi/developer/AgentPhilosophy`。
- 不新增 `skill-philosophy-extraction` 或独立 `skill-code-review` 等可选模块。
- 不手工编辑任何 `.agents/agentphilosophy-state.yaml`。
- 中央仓发布前必须通过 ruff、全量 pytest、central validate、build 和 installed-wheel smoke。
- cadraq 同步顺序固定为 central validate、target validate、dry-run、apply、status。
- cadraq 的 `spec/TestStrategy.md` 必须保留 `docs/guides/verification-boundaries.md` 入口且不再产生托管冲突。
- AgentPhilosophy 使用 `jj` 中文 change；中央 Release 必须推送 `main` 后再发布。
- cadraq 本轮只形成已验证的本地 change，不推送远端。

---

## 文件结构

### AgentPhilosophy

- `modules/spec-test-general/templates/TestStrategy.md.j2`：定义测试策略及可选验证指南章节。
- `modules/spec-test-general/module.yaml`：记录模块版本 `1.1.0`。
- `src/agentphilosophy/default_source/modules/spec-test-general/`：发布包内同内容镜像。
- `tests/e2e/test_sync_cli.py`：覆盖默认不渲染、配置后渲染以及既有同内容文件无冲突接管。
- `pyproject.toml`、`src/agentphilosophy/__init__.py`、`catalog.yaml`、packaged catalog、`README.md`、`uv.lock`：由发版脚本统一更新到 `0.7.5`。

### cadraq

- `.agentphilosophy.yaml`：声明 `verification_guide_path`。
- `spec/TestStrategy.md`：同步后应与当前内容一致，但 state 更新为新模板事实。
- `skills/`、`.codex/skills/`、`AGENTS.md`、`spec/DDDSpec.md`、`spec/ProductCopySpec.md`：由 AgentPhilosophy 生成最新输出。
- `.agents/agentphilosophy-state.yaml`：只由 `push --apply` 更新到 `0.7.5`。

---

### Task 1: 为测试策略增加可配置验证指南入口

**Files:**
- Modify: `tests/e2e/test_sync_cli.py`
- Modify: `modules/spec-test-general/templates/TestStrategy.md.j2`
- Modify: `modules/spec-test-general/module.yaml`
- Modify: `src/agentphilosophy/default_source/modules/spec-test-general/templates/TestStrategy.md.j2`
- Modify: `src/agentphilosophy/default_source/modules/spec-test-general/module.yaml`

**Interfaces:**
- Consumes: `.agentphilosophy.yaml` 的 `vars.verification_guide_path: str | undefined`。
- Produces: `spec/TestStrategy.md` 中可选的“验证边界”章节；未配置变量时输出保持原样。

- [ ] **Step 1: 写入 packaged-source 失败测试**

在 `tests/e2e/test_sync_cli.py` 增加以下测试。测试先生成默认文件，再模拟 cadraq 已经手工补上与新模板完全相同的内容，最后配置变量并验证同步器把它识别为 `already up to date`，而不是托管冲突。

```python
def test_packaged_orchestrator_adopts_matching_verification_guide_output(tmp_path: Path) -> None:
    target = tmp_path / "target"
    workdir = tmp_path / "workdir"
    workdir.mkdir()
    sync_py = str(Path(__file__).resolve().parents[2] / "sync.py")

    for args in (["init", str(target), "--preset", "orchestrator"], ["push", str(target), "--apply"]):
        result = subprocess.run(
            [sys.executable, sync_py, *args],
            cwd=workdir,
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr + result.stdout

    strategy_path = target / "spec" / "TestStrategy.md"
    baseline = strategy_path.read_text(encoding="utf-8")
    assert "## 验证边界" not in baseline
    strategy_path.write_text(
        baseline
        + "\n## 验证边界\n\n"
        + "具体到 change class 的必跑命令、smoke 选择、未覆盖边界记录和禁止事项见 "
        + "`docs/guides/verification-boundaries.md`。完成前必须使用当前命令输出作为证据，"
        + "不能用旧日志或推测替代。\n",
        encoding="utf-8",
    )

    config_path = target / ".agentphilosophy.yaml"
    config_text = config_path.read_text(encoding="utf-8")
    marker = "  primary_tool: Codex CLI\n"
    assert config_text.count(marker) == 1
    config_path.write_text(
        config_text.replace(
            marker,
            marker + "  verification_guide_path: docs/guides/verification-boundaries.md\n",
        ),
        encoding="utf-8",
    )

    apply_result = subprocess.run(
        [sys.executable, sync_py, "push", str(target), "--apply"],
        cwd=workdir,
        text=True,
        capture_output=True,
        check=False,
    )
    assert apply_result.returncode == 0, apply_result.stderr + apply_result.stdout
    assert "skip: spec/TestStrategy.md (already up to date)" in apply_result.stdout
    assert "conflict: spec/TestStrategy.md" not in apply_result.stdout

    second_dry_run = subprocess.run(
        [sys.executable, sync_py, "push", str(target), "--dry-run"],
        cwd=workdir,
        text=True,
        capture_output=True,
        check=False,
    )
    assert second_dry_run.returncode == 0, second_dry_run.stderr + second_dry_run.stdout
    assert "conflict: spec/TestStrategy.md" not in second_dry_run.stdout
```

- [ ] **Step 2: 运行测试并确认红灯原因**

Run:

```bash
uv run pytest -q tests/e2e/test_sync_cli.py::test_packaged_orchestrator_adopts_matching_verification_guide_output
```

Expected: FAIL；当前模板不会渲染“验证边界”章节，因此 apply 输出包含 `conflict: spec/TestStrategy.md`。

- [ ] **Step 3: 实现最小 Jinja 扩展**

把根目录与 packaged source 的 `TestStrategy.md.j2` 同步修改为：

```jinja2
# 测试策略

## 分层

- 单元测试：覆盖纯逻辑、路径安全、hash/state 和边界条件。
- BDD 测试：覆盖用户可观察流程。
- e2e 测试：覆盖 CLI 或真实运行入口的完整链路。

## 默认命令

`{{ test_command | default("pytest -q") }}`
{% set verification_guide = verification_guide_path | default("", true) %}
{% if verification_guide %}

## 验证边界

具体到 change class 的必跑命令、smoke 选择、未覆盖边界记录和禁止事项见 `{{ verification_guide }}`。完成前必须使用当前命令输出作为证据，不能用旧日志或推测替代。
{% endif %}
```

把两份 `modules/spec-test-general/module.yaml` 的版本从 `1.0.0` 提升为：

```yaml
version: 1.1.0
```

- [ ] **Step 4: 运行 focused 测试并确认绿灯**

Run:

```bash
uv run pytest -q tests/e2e/test_sync_cli.py::test_packaged_orchestrator_adopts_matching_verification_guide_output
```

Expected: `1 passed`，apply 和第二次 dry-run 均无 `spec/TestStrategy.md` conflict。

- [ ] **Step 5: 验证中央与 packaged source 一致**

Run:

```bash
uv run pytest -q tests/test_packaged_source.py tests/e2e/test_sync_cli.py
uv run ruff check .
uv run sync.py validate
```

Expected: 全部通过，`validate` 输出 `[ok] no issues found`。

- [ ] **Step 6: 形成独立中文 jj change**

Run:

```bash
jj describe -m "规范：支持项目验证指南无漂移接入"
jj new
```

Expected: 新工作副本为空，父 change 描述为 `规范：支持项目验证指南无漂移接入`。

---

### Task 2: 准备并验证 AgentPhilosophy 0.7.5

**Files:**
- Modify: `pyproject.toml`
- Modify: `src/agentphilosophy/__init__.py`
- Modify: `README.md`
- Modify: `catalog.yaml`
- Modify: `src/agentphilosophy/default_source/catalog.yaml`
- Modify: `uv.lock`
- Generated: `.agents/agentphilosophy-state.yaml`
- Generated: `dist/agentphilosophy-0.7.5-py3-none-any.whl`
- Generated: `dist/agentphilosophy-0.7.5.tar.gz`
- Generated: `dist/release-notes-v0.7.5.md`

**Interfaces:**
- Consumes: 已通过测试的中央 change stack，以及 `scripts/prepare-release.sh VERSION`。
- Produces: CLI/content `0.7.5` 构建产物和无占位 release notes。

- [ ] **Step 1: 确认发版起点干净且版本未占用**

Run:

```bash
jj status
gh release view v0.7.5
```

Expected: `jj status` 报告无变更；`gh release view` 返回 release 不存在。若 release 已存在，停止并重新判断版本，不覆盖既有发布。

- [ ] **Step 2: 运行仓库原生发版准备脚本**

Run:

```bash
bash scripts/prepare-release.sh 0.7.5
```

Expected: 脚本完成版本更新、state 刷新、ruff、全量 pytest、central validate、build 和 installed-wheel smoke，最后输出 `Prepared AgentPhilosophy release v0.7.5 with content_version 0.7.5.`。

- [ ] **Step 3: 审查版本面与 release notes**

Run:

```bash
rg -n '0\.7\.5|content_version: 0\.7\.5|version: 1\.1\.0' \
  pyproject.toml src/agentphilosophy/__init__.py README.md catalog.yaml \
  src/agentphilosophy/default_source/catalog.yaml modules/spec-test-general/module.yaml \
  src/agentphilosophy/default_source/modules/spec-test-general/module.yaml uv.lock
sed -n '1,240p' dist/release-notes-v0.7.5.md
rg -n 'T[B]D|T[O]DO|待[补]充' dist/release-notes-v0.7.5.md
```

Expected: 所有 release/version 面一致为 `0.7.5`，模块版本为 `1.1.0`；release notes 无占位词，最后一个 `rg` 无输出。

- [ ] **Step 4: 形成 release change 并回到干净子 change**

Run:

```bash
jj describe -m "发布：AgentPhilosophy 0.7.5 升级默认模板"
jj new
jj status
```

Expected: 工作副本无变更，父 change 是完整 release change。

---

### Task 3: 推送并发布 AgentPhilosophy v0.7.5

**Files:**
- No source file changes.

**Interfaces:**
- Consumes: Task 2 的干净 release change 与 dist artifacts。
- Produces: 远端 `main`、Git tag `v0.7.5`、GitHub Release 及 wheel/sdist assets。

- [ ] **Step 1: 把 main bookmark 移到 release change**

Run:

```bash
jj bookmark set main -r @-
jj log -r 'main|main@origin|@-' --no-graph -T 'bookmarks ++ " " ++ commit_id.short() ++ " " ++ description.first_line() ++ "\n"'
```

Expected: `main` 指向 `发布：AgentPhilosophy 0.7.5 升级默认模板`，`main@origin` 仍指向旧版本。

- [ ] **Step 2: 推送 main 并复核远端**

Run:

```bash
jj git push --bookmark main
jj git fetch
jj log -r 'main|main@origin' --no-graph -T 'bookmarks ++ " " ++ commit_id ++ "\n"'
```

Expected: `main` 与 `main@origin` commit id 完全一致。

- [ ] **Step 3: 创建 GitHub Release**

Run:

```bash
bash scripts/publish-release.sh 0.7.5
```

Expected: 输出 GitHub Release JSON，`tagName` 为 `v0.7.5`，包含 wheel 与 sdist assets，远端 tag 可查询。

- [ ] **Step 4: 做发布后只读复核**

Run:

```bash
gh release view v0.7.5 --json tagName,targetCommitish,url,name,isDraft,isPrerelease,assets
git ls-remote origin refs/heads/main refs/tags/v0.7.5
jj status
```

Expected: Release 非 draft、非 prerelease，target 为 `main`；main 与 tag 均存在；工作副本干净。

---

### Task 4: 将 cadraq 同步到 AgentPhilosophy 0.7.5

**Files:**
- Modify: `/Users/zhaoyunyi/developer/cadraq/.agentphilosophy.yaml`
- Generated: `/Users/zhaoyunyi/developer/cadraq/.agents/agentphilosophy-state.yaml`
- Generated: `/Users/zhaoyunyi/developer/cadraq/AGENTS.md`
- Generated: `/Users/zhaoyunyi/developer/cadraq/spec/DDDSpec.md`
- Generated: `/Users/zhaoyunyi/developer/cadraq/spec/ProductCopySpec.md`
- Generated: `/Users/zhaoyunyi/developer/cadraq/skills/**`
- Generated: `/Users/zhaoyunyi/developer/cadraq/.codex/skills/**`

**Interfaces:**
- Consumes: AgentPhilosophy `v0.7.5` 中央源与 `vars.verification_guide_path`。
- Produces: cadraq `0.7.5` state、最新默认 preset 输出、无冲突的 `spec/TestStrategy.md`。

- [ ] **Step 1: 在 cadraq 配置声明验证指南路径**

在 `.agentphilosophy.yaml` 的 `vars` 中加入：

```yaml
vars:
  primary_tool: Codex CLI
  test_command: openspec validate --all --strict
  verification_guide_path: docs/guides/verification-boundaries.md
```

保留现有 `extra_model_rules` 不变。

- [ ] **Step 2: 重新运行中央与目标校验**

Run from `/Users/zhaoyunyi/developer/AgentPhilosophy`:

```bash
uv run sync.py validate
uv run sync.py validate /Users/zhaoyunyi/developer/cadraq
```

Expected: 两条命令均输出 `[ok] no issues found`。

- [ ] **Step 3: 审查 dry-run**

Run:

```bash
uv run sync.py push /Users/zhaoyunyi/developer/cadraq --dry-run
```

Expected:

- `spec/TestStrategy.md` 为 `skip: ... (already up to date)`，没有 conflict。
- 新增 repo/Codex 双路径的 `to-spec` 与 `to-tickets`。
- 更新 Portless、Matt Pocock 流程、DDD、产品文案和 AGENTS 输出。
- 无新的 unmanaged 或 manually changed conflict。

- [ ] **Step 4: 应用同步并检查 status**

Run:

```bash
uv run sync.py push /Users/zhaoyunyi/developer/cadraq --apply
uv run sync.py status --project /Users/zhaoyunyi/developer/cadraq
```

Expected: apply 无 error；status 无 stale、drift 或 conflict，state 记录 CLI/content `0.7.5`。

- [ ] **Step 5: 验证 skill discovery 与关键内容**

Run from `/Users/zhaoyunyi/developer/cadraq`:

```bash
find -L .codex/skills -name SKILL.md -print | sort
test -f skills/to-spec/SKILL.md
test -f .codex/skills/to-spec/SKILL.md
test -f skills/to-tickets/SKILL.md
test -f .codex/skills/to-tickets/SKILL.md
cmp -s skills/to-spec/SKILL.md .codex/skills/to-spec/SKILL.md
cmp -s skills/to-tickets/SKILL.md .codex/skills/to-tickets/SKILL.md
rg -n 'agentphilosophy_version: 0\.7\.5|source_content_version: 0\.7\.5' .agents/agentphilosophy-state.yaml
rg -n 'docs/guides/verification-boundaries\.md' spec/TestStrategy.md
```

Expected: 两套 skill 均存在且内容一致；state 与验证指南入口匹配。

---

### Task 5: 验证并收口 cadraq 本地 change

**Files:**
- Verify all files changed by Task 4.

**Interfaces:**
- Consumes: Task 4 的完整生成 diff。
- Produces: 一个已验证、可审查且未推送的 cadraq 中文 jj change。

- [ ] **Step 1: 审查目标仓 diff 边界**

Run from `/Users/zhaoyunyi/developer/cadraq`:

```bash
jj status
jj diff --stat
jj diff --summary
```

Expected: 变更仅包含 `.agentphilosophy.yaml`、state、中央托管规范和 repo/Codex skill；没有业务代码、部署文件或无关文档。

- [ ] **Step 2: 运行 cadraq 文档/spec 必跑门禁**

Run:

```bash
pnpm format
pnpm test:contract -- packages/config/src/deployment-files.contract.test.ts
pnpm openspec:validate
```

Expected: Prettier check 通过；focused contract 通过并确认 `spec/TestStrategy.md` 保留验证指南入口；OpenSpec strict validation 通过。

- [ ] **Step 3: 重跑 AgentPhilosophy 最终状态检查**

Run from `/Users/zhaoyunyi/developer/AgentPhilosophy`:

```bash
uv run sync.py validate /Users/zhaoyunyi/developer/cadraq
uv run sync.py push /Users/zhaoyunyi/developer/cadraq --dry-run
uv run sync.py status --project /Users/zhaoyunyi/developer/cadraq
```

Expected: validate 通过；dry-run 全部是 `skip`；status 无 stale 或 drift。

- [ ] **Step 4: 形成 cadraq 本地中文 jj change**

Run from `/Users/zhaoyunyi/developer/cadraq`:

```bash
jj describe -m "同步：升级 AgentPhilosophy 0.7.5 默认能力"
jj new
jj status
```

Expected: 新工作副本为空，父 change 描述正确；不移动 `main`，不推送远端。

- [ ] **Step 5: 记录已验证与未验证边界**

最终交付说明必须列出：

- AgentPhilosophy ruff、全量 pytest、build、wheel smoke 与 GitHub Release 结果。
- cadraq format、focused contract、OpenSpec、sync validate/dry-run/status 结果。
- 未运行 cadraq typecheck、lint、全量 unit/BDD/e2e 和 live smoke；本轮未修改业务代码、用户流程、UI、运行时或线上环境，因此这些不属于完成门禁。
