# 正文翻译规则

`translations/docs/` 是插件正文的中文覆盖层。每个文件与仓库根目录下的目标文档保持相同相对路径，例如：

```text
translations/docs/plugins/example/plugin/README.md
→ plugins/example/plugin/README.md
```

同步工作流先拉取上游原文，再应用这里的中文覆盖层。

翻译必须遵守：

- 翻译自然语言正文、标题、表格说明和注释。
- 原样保留代码块、命令、文件路径、URL、JSON/YAML 键、环境变量、插件 ID、版本号和许可证文本。
- 不调整文档结构，不删除安全说明、限制条件或署名。
- 遇到品牌和技术术语时保留原名称，并用中文说明用途。
