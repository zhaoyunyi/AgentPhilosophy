# AgentPhilosophy 发布说明索引

本目录长期保存正式版本的发布说明，并与 `dist/`、`build/` 等临时构建产物分开管理。每个正式版本使用 `v<MAJOR>.<MINOR>.<PATCH>.md` 命名；项目已有更严格版本方案时，文件名跟随该方案并在本索引中说明。

## 单版本说明要求

每份发布说明至少包含：

- 变更摘要；
- 兼容性与迁移；
- 验证结果；
- 回滚入口；
- 验证与发布回执。

发布说明必须区分“已实现”“已验证”“候选环境可用”和“已正式发布”，不能用测试、构建或 Ready 状态替代目标平台的真实发布回执。

## 版本列表

项目版本条目通过 layered custom 源维护。默认路径为 `.agents/custom/release-notes/README.custom.md`；如果项目自定义了 `paths.custom_dir`，以 `.agents/custom/release-notes/README.custom.md` 为准。修改 custom 源后运行 AgentPhilosophy 同步刷新本文件。

<!-- release-notes:start -->
- [v1.2.2](v1.2.2.md)：发布候选，完整 LLM 技能安装与使用指南
- [v1.2.1](v1.2.1.md)：已发布，Loop-Check 与配置指引修复
- [v1.2.0](v1.2.0.md)：未单独发布，内容已纳入 1.2.1
- [v1.1.0](v1.1.0.md)：已发布，目标重述与可选 UI/UX Loop 技能
- [v1.0.0](v1.0.0.md)：已发布，Matt 非兼容更新与固定提交制品回执
- [v0.13.0](v0.13.0.md)：已发布，含外部 skill 依赖升级与制品回执
- [v0.12.0](v0.12.0.md)：已发布，含制品回执与远端 CI 账户阻断说明
- [v0.11.0](v0.11.0.md)：已发布，含源码与制品回执
- [v0.10.0](v0.10.0.md)
- [v0.9.0](v0.9.0.md)
- [v0.8.0](v0.8.0.md)
- [v0.7.16](v0.7.16.md)
<!-- release-notes:end -->

## AgentPhilosophy 发布工具

- `scripts/prepare-release.sh` 生成对应版本说明并更新本索引；重复执行不会生成重复条目。
- `scripts/publish-release.sh` 使用对应版本说明创建 GitHub Release，确保仓库归档与对外说明一致。
- `v0.7.15` 及更早版本沿用旧流程，历史说明以对应的 GitHub Release 为准；本目录从后续版本开始持续归档。
