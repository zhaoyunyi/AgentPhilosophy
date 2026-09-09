## 十四、构建流水线调优 skill

当前中央源默认 preset 包含 `skill-optimize-build-pipeline`（模块版本1.1.0）。它会把完整 Skill、测量合同、优化决策手册和
时间线/测试清单比较器，以及集成测试、Runner缓存和完整案例参考同步到：

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

模块1.1.0将ExampleBuildProject完整优化过程提炼为可迁移方法：先测每项测试/fixture与I/O，按持久性合同评估CI临时卷，隔离数据库与真实服务组，再验证依赖分层、预装工具和并发取消。案例中的容量、worker数和40分钟阈值不作为其他工程默认值。

按需读取的资源位于技能目录：

- `references/integration-testing.md`：计时、临时库、分组与完整测试清单。
- `references/runner-image-cache.md`：ownership、缓存成本、工具实际采用、镜像权限和取消清理。
- `references/case-study-build-pipeline.md`：真实run、失败修复、冷/热验收及未启用并行的依据。

```bash
python <skill-dir>/scripts/compare_test_runs.py before.tsv database.tsv serial.tsv --require-preserved
```

比较器只读文件，退出0/1/2分别代表保留门禁通过/未通过/无效输入；允许新增通过用例，丢失、重复或新增跳过会被指出。它不证明测试断言与coverage，也不把阶段工作量当并发墙钟。包内默认源和repo/Codex目标均包含这些资源；不要求安装额外服务或启用全局入口。
