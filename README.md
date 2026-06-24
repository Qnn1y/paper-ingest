# paper-ingest

> 一个 Claude Code skill：丢一个论文链接 / 标题 / 公众号文章 → 自动**下载 PDF → 提取全文精读 → 分类 → 入 Zotero → 写 Obsidian 精读笔记**。让每天刷到的论文真正"读进去、查得到"。

## 它解决什么问题

研究者每天刷到大量论文（arXiv / 公众号 / 知乎），但：
- 收藏了不读，读完没笔记，笔记找不到
- Zotero 库越堆越乱，分类靠手动拖
- 公众号解读和论文原文对不上

`paper-ingest` 把"链接 → 吸收"这条路打通：**自动分析归类 + 全文精读笔记 + Zotero 规范入库 + Obsidian 索引**。

## 核心能力

- 🔗 **多种输入**：arXiv/DOI 链接、纯论文标题、公众号/知乎链接
- 📖 **PDF 精读**（不是摘要复述）：下载 PDF → 提取全文 → 8 字段深度笔记（问题/贡献/方法详解/实验/细节/局限/我的思考）
- 🗂️ **自动分类**：按你的 Zotero collection 结构归类（默认 30 分类：SAR/超分/复原/扩散/基础方法）
- 📚 **Zotero 自动入库**：pyzotero 建条目 + 归类 + 查重；**PDF 挂载走 WebDAV 坚果云**（不撞 zotero.org 300MB 配额，见下）
- 📝 **Obsidian 笔记**：frontmatter 带 `category`，Dataview 自动索引
- 🌐 **公众号智能分流**：识别解读的是哪篇论文 → 论文入 Zotero + 解读笔记关联 `[[论文]]`
- ✅ **确认检查点**：入库前展示分类决策让你确认（防误归类）

## 安装（5 步）

```bash
# 1. 克隆到 Claude Code 的 skills 目录
git clone https://github.com/Qnn1y/paper-ingest.git ~/.claude/skills/paper-ingest
# Windows: C:\Users\<你>\.claude\skills\paper-ingest

# 2. 装 Python 依赖
pip install pyzotero pymupdf

# 3. 配置（复制模板，填你自己的值）
cd ~/.claude/skills/paper-ingest
cp config.example.json config.json
# 编辑 config.json：填 Zotero userID/API key + 你的 Obsidian vault 路径

# 4. Zotero 准备
#    - 注册 zotero.org 账号，桌面端登录开启同步
#    - zotero.org → Settings → API Keys → Create（勾 library/notes/write/file upload）
#    - 建你想要的 collection 分类（或用默认 30 分类，见 references/classification.md）

# 5. Obsidian 准备
#    - 装 Dataview 插件（设置→第三方插件→浏览→Dataview）
#    - vault 里建 config.json 配的目录（默认 01-Papers/ 06-Notes/ 00-Dashboard/，可自定义）
#    - 把 templates/dashboard.md 复制到你的 dashboard 目录
```

## 配置说明（config.json）

```json
{
  "library_id": "你的 Zotero userID（数字）",
  "library_type": "user",
  "api_key": "你的 Zotero API key",
  "vault_dir": "/path/to/your/obsidian/vault",
  "papers_subdir": "01-Papers",
  "notes_subdir": "06-Notes",
  "dashboard_subdir": "00-Dashboard",
  "storage_dir": "/path/to/pdf/storage"
}
```

> `config.json` 已被 `.gitignore` 排除，API key 不会进 git。Obsidian 子目录名可任意改，不强制 `01-Papers` 这种命名。

## 使用

装好后，在 Claude Code 里直接：

```
读这篇 https://arxiv.org/abs/2307.12348
存一下 "FaithDiff"
这篇公众号解读收一下 https://mp.weixin.qq.com/s/xxx
```

Claude 会自动触发 skill，走完整流程，关键分类决策前会让你确认。

## PDF 同步（坚果云 WebDAV）

> ⚠️ **关键设计**：PDF 挂载**不走 pyzotero**。因为 pyzotero 文件上传只能走 zotero.org 服务器存储（有 300MB 配额），而用户的 PDF 同步主力是**坚果云 WebDAV**。pyzotero 不支持 WebDAV，直接挂会把 zotero.org 配额撑爆（且留下「幽灵附件」——附件条目建了但文件没传上去）。

**本 skill 的做法**：
1. 入库时，PDF 路径累积到 `pending_attachments.json`（不入 zotero.org）
2. 自动生成 `attach_pending.js`（Zotero Run JavaScript 脚本）
3. **你在 Zotero 客户端跑一次 `attach_pending.js`** → `importFromFile` 走客户端配置的 WebDAV 上传到坚果云（不占 zotero.org 配额）
4. 挂载成功的条目，下次生成 JS 时自动从 pending 剔除（用 `md5` 字段判断真挂载，能识别并跳过幽灵附件）

**前提**：Zotero 客户端「编辑 → 首选项 → 同步 → 文件同步」选 **WebDAV** 并填好坚果云地址（不是 zotero.org）。

**操作**：
```
Zotero → 工具 → 开发者 → Run JavaScript
粘贴 <skill目录>/attach_pending.js 的内容 → Run
跑完点右上角「同步」
```

> 期刊论文（IEEE/Elsevier 等无 arXiv 版的）PDF 需自行下载后，手动在 Zotero 拖入条目即可（同样走 WebDAV）。

## 自定义

- **分类规则**：改 `scripts/classify.py` 的 `classify()` 函数（判定逻辑在 `references/classification.md` 详解）
- **笔记模板**：改 `scripts/obsidian_note.py` 的 `build_note()`（章节结构）
- **Dashboard 查询**：改 `templates/dashboard.md` 的 Dataview 语句

## 目录结构

```
paper-ingest/
├── SKILL.md                  # skill 入口（Claude 读取的指令）
├── README.md
├── config.example.json       # 配置模板（复制为 config.json）
├── .gitignore                # 排除 config.json（含 API key）
├── pending_attachments.json  # 待挂 PDF 列表（自动生成，gitignore）
├── attach_pending.js         # Zotero Run JavaScript 挂 PDF（自动生成）
├── scripts/
│   ├── _common.py            # 配置加载 + pyzotero/arXiv/S2 客户端
│   ├── resolve_meta.py       # URL/标题/DOI → 元数据
│   ├── extract_text.py       # PDF → 全文文本（精读用）
│   ├── classify.py           # 分类规则
│   ├── zotero_push.py        # Zotero 入库 + 归类 + 查重（PDF 累积 pending → WebDAV）
│   └── obsidian_note.py      # 渲染精读笔记
├── references/
│   └── classification.md     # 30 分类判定详解
├── templates/
│   ├── paper.md              # 精读笔记模板
│   └── dashboard.md          # Dataview 索引看板模板
└── examples/
    └── fill_diffusion_pdfs.py  # 批量补 PDF 示例
```

## 设计借鉴

- [Anthropic Skill 最佳实践](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)：progressive disclosure、plan-validate-execute、预制脚本
- [academic-research-skills](https://github.com/Imbad0202/academic-research-skills)：多 mode 路由、确认检查点、查重保护
- [AI-Research-SKILLs](https://github.com/Orchestra-Research/AI-Research-SKILLs)：scripts/ 预制 + references/ 分离

## License

MIT
