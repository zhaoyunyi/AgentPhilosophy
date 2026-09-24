## 五、Superpowers 显式可选合同

`superpowers-system` 是显式可选模块，默认 preset 不包含它。当前中央说明参考 Superpowers `6.4.1`、提交 `5bf4e78011075bcfc0dc295f0724994cd123ee71`；上游 Codex 安装入口为插件市场。模块只生成项目说明，不安装插件、不复制上游仓库，也不证明本机已经安装。

只有用户明确点名 Superpowers、superpowers-cn 或其所属的具体技能时才进入流程。安装/发现技能不等于本轮启用；既有任务授权直接沿用，宿主规则和项目 jj 约定优先。

已有项目的模块列表仍显式冻结。确实需要说明时追加模块，再走中央/目标 validate、dry-run、apply 和 status。启用前核对实际渠道、位置和版本；不要因旧文档提及 `~/.agents/skills/superpowers` 自动创建全局入口。已有 `~/.codex/superpowers` clone 也不等于发现入口可用。

来源：[上游安装说明](https://github.com/obra/superpowers/blob/v6.4.1/README.md#codex-app)、[调用优先级](https://github.com/obra/superpowers/blob/v6.4.1/skills/using-superpowers/SKILL.md)。
