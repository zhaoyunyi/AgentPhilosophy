## 十四、构建流水线调优 skill

当前中央源默认 preset 包含 `skill-optimize-build-pipeline`。它会把完整 Skill、测量合同、优化决策手册和
时间线分析器同步到：

```text
skills/optimize-build-pipeline/
.agents/skills/optimize-build-pipeline/
```

该 Skill 用于诊断和优化 CI/CD、self-hosted runner、Docker/BuildKit 镜像构建与 registry 供应链，统一要求：

- 记录 workflow 创建到最终 receipt 的真实完整墙钟；
- 区分自然新 revision、冷缓存、热缓存、空闲和真实并发；
- 同时采集 CPU/throttle、RSS、I/O、调度 request/limit、cache 与 registry task/overhead；
- 优先消除重复网络/构建，再做 cache、并行、调度校准，最后才扩 CPU 或迁代码托管平台；
- 保留测试、coverage、扫描、smoke、source revision/context、digest equality 和独立 pull；
- 最终 receipt 仅在所有异步 gate join 后生成，不把供应链验收写成产品已 rollout。

已有项目的 `modules` 是显式冻结的。需要长期复用这套调优流程时追加：

```yaml
modules:
  - existing-module
  - skill-optimize-build-pipeline
```

随后执行标准同步流程，并验证 repo/Codex 两个目标目录内容一致：

```bash
agentphilosophy-sync validate
agentphilosophy-sync validate /path/to/project
agentphilosophy-sync push /path/to/project --dry-run
agentphilosophy-sync push /path/to/project --apply
find -L /path/to/project/{skills,.agents/skills}/optimize-build-pipeline -type f -print
```

时间线分析器接受 `stage/start_epoch/end_epoch/lane/category/status` TSV；它会计算真实墙钟、并发重叠、空闲
间隙和峰值并行度，避免把并行阶段手工相加。它不自动宣称关键路径，仍需结合依赖关系和原始 run evidence。
