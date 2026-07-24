---
name: optimize-build-pipeline
description: 以完整墙钟、阶段时间线、CPU/RSS/I/O、调度与缓存证据诊断和优化 CI、CD、Docker/BuildKit 镜像构建及 registry 供应链。用于构建太慢、self-hosted runner 利用率、缓存分层、并行/串行关键路径、CPU/VM 扩容、GitHub 与自建 GitLab 往返、Harbor/ACR 复制波动、完整 refs receipt 或优化前后 A/B 验收；要求不削弱测试、安全、source revision、digest 和发布门禁。
---

# 构建流水线调优

把目标定义为“缩短从可信 source revision 进入流水线到最终可消费 receipt 的完整墙钟”，而不是只让某个 build step 看起来更快。保留所有质量与供应链门禁，用一次只改变一个主要变量的 A/B 证据决定是否保留优化。

## 读取路由

- 开始测量或定义 evidence 时读取 [measurement-contract.md](references/measurement-contract.md)。
- 选择优化目标、判断是否加 CPU、迁 GitLab 或改 cache 时读取 [optimization-playbook.md](references/optimization-playbook.md)。
- 已有阶段开始/结束 epoch 时运行 `scripts/analyze_timeline.py`，不要手工相加并行阶段。

## 1. 锁定边界

先写清以下合同：

1. source of truth：仓库、分支、完整 revision、构建 context hash。
2. 完成点：CI 绿、镜像构建完成、registry digest 可拉取、最终 refs receipt，或产品 rollout。
3. 必须保留的 gate：测试、lint、coverage、扫描、smoke、digest equality、独立拉取。
4. 变更授权：只读诊断、流水线修改、集群资源修改和产品发布分别处理。
5. 不变量：是否允许修改 Deployment、tag、schema、Secret、runner trust boundary。

没有产品发布授权时，把 `product_image_refs_mutated=false` 作为验收不变量。供应链可用不等于产品已经上线。

## 2. 建立完整基线

至少采集一个自然新 revision 和一个同 revision 热缓存样本。不要把热缓存结果写成首次构建，也不要把多个 run 的最快阶段拼成一次不存在的墙钟。

统一记录：

- workflow create、queue、runner start、setup、source materialization；
- 每个测试/构建/smoke 的 start/end，不只记录 step 显示时长；
- artifact 上传/下载、CI wait、registry 复制、digest pull、receipt、cleanup；
- 组件或 job 的并行关系；
- runner/BuildKit/节点的 CPU、throttle、RSS、读写字节和峰值；
- cache scope、cache cold/warm、toolchain/base image/lockfile revision；
- run ID、attempt、source revision、最终 digest 与产品 refs 前后快照。

把数据写成 `measurement-contract.md` 定义的 TSV 后运行：

```bash
python skills/optimize-build-pipeline/scripts/analyze_timeline.py timeline.tsv --format markdown
python skills/optimize-build-pipeline/scripts/analyze_timeline.py timeline.tsv --format json --require-passed
```

## 3. 找关键路径而非最高峰

按墙钟贡献排序：

1. queue/调度等待；
2. checkout、Action/toolchain、module/package 下载；
3. 最慢的串行 gate；
4. 冷编译、链接、镜像 export/push；
5. CI wait、registry 复制和 digest smoke；
6. artifact/summary/cleanup 固定开销。

并行阶段不能相加。CPU 峰值低也不能直接推断“应加 CPU”：缓存命中可能已经消除了工作，外网等待和 export I/O 也会让 CPU 空闲。

## 4. 按价值顺序实施

依次评估，前一档没有足够收益再进入后一档：

1. 自动记录完整时间线与最终 receipt，先消除口径误差。
2. 消除重复 checkout、Action package、toolchain 和依赖下载；可信 runner 可使用按 SHA 校验的近端 mirror/snapshot。
3. 建立持久依赖缓存与编译缓存；cache key 必须绑定架构、toolchain、lockfile 和必要的 build flags。
4. 优化 Docker context、layer 顺序、`.dockerignore` 和 BuildKit cache mount；固定 base image digest。
5. 删除同一 revision 的重复 build/test，或在一个可信 runner 内共享 source/cache 后并行独立 gate。
6. 校准 Kubernetes `request` 与 `limit`：request 是调度保证，limit 才是上限。避免 request 过高导致并发工作被 scheduler 串行化。
7. 将 CI wait 与 registry 复制、digest smoke 等相互独立的最终验证重叠；最终 receipt 必须 join 全部分支并 fail closed。
8. 分离 registry task 时间、controller 建立/轮询 overhead 和实际传输字节，再决定轮询、事件驱动或网络治理。
9. 只有证据显示持续 CPU 饱和、throttle 或关键路径随 CPU 增加而缩短时，才扩 runner/VM CPU。
10. 只有剩余墙钟主要是代码托管往返，或另有主权/离线/可用性目标时，才把 GitLab 迁移列为速度优先项。

不得通过删除测试、降低 coverage、跳过扫描、使用 mutable tag、弱化 digest pull 或绕过 source binding 换取时间。

## 5. 做单变量 A/B

每项优化都记录：

- 假设和主要变量；
- 固定 revision、runner/节点、并发负载、cache 状态；
- baseline run ID 与 candidate run ID；
- 完整墙钟和受影响阶段；
- CPU/RSS/I/O/传输字节变化；
- 所有 gate、digest、receipt 和产品 refs 不变量；
- 保留或撤销阈值。

至少区分：

- 冷缓存/自然新 revision；
- 热缓存/同 revision 重建；
- 空闲 runner；
- CI 与正式构建真实并发。

外部服务有明显波动时用多轮中位数与范围，不用单轮最快值。优化使完整墙钟变差、I/O 暴增或失去确定性时立即撤销，并把失败方案固化为边界，防止以后重复试错。

## 6. 验收完整链路

最终至少跑一次当前正式入口，覆盖：

1. exact revision source materialization；
2. 全部 CI gate；
3. 所有组件构建与组件 smoke；
4. 内部 registry push/scan；
5. 所有目标仓库复制；
6. 每个最终 digest 的独立 pull/smoke；
7. source revision/context、Harbor/目标 registry digest equality；
8. refs receipt、secret scan、产品 refs 前后对照；
9. workflow 从创建到完成的真实墙钟。

异步优化必须证明：任一后台分支失败都会阻止 receipt；cleanup 会终止残留 waiter/pod；receipt 只在 join 后生成。

## 7. 报告结果

先给结果，再给阶段表：

```text
完整 workflow：<秒>
最终 receipt：第 <秒>
自然新 revision：<秒>
同 revision 热缓存：<秒>
相对 baseline：减少 <秒>/<百分比>
```

阶段表必须包含“阶段、耗时、串行/并行、证据 run”。同时报告：

- 当前关键路径和下一档最高价值目标；
- CPU 是否打满、增加 CPU 是否可能有效；
- cache 命中与首次构建的区别；
- 外部时延中可控 overhead 与不可控波动；
- 最终 digest/receipt；
- 产品是否真正 rollout；
- 被撤销方案及原因。

不要把预测值写成实测值。没有在最终配置下跑过自然新 revision 时，明确标记“未直接测量”。
