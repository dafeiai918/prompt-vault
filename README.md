# prompt-vault · 提示词模板库

**好用的提示词别再丢在备忘录里。** 本地存、能搜索、带变量、一键复制到剪贴板。

零依赖 · 单文件 · 中文 · 内置 12 个实用模板

---

## 解决什么

- 提示词散落在微信收藏 / 备忘录 / 聊天记录里，用的时候找不到
- 每次都要手动改几个地方（改成英文、改字数、换产品名）
- 想分享给同事，只能一段段复制

---

## 快速开始

```bash
# 1. 初始化（写入 12 个内置模板）
python prompt_vault.py init

# 2. 看看有什么
python prompt_vault.py list

# 3. 填充变量并复制到剪贴板
python prompt_vault.py render p001 -s "内容=今天天气很好，适合出门。" --copy
# → 已复制到剪贴板，直接粘到任意 AI 客户端

# 4. 加自己的模板
python prompt_vault.py add -t "合同风险审查" -c "审查下面合同的{{风险类型}}风险：\n\n{{合同}}" -g 法律,职场
```

---

## 内置模板

| ID | 标题 | 变量 |
|---|---|---|
| p001 | 翻译成英文 | 内容 |
| p002 | 中文润色 | 内容 |
| p003 | 长文总结 | 要点数、内容 |
| p004 | 周报生成 | 工作记录 |
| p005 | 邮件回复 | 语气、原邮件 |
| p006 | 代码解释 | 语言、代码 |
| p007 | 代码重构 | 语言、目标、代码 |
| p008 | SQL 生成 | 数据库、需求、表结构 |
| p009 | 会议纪要 | 会议记录 |
| p010 | 检查错别字 | 内容 |
| p011 | 小红书文案 | 产品、卖点 |
| p012 | 角色扮演面试官 | 岗位 |

---

## 命令一览

| 命令 | 说明 |
|---|---|
| `init` | 初始化并写入内置模板 |
| `add -t 标题 -c 内容 -g 标签` | 添加（`-c -` 可从标准输入读） |
| `list [关键词] [-g 标签]` | 列出 / 搜索 |
| `show ID` | 查看完整内容与变量 |
| `render ID -s "变量=值" --copy` | 填充变量 / 复制 |
| `edit ID [-t/-c/-g]` | 修改 |
| `remove ID` | 删除 |
| `tags` | 标签统计 |
| `export -o 文件.json` | 导出分享 |
| `import -f 文件.json` | 导入 |

ID 可以只写前缀，也可以直接写标题的一部分（`render 翻译`）。

---

## 变量语法

用 `{{变量名}}` 占位：

```bash
python prompt_vault.py add -t "改写语气" -c "把下面内容改写成{{语气}}语气：\n\n{{内容}}"
python prompt_vault.py render 改写语气 -s "语气=正式" -s "内容=这活儿干得漂亮" --copy
```

- 未填的变量保留原样输出（不会报错）
- 但加了 `--copy` 时，缺变量会拒绝复制并提示，避免误发半成品

---

## 分享模板包

```bash
# 导出
python prompt_vault.py export -o 我的提示词.json

# 对方导入（重名的会自动跳过）
python prompt_vault.py import -f 我的提示词.json
```

---

## 剪贴板支持

| 平台 | 方式 |
|---|---|
| Windows | tkinter → PowerShell `Set-Clipboard` 兜底 |
| macOS | `pbcopy` |
| Linux | `xclip` |

复制失败会自动改为打印内容，不影响使用。

---

## 数据位置

- `~/.prompt-vault/vault.json` — 全部本地，不上传任何地方
- 纯 JSON，可以直接用编辑器改，也可以放 git 里同步

---

## 相关项目

| 项目 | 用途 |
|---|---|
| [OneClickRelay](https://github.com/dafeiai918/oneclickrelay) | 一键把中转站写进 60+ 客户端 |
| [relay-converter](https://github.com/dafeiai918/relay-converter) | 一份配置转 19 种客户端格式 |
| [awesome-relay](https://github.com/dafeiai918/awesome-relay) | 中转站与客户端精选导航 |

---

## License

MIT
