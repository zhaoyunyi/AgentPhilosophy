# 案例：VideoAgentTeam 完整构建优化

日期：2026-09-09。此页保留当时已完成的诊断过程和数字，帮助选择实验；不把工程名、工具版本、容量或耗时作为其他项目配置。

## 合同与证据入口

用户设定从workflow创建到最终制品回执低于40分钟，保留全部测试、coverage、扫描和source/digest校验；不部署生产，不提交付费生成。

业务源码/CI在VideoAgentTeam；Runner和运行配置由RunIDC维护。现场先确认当前checkout、WIP、实际Runner镜像与资源，避免把中央模板当成已经生效的配置。最终制品source为`d2c5d1cc13524ff83a4efd52ef09fd60eb32c3e0`，版本2.1.2。

完整项目证据：[性能报告](https://github.com/zhaoyunyi/VideoAgentTeam/blob/d92afb1c8299/docs/development/ci-performance.md)、[证据索引](https://github.com/zhaoyunyi/VideoAgentTeam/blob/d92afb1c8299/docs/development/evidence/ci-performance/README.md)。以下run链接用于追溯，不需要访问生产环境。

## 从测试慢追到存储等待

原成功参考run [34310963476](https://github.com/zhaoyunyi/VideoAgentTeam/actions/runs/34310963476)完整3364秒（56分04秒），集成测试2142.30秒；unit/BDD不足一分钟。直接增加集成worker的尝试曾出现Temporal与wheel安装超时，不能单据此认定队列互抢。

先推只有计时的基线。首次插件加载失败，因为本机`python -m pytest`与CI的脚本入口导入路径不同；修正后窄入口验证，再完成串行计时。run [34319645443](https://github.com/zhaoyunyi/VideoAgentTeam/actions/runs/34319645443)记录212通过、1次wheel安装超时、4跳过，用于分析但不列为通过基线。

计时发现模板初始化208.75秒，CPU仅1.78秒；临时库只有约13MB，PostgreSQL反复等待DataFileImmediateSync/WALSync，节点系统盘位于RAID1。现场CPU不忙。于是只调整CI两个临时数据卷的介质，并提高内存记账上限；不改变源码、串行方式、工具镜像和CPU限额，保留fsync/同步提交/full-page writes。

同source临时卷对照run [34323152497](https://github.com/zhaoyunyi/VideoAgentTeam/actions/runs/34323152497)：

| 项目 | 磁盘取证秒 | Memory对照秒 |
|---|---:|---:|
| 测试setup合计 | 453.88 | 24.62 |
| 测试call合计 | 940.57 | 114.21 |
| 测试teardown合计 | 329.53 | 6.56 |
| 模板fixture（setup子集） | 208.75 | 2.32 |
| 完整Temporal流程（call子集） | 220.61 | 5.49 |

集成测试148.38秒、213通过/4跳过，完整工作流954秒（15分54秒）。同148次checkpoint累计write/sync约193秒→0.5秒。现场证据支持保留CI临时卷优化；不是生产持久性或宿主断电恢复证明，也不是多轮P95。

## 后续优化与实际踩坑

- 全217项分为202数据库组和15串行组（11通过、4既有paid opt-in跳过）；比对ID并集相同，无重复。每用例UUID库、每worker迁移模板，所有真实Temporal/paid入口串行。清理不越本轮资源。
- wheel使用锁定且带hash的运行依赖，再安装本次wheel并跑依赖及任意cwd迁移检查，避免每次解析浮动版本。
- Docker先建Python依赖层，再复制源码。审查发现后续递归chown会copy-up整套依赖，改为最终UID创建及COPY ownership；版本ARG后置，精简context，固定基础digest。
- Runner已有预装Dockerfile却没有采用。镜像切换后，硬编码HOME/PATH又使两项探测测试失败；修复成遵循调用方环境，不能拿本机绿测代替新Runner验收。
- 跨项目基础镜像pull被拒绝；没有扩CI机器人权限，而是从已确认digest的节点缓存导出，再复制到CI已有权限的项目，校验digest一致并清理凭据/临时文件。
- 预装uv后补回下载缓存。首次78MB缓存上传约5分钟，热恢复约48秒且不重复保存；Temporal测试服务还有单次下载波动，单独归因。
- 并行监督器经过组件失败、连续取消、进程组清理和独立日志测试后才进入正式对照；失败不能产生成功回执。

## 最终三轮与保留决策

| 最终相同source | 完整秒 | 验证job秒 | 构建job秒 |
|---|---:|---:|---:|
| 新revision [34327794237](https://github.com/zhaoyunyi/VideoAgentTeam/actions/runs/34327794237) | 2185 | 874 | 1236 |
| 串行热缓存 [34331268731](https://github.com/zhaoyunyi/VideoAgentTeam/actions/runs/34331268731) | 677 | 440 | 156 |
| 并行热缓存 [34332387824](https://github.com/zhaoyunyi/VideoAgentTeam/actions/runs/34332387824) | 668 | 336 | 253 |

全部1455项unit/BDD通过，213项integration通过、4项按原条件跳过，coverage80.59%（门槛80%）；扫描、source/digest及独立回执读取保留。最终三轮App/Auth digest相同，非root独立pull检查包、版本、静态文件和迁移入口通过。

并行job多97秒，其中66秒来自ORAS下载，实际构建/扫描/回执step132→160秒。总时间仅少9秒，单轮未证明并行收益，继续默认串行。不能把全部97秒归因于磁盘或并行。

新revision36分25秒、热缓存11分17秒均低于当前任务阈值；没有将不同run最快阶段拼成一轮。报告保留失败样本、首次层重建成本、共享节点负载与诊断重叠局限。最后停止采样、清理临时Pod/凭据、校验证据索引和manifest、合并当前规格；生产五个Deployment引用不变。已验收制品source与后续文档回执提交分别记录。
