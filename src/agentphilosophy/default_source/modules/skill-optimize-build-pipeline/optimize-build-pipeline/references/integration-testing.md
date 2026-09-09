# 集成测试：从等待证据到隔离并行

## 目录

1. 找到慢在哪里
2. 计时插件的行为合同
3. 临时数据库存储选择
4. 测试资源与分组
5. 依赖安装和测试服务下载
6. 比较测试清单

## 1. 找到慢在哪里

先分解每个用例的setup/call/teardown，再按fixture名称、scope和具体调用累计耗时。fixture初始化和清理属于测试阶段，不是可以额外相加的一条流水线。报“模板库耗时”要保留具体fixture记录，报“checkpoint耗时”要保留计数器名、单位、Pod/进程身份及采样窗口。

| 观察 | 进一步取证 | 决策约束 |
|---|---|---|
| 模板初始化墙钟大、进程CPU很小 | 子进程CPU、数据库wait event、I/O PSI、volume实际介质 | 不先增加worker或CPU |
| 每次建库/删库都有同步等待 | 数据库克隆策略、checkpoint write/sync计数、每库容量 | 保留隔离，检查是不是反复落盘 |
| Temporal/外部测试服务偶发超时 | 子进程是否已启动、服务下载、网络与服务端状态 | 队列唯一不等于资源无竞争 |
| wheel/SDK安装超时 | 是否重复解析浮动依赖、缓存是否匹配锁文件 | 不通过延长超时把错误依赖路径固化 |

PostgreSQL可只读查询`pg_stat_activity.wait_event_type/wait_event`及当前版本支持的checkpoint统计视图。`WALSync`、`DataFileImmediateSync`与高I/O等待是诊断证据，不单独证明存储变更一定有效。累计毫秒只比较对应进程/Pod的计数范围；数据库版本不同可能有视图差异，先检查现场schema。

## 2. 计时插件的行为合同

优先采用框架已有durations、JUnit、fixture或trace能力。需要插件时先用一条窄CI命令证明：

- 使用与正式入口相同的解释器、cwd和导入路径；pytest预加载本仓插件时，`python -m pytest`可避免脚本入口过早加载而找不到本仓模块。
- 成功、断言失败、setup失败、teardown失败和worker崩溃仍保留原有退出状态。数据缺失不得被写成耗时0或成功。
- setup/teardown计时不改变fixture scope、finalizer顺序、重试次数或超时。包装yield fixture或LIFO finalizer时，测试原有清理仍执行，异常也会被框架报告。
- xdist的异常worker可能没有`workeroutput`；安全读取且保留原始崩溃，不制造新的INTERNALERROR。正常worker向master上报时，master汇总是唯一统计入口，worker文件只用于排障。
- 临时Runner回收前保存脱敏证据；日志导出失败、文件未上传或引用被gitignore排除都属于缺证据。避免把连接串、fixture参数和完整环境写入计时记录。

框架版本升级后复测这些行为；不要将一个项目的pytest插件原样复制到不使用pytest的工程。

## 3. 临时数据库存储选择

只在**可丢弃、每轮独立的CI测试数据**上评估内存临时卷，并同时满足：

1. 持久性合同只要求当前测试进程/服务重启后恢复，不要求Pod删除、宿主重启或断电后数据保留。
2. 现场证据显示磁盘等待位于关键路径；已量模板、峰值并发库与服务内存。
3. 卷有容量界限，容器memory limit计入tmpfs占用；请求/限额/namespace quota与节点余量都能承受并发，峰值不能只按空库估算。
4. 各Pod/worker不共享可写库，清理只作用于本轮精确资源；旧配置和回滚入口可恢复。

例如Kubernetes的`emptyDir.medium: Memory`可能适合这类测试。容量和memory limit由工程测量决定，不能照搬某案例的1Gi/2Gi。修改后回读实际挂载、峰值内存和数据库事务设置，再用同源码原有测试验证。

不关闭fsync、同步提交或其他数据正确性设置换速度。若测试目标是持久卷恢复、Pod重建或宿主断电耐久性，使用符合该目标的持久介质，不能用tmpfs替代。生产数据库迁移、存储重建和内存卷切换不属于这一CI实验。

## 4. 测试资源与分组

先检查已有隔离是否真实有效，避免把资源饥饿误称为对象冲突。并行前清点数据库/namespace/task queue、端口、临时目录、环境变量及进程内全局状态。

- 数据库可采用每worker一次真实迁移模板、每用例UUID克隆；空库迁移测试仍从真正空库运行，不能拿模板替换被测迁移。
- 先前后快照验证不同用例不会读写彼此数据，结束后只清理本轮ID；不以共享TRUNCATE、全库drop或通配清理支持并行。
- 持有共享服务、全局状态或具有外部副作用的测试应留在明确串行组，或获得真正独立服务后再并行。真实Temporal和paid opt-in也需要清点，不能因为普通CI里默认skip就漏出分组边界。
- `workers=2`只是可供试验的档位。独立数据库组可以并行，串行服务组在其worker退出后执行；失败组仍按合同收集结果，但任何失败/缺结果都阻断最终成功。
- 比较全量用例ID与分组并集，检查交集为空；新增测试单列。断言、fixture scope、覆盖率和原有skip条件还要独立review，数量相同不能代替行为相同。

并行监督需要独立日志、退出状态和结果文件；连续取消也要有界终止进程树。用barrier证明重叠比断言两个进程必须在250毫秒内启动更稳健。

## 5. 依赖安装和测试服务下载

独立wheel/SDK验收应使用项目锁定的运行依赖，再安装本次构建的包；安装后跑依赖一致性检查，并从任意cwd验证目标入口。避免每次新venv从宽松版本范围重新解析整个依赖图。

Python/uv示例（采用前核对当前CLI支持）：

```bash
uv export --frozen --no-dev --no-emit-project --output-file runtime-requirements.txt
uv pip install --python <venv-python> --require-hashes -r runtime-requirements.txt
uv pip install --python <venv-python> --no-deps <built-wheel>
uv pip check --python <venv-python>
```

测试框架自动下载服务二进制时，把下载与服务执行分开计时。重复下载占主要成本才考虑固定版本预装/缓存；安装后的真实服务测试仍保留，不用fake服务代替。

## 6. 比较测试清单

标准库脚本`../scripts/compare_test_runs.py`接受一个基线TSV和一个或多个**互不重叠的候选分组**：

```text
nodeid\tsetup_seconds\tcall_seconds\tteardown_seconds\toutcome
```

每行唯一nodeid，outcome为passed/failed/error/skipped，耗时为有限非负秒数。其它框架的xfail/xpass要按该项目门禁显式映射，不将unexpected pass/failure默认为通过。

```bash
python <skill-dir>/scripts/compare_test_runs.py before.tsv db.tsv serial.tsv --require-preserved
```

退出0表示候选保留全部基线ID、没有新skip/失败，允许新增通过用例；退出1表示保留门禁未满足；退出2表示格式/重复ID等无效输入。输出的`phase_work_seconds`是工作量，不是并发后的墙钟；测试通过仍不替代完整发布验收。
