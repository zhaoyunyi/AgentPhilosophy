# 灵活多 Agent 与可选 Superpowers 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让默认项目按任务选择合适的模型与推理强度，并将 Superpowers 从默认依赖改为项目显式可选模块。

**Architecture:** 保留 `model-constraints` 和 `superpowers-system` 两个独立模块，通过更新前者模板、移除四个 preset 对后者的默认引用来改变默认行为。仓库中央源与 Python 包内 `default_source` 镜像同步修改，最后通过 `0.7.7` 版本、状态文件、BDD、端到端测试和安装后 smoke 证明下游可发现并安全应用更新。

**Tech Stack:** Python 3.12、Jinja2、YAML、pytest、Bash、uv、Jujutsu（jj）

## Global Constraints

- CLI 版本和中央内容版本都提升到 `0.7.7`。
- `model-constraints` 模块版本提升到 `1.1.0`；`superpowers-system` 保持 `6.1.1`。
- 不删除 `superpowers-system` 模块，也不改变显式启用时的渲染内容。
- 不自动删除下游项目中已有的显式 `superpowers-system` 声明。
- 不写死模型名称、provider 或模型白名单，不新增项目配置变量。
- 根目录中央源与 `src/agentphilosophy/default_source` 包内镜像必须逐字节一致。
- 当前仓使用 jj；每个任务用中文 change 描述收口，不使用 `git add`、`git commit`、`git stash` 或 `git checkout`。
- 只准备本地 release，不推送、不打 tag、不创建或发布 GitHub Release。

---

## 文件职责映射

- `modules/model-constraints/**`：多 Agent 模型、推理强度和调度规则的中央模块源。
- `presets/*.yaml`：新项目初始化时使用的默认模块集合。
- `modules/superpowers-system/**`：Superpowers 显式 opt-in 模块；本次保持功能不变。
- `docs/cli-usage-for-llm.md`、`docs/llm-usage-*.md|json`：LLM 接入和模块选择合同。
- `src/agentphilosophy/default_source/**`：上述中央内容随 wheel 分发的镜像。
- `.agentphilosophy.yaml`：AgentPhilosophy 自身的模块依赖真值。
- `AGENTS.md`、`.agents/agentphilosophy-state.yaml`：同步器根据当前配置生成的托管输出和状态，不手工维护。
- `tests/bdd/test_user_flows.py`：面向用户行为的成功与兼容场景。
- `tests/e2e/test_sync_cli.py`：真实 CLI 初始化、渲染和 LLM 使用合同。
- `scripts/release-smoke.sh`、`tests/test_ci_release_gate.py`：安装后 release 合同及其静态守卫。
- `scripts/prepare-release.sh`：版本、lock、当前仓同步、全量验证、构建和 release notes 的唯一准备入口。

### Task 1: 升级多 Agent 模型与推理强度规则

**Files:**
- Modify: `tests/e2e/test_sync_cli.py`
- Modify: `modules/model-constraints/templates/model-rules.md.j2`
- Modify: `modules/model-constraints/module.yaml`
- Modify: `catalog.yaml`
- Modify: `src/agentphilosophy/default_source/modules/model-constraints/templates/model-rules.md.j2`
- Modify: `src/agentphilosophy/default_source/modules/model-constraints/module.yaml`
- Modify: `src/agentphilosophy/default_source/catalog.yaml`

**Interfaces:**
- Consumes: `doc-templates` 的 `model_constraints` fragment section，以及 preset 已声明的 `model-constraints` 模块。
- Produces: `model-constraints@1.1.0`，向 `AGENTS.md` 渲染五条不绑定具体模型名的多 Agent 规则。

- [ ] **Step 1: 写入失败的端到端测试**

在 `tests/e2e/test_sync_cli.py` 增加：

```python
@pytest.mark.parametrize("preset", ["fullstack", "frontend", "mobile-sdk", "orchestrator"])
def test_packaged_preset_uses_task_matched_model_and_reasoning(tmp_path: Path, preset: str) -> None:
    target = tmp_path / "target"
    workdir = tmp_path / "workdir"
    workdir.mkdir()

    for args in (["init", str(target), "--preset", preset], ["push", str(target), "--apply"]):
        result = subprocess.run(
            [sys.executable, str(Path(__file__).resolve().parents[2] / "sync.py"), *args],
            cwd=workdir,
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr + result.stdout

    agents_text = (target / "AGENTS.md").read_text(encoding="utf-8")
    assert "根据任务复杂度、风险、不确定性、时效和成本，选择合适的模型与推理强度" in agents_text
    assert "高风险、跨模块、难验证或证据不足的任务" in agents_text
    assert "机械、低风险、边界清晰且容易验证的任务" in agents_text
    assert "为子 agent 明确目标、负责范围、输入、预期产物和验收标准" in agents_text
    assert "默认继承当前会话模型和 reasoning" not in agents_text
    assert "不为子任务随意指定更弱模型" not in agents_text
```

- [ ] **Step 2: 运行测试并确认旧规则导致失败**

Run:

```bash
uv run pytest -q tests/e2e/test_sync_cli.py::test_packaged_preset_uses_task_matched_model_and_reasoning
```

Expected: 四个参数用例均 FAIL，首个失败断言缺少“根据任务复杂度、风险、不确定性、时效和成本”。

- [ ] **Step 3: 更新中央模块和包内镜像**

将根目录和包内镜像的 `model-rules.md.j2` 都改为：

```jinja2
- 根据任务复杂度、风险、不确定性、时效和成本，选择合适的模型与推理强度。
- 高风险、跨模块、难验证或证据不足的任务，优先使用能力更强的模型和更充分的推理。
- 机械、低风险、边界清晰且容易验证的任务，可以使用更轻量的模型与推理强度。
- 只有任务可独立推进、职责清晰且写入范围不冲突时才使用多 agent。
- 为子 agent 明确目标、负责范围、输入、预期产物和验收标准；修改代码时避免覆盖其他 agent 或用户的改动。
{% for rule in extra_model_rules | default([], true) -%}
- {{ rule }}
{% endfor %}
```

在两份 `module.yaml` 中使用相同元数据：

```yaml
name: model-constraints
description: 多 Agent 模型、推理强度和代理调度约束
version: 1.1.0
```

其余 `requires`、`provides` 和 `outputs` 保持不变。两份 `catalog.yaml` 的 `model-constraints` 描述同步改为：

```yaml
description: 多 Agent 模型、推理强度和代理调度约束
```

- [ ] **Step 4: 运行聚焦测试与镜像一致性测试**

Run:

```bash
uv run pytest -q \
  tests/e2e/test_sync_cli.py::test_packaged_preset_uses_task_matched_model_and_reasoning \
  tests/test_packaged_source.py::test_packaged_default_source_matches_repository_source
```

Expected: `5 passed`。

- [ ] **Step 5: 用 jj 收口任务 change**

```bash
jj diff --summary
jj describe -m "规范：按任务选择多 Agent 模型与推理强度"
jj new
```

Expected: 新工作副本为空，父 change 只包含本任务列出的测试、模块和 catalog 描述改动。

### Task 2: 将 Superpowers 改为默认关闭、显式启用

**Files:**
- Modify: `tests/e2e/test_sync_cli.py`
- Modify: `tests/bdd/test_user_flows.py`
- Modify: `presets/frontend.yaml`
- Modify: `presets/fullstack.yaml`
- Modify: `presets/mobile-sdk.yaml`
- Modify: `presets/orchestrator.yaml`
- Modify: `src/agentphilosophy/default_source/presets/frontend.yaml`
- Modify: `src/agentphilosophy/default_source/presets/fullstack.yaml`
- Modify: `src/agentphilosophy/default_source/presets/mobile-sdk.yaml`
- Modify: `src/agentphilosophy/default_source/presets/orchestrator.yaml`
- Modify: `.agentphilosophy.yaml`

**Interfaces:**
- Consumes: catalog 中继续存在的 `superpowers-system` 模块和 `doc-templates` 依赖。
- Produces: 四个不默认声明 Superpowers 的 preset；显式加入模块后仍可渲染原有 Superpowers section。

- [ ] **Step 1: 把默认与显式 opt-in 行为写成失败测试**

在 `tests/e2e/test_sync_cli.py` 中：

1. 将 `test_packaged_fullstack_without_optional_superpowers_has_no_blank_section` 改名为 `test_packaged_fullstack_without_superpowers_has_no_blank_section`，删除“先断言存在再从配置删除模块”的三行，让它直接同步默认 fullstack 并断言：

```python
project_config = config_path.read_text(encoding="utf-8")
assert "- superpowers-system" not in project_config
assert "Superpowers System" not in agents_text
assert "\n\n\n## 工程规范" not in agents_text
```

2. 将 `test_packaged_preset_declares_superpowers_version_by_default` 替换为：

```python
@pytest.mark.parametrize("preset", ["fullstack", "frontend", "mobile-sdk", "orchestrator"])
def test_packaged_preset_does_not_enable_superpowers_by_default(tmp_path: Path, preset: str) -> None:
    target = tmp_path / "target"
    workdir = tmp_path / "workdir"
    workdir.mkdir()

    for args in (["init", str(target), "--preset", preset], ["push", str(target), "--apply"]):
        result = subprocess.run(
            [sys.executable, str(Path(__file__).resolve().parents[2] / "sync.py"), *args],
            cwd=workdir,
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr + result.stdout

    project_config = (target / ".agentphilosophy.yaml").read_text(encoding="utf-8")
    agents_text = (target / "AGENTS.md").read_text(encoding="utf-8")
    assert "- model-constraints" in project_config
    assert "- superpowers-system" not in project_config
    assert "Superpowers System" not in agents_text
    assert "Superpowers skill 版本为 `6.1.1`" not in agents_text
```

3. 新增显式启用测试：

```python
def test_packaged_project_can_explicitly_enable_superpowers(tmp_path: Path) -> None:
    target = tmp_path / "target"
    workdir = tmp_path / "workdir"
    workdir.mkdir()

    init_result = subprocess.run(
        [sys.executable, str(Path(__file__).resolve().parents[2] / "sync.py"), "init", str(target), "--preset", "fullstack"],
        cwd=workdir,
        text=True,
        capture_output=True,
        check=False,
    )
    assert init_result.returncode == 0, init_result.stderr + init_result.stdout

    config_path = target / ".agentphilosophy.yaml"
    config_text = config_path.read_text(encoding="utf-8")
    config_path.write_text(
        config_text.replace("- model-constraints\n", "- model-constraints\n- superpowers-system\n", 1),
        encoding="utf-8",
    )

    push_result = subprocess.run(
        [sys.executable, str(Path(__file__).resolve().parents[2] / "sync.py"), "push", str(target), "--apply"],
        cwd=workdir,
        text=True,
        capture_output=True,
        check=False,
    )
    assert push_result.returncode == 0, push_result.stderr + push_result.stdout

    agents_text = (target / "AGENTS.md").read_text(encoding="utf-8")
    assert "Superpowers System" in agents_text
    assert "Superpowers skill 版本为 `6.1.1`" in agents_text
    assert "~/.codex/superpowers" in agents_text
    assert "~/.agents/skills/superpowers" in agents_text
```

在 `tests/bdd/test_user_flows.py` 新增：

```python
def test_bdd_default_preset_excludes_superpowers_but_keeps_multi_agent_rules(tmp_path: Path) -> None:
    source = Path(__file__).resolve().parents[2]
    target = tmp_path / "default-project"

    assert main(["--source", str(source), "init", str(target), "--preset", "orchestrator"]) == 0
    assert main(["--source", str(source), "push", str(target), "--apply"]) == 0

    config_text = (target / ".agentphilosophy.yaml").read_text(encoding="utf-8")
    agents_text = (target / "AGENTS.md").read_text(encoding="utf-8")
    assert "- model-constraints" in config_text
    assert "- superpowers-system" not in config_text
    assert "选择合适的模型与推理强度" in agents_text
    assert "Superpowers System" not in agents_text


def test_bdd_explicit_superpowers_selection_is_preserved(tmp_path: Path) -> None:
    source = Path(__file__).resolve().parents[2]
    target = tmp_path / "opt-in-project"

    assert main(["--source", str(source), "init", str(target), "--preset", "orchestrator"]) == 0
    config_path = target / ".agentphilosophy.yaml"
    config_text = config_path.read_text(encoding="utf-8")
    config_path.write_text(
        config_text.replace("- model-constraints\n", "- model-constraints\n- superpowers-system\n", 1),
        encoding="utf-8",
    )

    assert main(["--source", str(source), "push", str(target), "--apply"]) == 0
    agents_text = (target / "AGENTS.md").read_text(encoding="utf-8")
    assert "Superpowers System" in agents_text
    assert "Superpowers skill 版本为 `6.1.1`" in agents_text
```

- [ ] **Step 2: 运行测试并确认默认 preset 仍启用 Superpowers**

Run:

```bash
uv run pytest -q \
  tests/e2e/test_sync_cli.py::test_packaged_fullstack_without_superpowers_has_no_blank_section \
  tests/e2e/test_sync_cli.py::test_packaged_preset_does_not_enable_superpowers_by_default \
  tests/e2e/test_sync_cli.py::test_packaged_project_can_explicitly_enable_superpowers \
  tests/bdd/test_user_flows.py::test_bdd_default_preset_excludes_superpowers_but_keeps_multi_agent_rules \
  tests/bdd/test_user_flows.py::test_bdd_explicit_superpowers_selection_is_preserved
```

Expected: 默认关闭相关用例 FAIL；显式启用用例保持 PASS，证明模块本身没有被删除。

- [ ] **Step 3: 从默认 preset 和当前仓配置移除模块**

在根目录与包内镜像的四份 preset 中，把相邻模块列表从：

```yaml
  - jj-conventions
  - model-constraints
  - superpowers-system
  - doc-templates
```

改为：

```yaml
  - jj-conventions
  - model-constraints
  - doc-templates
```

在 `.agentphilosophy.yaml` 中做同样删除。不要修改 `modules/superpowers-system/**` 或 catalog 中该模块的登记。

- [ ] **Step 4: 运行用户行为、端到端和镜像测试**

Run:

```bash
uv run pytest -q \
  tests/e2e/test_sync_cli.py::test_packaged_fullstack_without_superpowers_has_no_blank_section \
  tests/e2e/test_sync_cli.py::test_packaged_preset_does_not_enable_superpowers_by_default \
  tests/e2e/test_sync_cli.py::test_packaged_project_can_explicitly_enable_superpowers \
  tests/bdd/test_user_flows.py::test_bdd_default_preset_excludes_superpowers_but_keeps_multi_agent_rules \
  tests/bdd/test_user_flows.py::test_bdd_explicit_superpowers_selection_is_preserved \
  tests/test_packaged_source.py::test_packaged_default_source_matches_repository_source
```

Expected: `9 passed`。

- [ ] **Step 5: 检查当前仓同步计划并提交任务 change**

```bash
uv run sync.py validate
uv run sync.py push . --dry-run
jj diff --summary
jj describe -m "配置：将 Superpowers 调整为项目显式可选"
jj new
```

Expected: `validate` 成功；dry-run 计划刷新 `AGENTS.md` 和 state，但本任务不手工编辑托管输出；新工作副本为空。

### Task 3: 更新 LLM 接入合同与安装后 release smoke

**Files:**
- Modify: `tests/e2e/test_sync_cli.py`
- Modify: `tests/test_ci_release_gate.py`
- Modify: `docs/cli-usage-for-llm.md`
- Modify: `docs/llm-usage-auto-config.md`
- Modify: `docs/llm-usage-user-breakpoints.md`
- Modify: `docs/llm-usage-user-breakpoints.json`
- Modify: `src/agentphilosophy/default_source/docs/cli-usage-for-llm.md`
- Modify: `src/agentphilosophy/default_source/docs/llm-usage-auto-config.md`
- Modify: `src/agentphilosophy/default_source/docs/llm-usage-user-breakpoints.md`
- Modify: `src/agentphilosophy/default_source/docs/llm-usage-user-breakpoints.json`
- Modify: `README.md`
- Modify: `scripts/release-smoke.sh`

**Interfaces:**
- Consumes: Task 2 的默认关闭 preset 与仍可显式启用的模块。
- Produces: LLM 自动配置、用户断点、完整 CLI 文档和安装后 wheel smoke 对同一默认策略的统一合同。

- [ ] **Step 1: 为 LLM 推荐项和 release smoke 写失败守卫**

在 `tests/e2e/test_sync_cli.py` 的 `test_cli_prints_llm_usage_document_from_default_source` 中增加：

```python
assert "默认不追加 `superpowers-system`" in auto_result.stdout
assert "推荐选择：`skip-module`" in breakpoint_result.stdout

superpowers_breakpoint = next(
    item for item in breakpoint_payload["breakpoints"] if item["id"] == "superpowers-system"
)
assert superpowers_breakpoint["recommended"]["id"] == "skip-module"
assert superpowers_breakpoint["options"][0]["id"] == "skip-module"
```

在 `tests/test_ci_release_gate.py::test_release_smoke_script_checks_installed_cli_and_state_versions` 中用以下精确守卫替换默认 Superpowers 断言：

```python
assert '! grep -q "superpowers-system" "$target/.agentphilosophy.yaml"' in content
assert 'grep -q "选择合适的模型与推理强度" "$target/AGENTS.md"' in content
assert 'superpowers_target="$smoke_root/project-with-superpowers"' in content
assert "Superpowers skill 版本为 \\`6.1.1\\`" in content
assert "~/.agents/skills/superpowers" in content
```

- [ ] **Step 2: 运行守卫并确认文档和脚本仍表达旧默认**

Run:

```bash
uv run pytest -q \
  tests/e2e/test_sync_cli.py::test_cli_prints_llm_usage_document_from_default_source \
  tests/test_ci_release_gate.py::test_release_smoke_script_checks_installed_cli_and_state_versions
```

Expected: 两个测试均 FAIL，分别缺少 `skip-module` 推荐语义和默认关闭 smoke 命令。

- [ ] **Step 3: 更新自动配置与用户断点文档**

在根目录和包内 `llm-usage-auto-config.md` 中将两条 Superpowers 规则改为：

```markdown
| 新项目使用默认 preset | 默认不追加 `superpowers-system`；需要 Superpowers 时由项目显式选择 |
| 项目明确需要统一 Superpowers 固定路径、版本和排障规则 | 追加 `superpowers-system`，再同步刷新 `AGENTS.md` |
```

在两份 `llm-usage-user-breakpoints.md` 中使用：

```markdown
推荐选择：`skip-module`，因为 Superpowers 是项目可选能力；只有项目明确需要统一其安装位置、版本和排障方式时才追加。

可选项：
1. `skip-module`：不修改项目配置。影响：保持默认 preset，不新增 Superpowers 约束。
2. `add-module`：追加 `superpowers-system`。影响：后续 `push --apply` 会刷新 `AGENTS.md` 中的 Superpowers 6.1.1 约束。
3. `minimal-config`：保持极简配置。影响：只保留项目当前显式模块，后续需要时再单独追加。
```

在两份 JSON 中把 `superpowers-system` breakpoint 完整改为：

```json
{
  "id": "superpowers-system",
  "title": "是否同步 Superpowers 6.1.1 约束",
  "question": "我需要确认是否把 Superpowers 的 Codex 原生 discovery 固定路径、版本和排障规则写入 `AGENTS.md`。",
  "why": "Superpowers 是显式可选模块；这个选择会决定是否向 `.agentphilosophy.yaml` 追加 `superpowers-system`。",
  "recommended": {
    "id": "skip-module",
    "reason": "默认 preset 不启用 Superpowers；只有项目明确需要统一其安装位置、版本和排障方式时才追加。"
  },
  "options": [
    {
      "id": "skip-module",
      "label": "保持默认配置",
      "impact": "不新增 Superpowers 约束。"
    },
    {
      "id": "add-module",
      "label": "追加 `superpowers-system`",
      "impact": "后续 `push --apply` 会刷新 `AGENTS.md` 中的 Superpowers 6.1.1 约束。"
    },
    {
      "id": "minimal-config",
      "label": "保持极简配置",
      "impact": "只保留项目当前显式模块，后续需要时再单独追加。"
    }
  ],
  "reply_format": "回复选项编号或 id"
}
```

- [ ] **Step 4: 更新完整 CLI 文档、README 和 release smoke**

在两份 `cli-usage-for-llm.md` 中：

- 从默认配置 YAML 示例删除 `- superpowers-system`。
- 将第五节首句改为：

```markdown
`superpowers-system` 是显式可选模块，不包含在中央源默认 preset 中。该模块不会复制上游 Superpowers 仓库，也不会生成项目级 `SKILL.md`；它只把 Codex 原生 skill discovery 的固定路径、排障方式和当前项目要求的 Superpowers skill 版本 `6.1.1` 写入 `AGENTS.md`。
```

- 保留显式追加模块的 YAML 和四步同步命令。
- 明确旧项目已有显式声明时继续保留，不因默认值变化自动删除。

在 `README.md` 的文档入口说明中，把 `superpowers-system` 描述为“可选的原生 discovery 版本约束”，删除“默认 preset”语义。

在 `scripts/release-smoke.sh` 默认 fullstack 同步后使用：

```bash
! grep -q "superpowers-system" "$target/.agentphilosophy.yaml"
grep -q "model-constraints" "$target/.agentphilosophy.yaml"
grep -q "选择合适的模型与推理强度" "$target/AGENTS.md"
! grep -q "Superpowers System" "$target/AGENTS.md"
```

随后增加独立显式 opt-in smoke：

```bash
superpowers_target="$smoke_root/project-with-superpowers"
mkdir -p "$superpowers_target"
cat >"$superpowers_target/.agentphilosophy.yaml" <<'YAML'
project_name: SuperpowersSmoke
project_type: orchestrator
modules:
  - doc-templates
  - model-constraints
  - superpowers-system
YAML
"$smoke_root/venv/bin/agentphilosophy-sync" validate "$superpowers_target" >/dev/null
"$smoke_root/venv/bin/agentphilosophy-sync" push "$superpowers_target" --dry-run >/dev/null
"$smoke_root/venv/bin/agentphilosophy-sync" push "$superpowers_target" --apply >/dev/null
grep -q "Superpowers skill 版本为 \`6.1.1\`" "$superpowers_target/AGENTS.md"
grep -q "~/.agents/skills/superpowers" "$superpowers_target/AGENTS.md"
```

- [ ] **Step 5: 运行文档、LLM、脚本和镜像验证**

Run:

```bash
uv run pytest -q \
  tests/e2e/test_sync_cli.py::test_cli_prints_llm_usage_document_from_default_source \
  tests/test_ci_release_gate.py::test_release_smoke_script_checks_installed_cli_and_state_versions \
  tests/test_packaged_source.py::test_packaged_default_source_matches_repository_source \
  tests/test_packaged_source.py::test_long_lived_docs_are_listed_in_docs_index
bash -n scripts/release-smoke.sh
uv run sync.py llm-usage --mode user-breakpoints --format json >/dev/null
```

Expected: `4 passed`，Bash 语法检查和 JSON 输出命令退出码均为 0。

- [ ] **Step 6: 用 jj 收口任务 change**

```bash
jj diff --summary
jj describe -m "文档：统一 Superpowers 可选接入合同"
jj new
```

Expected: 新工作副本为空，父 change 仅包含 LLM 文档、包内镜像、README、release smoke 和对应测试守卫。

### Task 4: 准备 0.7.7 release 并刷新当前仓托管输出

**Files:**
- Modify via `scripts/prepare-release.sh`: `pyproject.toml`
- Modify via `scripts/prepare-release.sh`: `src/agentphilosophy/__init__.py`
- Modify via `scripts/prepare-release.sh`: `README.md`
- Modify via `scripts/prepare-release.sh`: `catalog.yaml`
- Modify via `scripts/prepare-release.sh`: `src/agentphilosophy/default_source/catalog.yaml`
- Modify via `scripts/prepare-release.sh`: `uv.lock`
- Modify via sync: `AGENTS.md`
- Modify via sync: `.agents/agentphilosophy-state.yaml`
- Create: `dist/release-notes-v0.7.7.md`

**Interfaces:**
- Consumes: Tasks 1-3 的干净 jj 父 changes、`model-constraints@1.1.0`、默认关闭 preset 和统一 LLM/release 合同。
- Produces: 可构建的 `agentphilosophy@0.7.7` 本地 release、`content_version: 0.7.7`、不含 Superpowers 的当前仓托管规则和完整验证证据。

- [ ] **Step 1: 确认 release 准备从干净工作副本开始**

Run:

```bash
jj status
jj log -r 'ancestors(@, 5)' --no-graph -T 'change_id.short() ++ " " ++ description.first_line() ++ "\n"'
```

Expected: `The working copy has no changes.`；最近三个非空父 changes 分别对应 Tasks 1-3，且设计与计划 changes 仍在祖先链中。

- [ ] **Step 2: 运行官方 release 准备入口**

Run:

```bash
bash scripts/prepare-release.sh 0.7.7
```

Expected: 末行包含 `Prepared AgentPhilosophy release v0.7.7 with content_version 0.7.7.`；脚本内部的 ruff、全量 pytest、中央源 validate、build 和安装后 release smoke 全部成功。

- [ ] **Step 3: 核对当前仓配置、托管输出与状态**

Run:

```bash
rg -n "version = \"0.7.7\"|content_version: 0.7.7" pyproject.toml catalog.yaml src/agentphilosophy/default_source/catalog.yaml
rg -n "选择合适的模型与推理强度" AGENTS.md
! rg -n "默认继承当前会话模型|Superpowers System" AGENTS.md
rg -n "model-constraints: 1.1.0|agentphilosophy_version: 0.7.7|source_content_version: 0.7.7" .agents/agentphilosophy-state.yaml
! rg -n "superpowers-system" .agents/agentphilosophy-state.yaml
uv run sync.py status --project .
```

Expected:

- 版本和 content version 都是 `0.7.7`。
- `AGENTS.md` 命中新版“选择合适的模型与推理强度”，不命中旧继承规则或 `Superpowers System`。
- state 命中 `model-constraints: 1.1.0` 和两个 `0.7.7`，不命中 `superpowers-system`。
- `status --project .` 退出码为 0，且没有 stale、conflict 或 newer-than-current 提示。

- [ ] **Step 4: 复跑最终验证命令**

Run:

```bash
uv run sync.py validate
uv run ruff check .
uv run pytest -q
uv lock --check
uv build
bash scripts/release-smoke.sh dist/agentphilosophy-0.7.7-py3-none-any.whl
```

Expected: validate、ruff、pytest、lock、build 和安装后 smoke 全部退出 0；smoke 末行包含 `release smoke ok: agentphilosophy=0.7.7, content=0.7.7`。

- [ ] **Step 5: 审查 release diff 与 notes**

Run:

```bash
jj diff --summary
jj diff --stat
sed -n '1,240p' dist/release-notes-v0.7.7.md
```

Expected: diff 只包含本任务列出的版本、lock、托管输出、state 和 release notes；release notes 明确多 Agent 规则升级、Superpowers 默认关闭与显式兼容，不包含占位文案。

- [ ] **Step 6: 用 jj 提交 release change 并留下干净子 change**

```bash
jj describe -m "发布：AgentPhilosophy 0.7.7 灵活多 Agent 默认策略"
jj new
jj status
```

Expected: 新工作副本显示 `The working copy has no changes.`；不设置或推送 `main` bookmark，不执行 `scripts/publish-release.sh`。

---

## 最终审查清单

- [ ] 设计目标分别由 Tasks 1-4 覆盖，没有删除显式 Superpowers 能力。
- [ ] 根目录中央源与包内镜像一致性测试通过。
- [ ] BDD 同时覆盖默认关闭和显式启用。
- [ ] 默认 preset 的四种项目类型全部覆盖。
- [ ] 当前仓配置、`AGENTS.md` 与 state 一致。
- [ ] 最终回复区分已验证结果、未执行的外部发布与未同步的下游项目。
