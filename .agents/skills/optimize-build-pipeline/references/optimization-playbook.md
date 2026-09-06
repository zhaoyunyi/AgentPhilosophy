# 构建流水线优化决策手册

## 目录

1. 价值排序
2. Source 与工具链往返
3. 依赖和编译缓存
4. 镜像层与可复现性
5. 并行、调度与 CPU
6. Registry 和最终控制器
7. GitHub 与 GitLab
8. A/B 接受标准

## 1. 价值排序

以“预期节省墙钟 × 发生频率 × 成功概率 ÷ 实施与维护成本”排序。优先消除工作，再优化工作，最后扩硬件。

| 观察 | 第一假设 | 优先动作 |
|---|---|---|
| checkout/下载占多数 | 远端往返 | exact-SHA mirror、预装工具、依赖近端缓存 |
| 同 revision 重复编译 | cache scope 不持久或 key 漂移 | 固定持久 cache、审计 key/context |
| 多 job 各自 checkout | 隔离粒度过细 | 可信单 runner 一次物化、Pod 内并行 gate |
| Pod Pending 且节点 CPU 空闲 | request 保留量过高 | 校准 request，保留足够 limit |
| CPU throttle 高且耗时随 CPU 下降 | CPU cap | 增加 limit/request 或 VM CPU |
| CPU 低、写入巨大 | layer export/rewrite | 减少 layer 失效、撤销高成本重写 |
| registry task 短、controller 长 | 控制面 overhead | 缩轮询/事件等待/并行 execution |
| CI wait 后才复制 | 独立阶段串行 | 后台 wait，与 registry validation 重叠后 join |

## 2. Source 与工具链往返

按顺序处理：

1. 使用 exact SHA 浅 fetch，禁止只按 mutable branch 构建。
2. 对可信默认分支建立节点本地 bare mirror 或 source cache。
3. 从 mirror 创建不可变浅快照；快照只读挂给正式构建。
4. 把固定版本 Go/Node/pnpm/linter/scanner/browser 预装到 runner image。
5. 避免每个 job 下载相同 Action package 或 artifact。

mirror 不是新的 source of truth。远端 revision 仍是权威，mirror 只提供经过 SHA 校验的传输优化。不可信 PR 不复用高权限默认分支 runner。

## 3. 依赖和编译缓存

建立三层 cache：

1. 包管理器下载 cache：Go module、pnpm/npm、Cargo、pip/uv。
2. 编译器 cache：Go build cache、ccache/sccache、增量编译目录。
3. BuildKit layer/cache mount：跨临时 Pod 持久。

验收 cache 时至少证明：

- 第一次 cache bootstrap 与后续热命中分开计时；
- 临时 runner/pod 更换后 cache 仍有效；
- lockfile/toolchain/architecture 变化会正确失效；
- 并发访问使用合适的 sharing/locking；
- cache 命中不跳过源代码、测试或安全 gate；
- 本地盘有 GC、水位和恢复边界。

不要把 cache size 声明当文件系统硬配额。持续记录真实目录占用和节点剩余空间。

## 4. 镜像层与可复现性

优先级：

1. 精简 `.dockerignore` 和 build context。
2. 把低频变化的依赖层放在高频源码 COPY 前。
3. 使用 BuildKit cache mount 保存包管理器 store，不把 store COPY 进最终层。
4. 多 stage 只复制运行需要的产物。
5. 固定所有 base image registry digest。
6. 记录每组件 source context hash。

固定 base digest 能消除 mutable tag 漂移，但不保证不同时间构建的最终 image digest bit-for-bit 相同。若要求强可复现性，可单独试验 `SOURCE_DATE_EPOCH`、provenance 与 timestamp rewrite；必须先量冷/热构建、layer 写入和 export 成本。性能显著回退时不要默认启用。

## 5. 并行、调度与 CPU

并行化条件：

- 输入不可变；
- 输出目录、端口和临时文件隔离；
- gate 之间没有数据依赖；
- 任一 gate 失败可 collect-all 后统一 fail；
- 最终汇总不会漏掉失败或缺失结果。

Kubernetes 调度：

```text
并发可调度条件 = 已分配 requests + 新 Pod requests <= allocatable/quota
真实 CPU 上限 = container limit（未设置时受节点竞争约束）
```

若 request 从 10 降到 6、limit 仍为 20，Pod 可以实际使用超过 6 CPU；但节点拥塞时只保证 6。根据稳态 P95 使用量、启动 burst 和服务等级选 request，不用峰值直接当 request。

CPU A/B 必须固定 source、cache 和并发负载。至少测试 2～3 档，并观察：

- 构建耗时是否单调下降；
- throttled ratio；
- CPU 平均/峰值；
- I/O 与 memory 是否成为新瓶颈；
- 12→16 等高档的边际收益。

边际收益低于维护成本时停止扩容。

## 6. Registry 和最终控制器

四组件/多仓库复制优先并行，digest pull smoke 也可并行。进一步缩短完整链路时，把同 revision CI wait 作为后台分支：

```text
验证内部 receipt
├── wait CI(same revision)
└── replicate all repositories -> verify digest pulls
join CI + registry validation
write final refs receipt
```

实现要求：

- 后台 wait 把成功结果写入临时状态文件；
- 主进程 `wait` 并校验状态字段；
- trap 在失败时终止 waiter 和临时 smoke Pod；
- CI、复制或 pull 任一失败均不生成 ready receipt；
- 记录 `ci_registry_validation_overlap_seconds`。

ACR/Harbor 波动应拆为 task 与 controller overhead。不能用缩短 timeout 隐藏 59 秒异常，也不能承诺外部网络永远恢复到 15 秒；可以通过重叠降低它对关键路径的贡献。

## 7. GitHub 与 GitLab

先量以下时间再决定迁移：

- source checkout；
- Action/tool download；
- queue/runner registration；
- artifact 上传/下载；
- status/summary/cleanup；
- 构建、测试、registry 等与代码托管无关阶段。

若近端 source snapshot、预装 runner 和本地 artifact 已把 GitHub 数据面降到数秒，仅为速度迁 GitLab 通常只能再省固定调度/元数据时间。只有剩余关键路径确实在 GitHub，或代码主权、离线恢复、可用性本身是目标时，才计算 GitLab HA、备份、升级、runner、权限和迁移成本。

## 8. A/B 接受标准

每个 candidate 满足全部条件才保留：

```text
完整墙钟达到预设收益阈值
全部原 gate 仍通过
source revision/context 完全绑定
最终 digest 可独立拉取
secret scan 通过
产品 refs 未越权修改
没有新的持续 Pending/throttle/disk pressure
失败路径不生成 ready receipt
回滚方法已验证或明确
```

建议阈值：固定开销优化至少节省 5 秒或 10%；结构性优化至少节省 15%；资源扩容要求多轮中位数有稳定收益。具体阈值应按项目构建频率和维护成本调整。
