## 十六、Registry 文件

`registry.yaml` 位于 AgentPhilosophy 中央源根目录，是本机真实批量入口。它可以记录本机绝对路径，且已加入 `.gitignore`，供以下命令读取：

```bash
uv run sync.py status
uv run sync.py push --all --dry-run
uv run sync.py push --all --apply
```

`registry.example.yaml` 是可复用模板。新机器或新使用者应复制它为 `registry.yaml`，再把 `path` 改成本机真实路径；不要把 `registry.example.yaml` 当作真实批量同步入口。

需要在批量同步后调用大模型更新项目文档时，为对应项目增加 `documentation_paths`。这些值必须是项目根目录内的相对文件或目录路径；不要写项目根目录、绝对路径、密钥文件、托管文件或代码目录。未声明该字段的项目仍会正常批量同步，但跳过模型阶段。

示例结构：

```yaml
schema_version: 1
projects:
  - name: ExampleProject
    path: /absolute/path/to/ExampleProject
```
