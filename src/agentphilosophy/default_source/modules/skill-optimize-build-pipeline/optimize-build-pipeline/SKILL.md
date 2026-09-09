---
name: optimize-build-pipeline
description: 用完整墙钟、测试与 fixture、CPU/I/O、缓存和制品回执定位并优化 CI/CD 瓶颈。适用于流水线慢、集成测试并行、临时数据库、Runner 工具预装、Docker/BuildKit 分层及 registry 等待；保留测试、扫描和发布身份门禁，以真实新 revision 与热缓存对照验收。
---

# 构建流水线调优

目标是缩短可信 source revision 进入流水线到约定完成点的完整墙钟。阈值来自当前任务；历史案例的40分钟不是其他工程的默认SLO。通过一次只改一个主要变量的对照决定是否保留优化。

## 按问题读取

- 定义时间、资源与证据口径：[measurement-contract.md](references/measurement-contract.md)。
- 判断瓶颈优先级、CPU/调度或托管平台迁移：[optimization-playbook.md](references/optimization-playbook.md)。
- 测试/fixture/数据库/Temporal慢，或准备并行测试：[integration-testing.md](references/integration-testing.md)。
- 缓存分层、预装工具、镜像复制或并发取消：[runner-image-cache.md](references/runner-image-cache.md)。
- 需要完整执行案例、失败修正和决策依据：[case-study-videoagentteam.md](references/case-study-videoagentteam.md)。案例含已冻结证据，不是当前基础设施配置。

## 1. 固定范围与完成点

记录当前仓库/WIP、主线完整revision、构建context、CI入口、Runner实际imageID和资源、发布入口及各自owner。跨仓配置按现场值读取，不从最近使用的checkout推断当前项目。

将代码/CI配置、Runner或集群资源、镜像复制、产品部署的授权范围分开记录；已有覆盖当前动作的授权直接沿用。没有产品发布授权时保留 `product_image_refs_mutated=false`，快照生产镜像引用并在最后比较。

冻结保留门禁：测试集合/断言/coverage、锁文件、类型/格式、迁移、扫描、组件smoke、source/digest绑定及独立读取。完成点若只到制品回执，不得报告产品已经上线。

## 2. 先测量，再修改

先获取一个真实通过的完整参考run；失败run可用于根因分析，不能作为通过样本。测量改动先跑一条窄的真实CI路径，确认插件导入、日志持久化与失败退出再跑全套，避免本机环境掩盖Runner差异。

分别采集workflow创建/排队/job/step与receipt时间；测试setup/call/teardown及fixture明细；CPU/throttle/RSS/I/O等待；缓存命中、下载和保存；run/attempt/source/制品摘要。共享节点负载、采样缺口与诊断任务重叠必须标注。

已有完整时间线时使用技能目录下的脚本（安装路径由当前宿主确定）：

```bash
python <skill-dir>/scripts/analyze_timeline.py timeline.tsv --format json --require-passed
python <skill-dir>/scripts/compare_test_runs.py baseline-tests.tsv db-tests.tsv serial-tests.tsv --require-preserved
```

比较器只检查清单/结果和阶段工作量，不能证明断言、覆盖率或发布门禁保留。fixture是测试阶段的子集，worker副本也不能与master汇总再次累加。

## 3. 按瓶颈走分支

| 证据 | 先验证的假设 |
|---|---|
| 测试setup/teardown很慢、CPU低、数据库sync等待高 | 临时库初始化/克隆/清理的存储成本；先查测试持久性合同，再评估受限临时内存卷 |
| 测试超时但队列已唯一 | 检查下载、I/O、外部服务等待和资源竞争，不能直接断言“worker互抢” |
| 大部分时间在工具/依赖下载或缓存保存 | 确認预装工具被实际使用，并比较缓存恢复+保存与重新下载成本 |
| 源码变动就重装所有依赖 | 调整COPY/ARG顺序、安装ownership、cache scope和构建context |
| 多组件串行且资源有余量 | 隔离输出后试验并行，全部join成功才允许回执 |
| 持续CPU饱和或throttle高 | 固定其他变量后做CPU档位对照 |
| 排队或registry控制面耗时主导 | 分拆调度、轮询与实际传输，再选择对应优化 |

不得通过删除测试、降低coverage、缩短超时掩盖失败、关闭事务/安全设置、使用mutable tag或绕过digest读取取得速度。

## 4. 可归因实验与恢复

每个实验记录假设、主要变量、固定source、配置差异、缓存状态、并发负载、各gate、完整墙钟和回滚入口。允许预先准备后续候选，但不要在当前基线运行中改变它的输入或环境；如果构建器要求远端主线保持exact SHA，也不能提前推进主线。

比较同revision的串行/并行时，同时拆job与step：独立工具下载变慢不能全归因于并行。缓存或资源状态无法固定时说明局限；多轮才可估计中位数/分位数。没有证明收益的选项保留原默认或撤销；不要为已写代码寻找必须启用的理由。

异步实现需证明：任一分支失败/缺结果阻断receipt；独立日志和元数据可定位组件；一次或连续取消均有界清理进程树和临时资源。重跑必须是授权内、无新增副作用的CI；付费生成、迁移或部署不能套用“自动重试构建”的规则。

## 5. 正式验收与收口

在最终配置下运行自然新revision和同revision热缓存完整入口，记录所有项目实际需要的gate：source物化、全测试、组件构建/smoke、registry push/scan、目标复制、各digest独立pull、source/context/digest对应、最终回执和cleanup。无需复制的项目不人为增设复制链路。

独立拉取检查用最终非root身份验证包导入、版本、必需静态文件/CLI，而不只检查镜像存在。结果保存实际命令语义、输出、退出码和imageID；按测试合同避免触发业务写入。校验索引引用、未被gitignore吞掉的证据文件与manifest。

同步项目文档和当前规格；完成或撤销候选后清理临时Pod、采样进程、导出文件与临时凭据。核对生产引用不变及工作区WIP。提交/推送/发布按当前任务授权执行，文档回执提交与已验证制品source分别报告。

## 6. 输出结果

给出自然新revision、同revision热缓存的完整墙钟，基线run与差值；再列阶段/并发关系、测试集合和coverage、关键资源与缓存证据、制品/回执、保留与撤销的方案。区分首次缓存建立和热命中、实测和预测、制品就绪和产品上线。

不要把预测值写成实测值。未在最终配置跑过自然新revision时明确写“未直接测量”；单轮结果不声称P95/P99。优化任务本身的调查与多轮验收用时也不能算成一次日常流水线耗时。
