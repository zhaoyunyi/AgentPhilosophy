# Out-of-scope 知识库

被明确拒绝的 enhancement 保存到 `docs/agents/out-of-scope/<concept>.md`，一项领域概念一个文件，而不是一个 issue 一个文件。

每个文件记录：

- 概念和用户需求。
- 拒绝日期、原因和适用边界。
- 相关 ADR/spec/issue 链接。
- 历次重复请求。
- 什么事实变化后值得重新考虑。

triage 开始时读取该目录。命中相似请求后让维护者选择：确认沿用、因前提变化而重开、或判断为不同概念。已实现的功能、被拒绝的 bug 和临时延期不写入该知识库。

新增或删除这些长期文档时同步更新 `docs/README.md` 或 `docs/agents/README.md`（若项目采用后者）。
