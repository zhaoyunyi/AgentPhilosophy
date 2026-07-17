---
name: wayfinder
description: 把超过单个 agent 会话、路径仍模糊的巨大工作规划成共享决策地图，并逐票消除未知直到路线清晰。
disable-model-invocation: true
---

# Wayfinder

改编自 Matt Pocock 的 `wayfinder` skill（MIT License）：https://github.com/mattpocock/skills/tree/HEAD/skills/engineering/wayfinder

Wayfinder 默认只规划：每张票解决一个决策，地图完成表示“已知道如何到达终点”，不是已经交付终点。

先读取 `docs/agents/issue-tracker.md`；缺少时运行 `/setup-matt-pocock-skills`。tracker 中 map、子票、阻塞、frontier、claim 与 resolve 的物理实现以该文件为准。

## 地图

map 是唯一的低分辨率索引：

```markdown
## Destination
<路线清晰时应得到的 spec、决策或变化>

## Notes
<领域、长期偏好、每个会话应调用的 skills>

## Decisions so far
- [已关闭决策票名称](link) — 一行结论

## Not yet specified
<仍在迷雾中、现在还无法精确出票的问题>

## Out of scope
<明确越过 destination 的事项>
```

map 不复制票内细节。面向用户时始终用票名并包裹链接，不用裸编号代替含义。

## 决策票

- 每票只解决一个可在一个会话内回答的问题。
- 类型为 `research`、`prototype`、`grilling` 或 `task`。
- 使用 tracker 原生依赖；不可用时才用正文约定。
- frontier 是所有开放、未阻塞、未认领的子票。
- 会话的第一次写操作必须是 claim；除 research 外，一个会话只解决一票。
- HITL 票必须由用户亲自回答，agent 不代答；AFK 票可独立推进。

## 创建地图

1. 用 `/grilling` 与 `/domain-modeling` 明确 destination；它决定范围。
2. 广度优先扫描决策空间。若路线已可在单会话内说明，停止并建议普通主线。
3. 创建 map，把可精确描述的问题创建为子票；先创建再连接依赖。
4. 暂时不能精确出票的内容保留在 `Not yet specified`，不提前切碎迷雾。
5. 独立 research 票可按当前多 agent 规则并行交给 `/research`；写清目标、范围、产物和验收。
6. 创建阶段不顺手解决决策票。

## 推进地图

1. 加载 map，只按需展开相关票。
2. 选择用户点名的票，否则取 frontier 最前；先 claim。
3. 调用 Notes 指定的 skill 解决问题。
4. 把答案写入该票，关闭它，在 `Decisions so far` 增加上下文指针。
5. 根据新事实创建并连接新票、把已清晰的迷雾毕业成票、关闭已越过范围的票。

frontier 清空且 `Not yet specified` 为空时，把地图交给 `/to-spec`，再进入 `/to-tickets` 与 `/implement`。
