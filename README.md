# 精选 Codex 插件（中文）

这是 [Awesome Codex Plugins](https://github.com/hashgraph-online/awesome-codex-plugins) 的社区中文 fork。它保留上游插件的 ID、版本、安装路径、代码和许可证，只本地化面向用户的展示信息。

## 在 Codex 中添加

```powershell
codex plugin marketplace add `
  'https://github.com/jiusimeng8-cmd/awesome-codex-plugins-zh.git' `
  --ref 'main' `
  --sparse '.agents/plugins' `
  --sparse 'plugins'
```

随后在 Codex 的 Plugins 页面选择 `awesome-codex-plugins-zh`，或执行：

```powershell
codex plugin list --source awesome-codex-plugins-zh
```

## 已中文化的内容

- 市场标题、分类、196 个插件的名称和简介。
- `plugins.json` 中的插件简介与分类。
- 已收录插件的 `.codex-plugin/plugin.json`：简介、显示名称、短介绍、长介绍和示例提示。
- Skill 卡片的 `agents/openai.yaml`：显示名称、短介绍和默认提示。

这些字段会直接影响 Codex 桌面版的插件列表与详情页。品牌、插件 ID、版本、作者、URL、安装策略、源路径和代码保持原样，以保证搜索、安装和上游同步稳定。

## 尚在翻译的内容

仓库同时镜像了大量上游正文文档，包括插件 README、`SKILL.md` 和参考资料。它们并非插件市场 UI 的展示元数据，当前仍主要保留英文原文；不要把“市场和详情已中文化”误认为“全部技术文档已完成翻译”。

我们会在保持代码块、命令、路径、稳定标识符和运行语义不变的前提下，逐步补充中文文档。欢迎通过 Issue 或 PR 修正术语和认领文档翻译。

## 上游与许可证

- 上游仓库：[hashgraph-online/awesome-codex-plugins](https://github.com/hashgraph-online/awesome-codex-plugins)
- 上游英文说明：[README（上游）](https://github.com/hashgraph-online/awesome-codex-plugins/blob/main/README.md)
- 本仓库沿用上游 Apache-2.0 许可；各插件目录中的原始许可证同样保留并优先适用。
