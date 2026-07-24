# 构建时间线与证据合同

## 目录

1. 时间口径
2. TSV schema
3. 采样合同
4. Cache 与 source 合同
5. Registry 与 receipt 合同
6. Evidence 目录

## 1. 时间口径

同时保留四个时间：

- `workflow_wall_seconds`：平台创建 workflow 到最终完成。
- `receipt_ready_seconds`：workflow 创建到最终可消费 refs receipt。
- `runner_job_seconds`：runner 真正开始到 job 完成。
- `stage_duration_seconds`：单阶段 start/end 差。

不要把 queue 排除后仍称为完整墙钟。不要把并行 stage 相加。平台 UI 的四舍五入时长只做交叉检查，正式证据使用 epoch 或带时区的原始时间戳。

## 2. TSV schema

第一行固定为：

```text
stage\tstart_epoch\tend_epoch\tlane\tcategory\tstatus
```

字段语义：

| 字段 | 规则 |
|---|---|
| `stage` | 当前文件内唯一、稳定、可读的阶段 ID |
| `start_epoch` | UTC epoch 秒，整数 |
| `end_epoch` | UTC epoch 秒，且不小于 start |
| `lane` | 并发执行面，例如 `ci`、`buildkit`、`controller` |
| `category` | `queue/source/test/build/registry/smoke/receipt/cleanup` 等 |
| `status` | 建议使用 `passed/failed/skipped` |

示例：

```text
stage\tstart_epoch\tend_epoch\tlane\tcategory\tstatus
runner-start\t100\t112\tformal\tqueue\tpassed
backend-build\t112\t132\tbuildkit\tbuild\tpassed
ci-wait\t132\t180\tcontroller\ttest\tpassed
registry-copy\t132\t156\tcontroller\tregistry\tpassed
digest-smoke\t156\t162\tcontroller\tsmoke\tpassed
receipt\t180\t181\tcontroller\treceipt\tpassed
```

分析器报告的 `concurrent_stage_seconds` 是重叠区间累计值，不等于任意方案必然节省的墙钟。关键路径仍要结合依赖关系解释。

## 3. 采样合同

优先用平台/内核已有指标，按 1～5 秒采样：

```bash
kubectl top node <node>
kubectl top pod -A --containers
kubectl get node <node> -o jsonpath='{.status.capacity.cpu}{" "}{.status.allocatable.cpu}{"\n"}'
```

有 Prometheus/cAdvisor 时记录：

- `container_cpu_usage_seconds_total` rate 与阶段峰值；
- `container_cpu_cfs_throttled_periods_total` / periods；
- `container_memory_rss`；
- `container_fs_reads_bytes_total`、`container_fs_writes_bytes_total`；
- 节点 CPU、memory available、disk latency/throughput、iowait；
- Pod Pending reason 与 namespace quota 已分配 request/limit。

采样窗口必须覆盖实际构建。若采样只覆盖热缓存空闲段，要在报告中说明，不能据此评价冷编译硬件。

CPU 判断：

- `request` 决定 scheduler 是否允许并发，不限制运行峰值；
- `limit` 与 CFS throttle 才能证明容器被 CPU cap；
- 节点核数高但 Pod request 总和过高，仍会 `Insufficient cpu`；
- 峰值高但平均低，通常要继续查依赖图、锁、网络、export 或短 burst。

## 4. Cache 与 source 合同

每个样本记录：

- 完整 source revision；
- build context hash 或明确 context 路径；
- runner image、toolchain、base image digest；
- dependency lockfile hash；
- cache cold/warm；
- cache namespace/ID、持久卷或目录；
- 是否发生外网下载；
- cache 命中后输出 digest 是否符合预期。

可信 source mirror 必须：

1. 只 materialize 请求的 exact revision；
2. 校验当前 HEAD 等于请求 revision；
3. 清除 mirror 自身 marker；
4. 验证工作树 clean；
5. 对不可信 PR 保持独立 runner/权限边界。

BuildKit cache mount 的 ID 至少考虑项目、组件、架构和 toolchain major。不要把 Secret、credential helper 状态或用户家目录整体作为共享 cache。

## 5. Registry 与 receipt 合同

拆分记录：

- replication trigger epoch；
- execution discovered epoch；
- task start/end；
- controller finished epoch；
- blob checks/skips/transfers/bytes；
- 每仓库 digest 与状态；
- 独立 pull Pod start/end/status。

`controller duration` 很长但 task 很短时，优先优化 execution 建立、轮询或控制面，而不是增加 BuildKit CPU。

最终 receipt 最少包含：

```text
source_revision
source_context_sha256 per component
ci_run_id / ci_status
builder / platform
component count
internal registry refs and digest
target registry refs and digest
scan and component smoke status
independent digest pull status
final_release_ready
local_build_used
product_image_refs_mutated
secret_values_recorded
phase timings
```

生成 receipt 前对产品 refs 做 before/after 对照。对 evidence 生成 manifest，并进行 secret scan；不得把 token、password、docker config 或原始 Authorization header写入证据。

## 6. Evidence 目录

建议每个 run 使用不可变目录：

```text
evidence/<UTC>-run-<id>/
├── identity.env
├── timeline.tsv
├── hardware-samples.tsv
├── cache.env
├── source-context.tsv
├── registry.tsv
├── result.env
├── refs.env
├── secret-boundary.env
└── manifest.sha256
```

在 `result.env` 中区分：`measured`、`counterfactual`、`estimated`。只有平台原始时间戳或当前 run receipt 支持的值才标 `measured`。
