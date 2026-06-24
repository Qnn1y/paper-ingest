---
name: paper-ingest
description: Ingests a research paper or web article into the user's knowledge base. Accepts an arXiv/DOI/venue URL, a paper title, or a WeChat/Zhihu/blog link. Analyzes the content, classifies it into the user's 30-collection Zotero structure (6 main + 24 sub: SAR研究/图像超分辨率/图像复原增强/扩散模型/基础与方法/待整理), pushes to Zotero via pyzotero, and writes an Obsidian note (one-line takeaway + abstract digest + core contributions + my thinking) that auto-indexes in the Dataview dashboard. Use when the user drops a paper/article link or title and wants it absorbed into their library, or says "读这篇/存一下/入库/归类这篇".
---

# paper-ingest

吸收论文/文章到知识库：分析→分类→Zotero→Obsidian笔记。目标是"有印象+查得到"。

## 触发与意图识别

用户输入可能是：
- **arXiv/DOI/会议论文 URL** → `quick` mode（论文，全流程）
- **纯论文标题**（如 "FaithDiff"）→ `title` mode（先反查元数据）
- **多个链接** → `batch` mode
- **公众号/知乎/博客 URL** → `web` mode（**智能分流**，见下）
- "重新分类这篇" → `reclassify` mode
- "更新论文索引/看板" → `dashboard` mode

意图模糊时默认 `quick`。

## web mode 智能分流（公众号/知乎多数是论文解读）

公众号/知乎文章抓取后，**先识别它解读的是哪篇论文**，再分流：

**Step 1**：用 web reader（mcp__web_reader__webReader）抓文章全文

**Step 2**：从文中提取 underlying 论文信号（按优先级）：
1. arXiv ID：正则 `\d{4}\.\d{4,5}`，或 `arxiv.org/abs/xxx` 链接
2. DOI：`10.xxxx/xxx`
3. 论文标题：文章标题/正文里的"《xxx》" / "xxx 论文精读" / 引号书名号包裹的英文标题

**Step 3 分流**：
- **识别到论文（多数情况）** → 该论文走 `quick` mode 全流程：
  - resolve_meta（用提取到的 arXiv ID / 标题）→ 入 Zotero + 写 `01-Papers/` 论文笔记
  - **同时**把公众号文章写成 `06-Notes/` 解读笔记，开头 `> 解读来源：[公众号文章名](URL)`，正文用 `[[论文标题]]` 链接到论文笔记
  - 两份笔记通过 `[[]]` 打通：论文笔记是规范引用+主笔记，解读笔记是辅助/批注
- **没识别到论文**（纯技术博客/观点/资讯）→ 只写 `06-Notes/`，不入 Zotero

**为什么这么分**：论文本身要进 Zotero（规范引用 + PDF），解读文章是二手信息只进 Obsidian（带你的批注）。两者 `[[]]` 关联，查论文时能看到"有哪些解读"。

## 核心工作流（plan-validate-execute，每个论文走一遍）

```
1. RESOLVE     run resolve_meta.py → 元数据(title/authors/abstract/year/venue/arxiv_id)
2. DOWNLOAD    下载 PDF（arxiv.org/pdf/<id>.pdf，浏览器UA；限流则标"PDF待补"继续）
3. EXTRACT     run extract_text.py <pdf> → 全文文本（供精读，不只看摘要）
4. ANALYZE     【精读全文】提炼8字段：
               - takeaway 一句话总结
               - problem 问题与动机
               - contributions 核心贡献
               - method 方法详解（架构/公式/关键模块）
               - experiments 实验亮点（数据集/指标/消融）
               - details 关键细节与技巧
               - limitations 局限与可改进
               - thinking 我的思考（借鉴/质疑/关联[[ATD-SAR]]等）
5. CLASSIFY    run classify.py --title --abstract（用元数据摘要判定）
6. CONFIRM     【检查点】向用户展示：一句话总结 + 归类，问"归类对吗？要改吗？"
               └ 用户确认或调整后才继续（防误归类，尤其SAR相关）
7. EXECUTE
   a. run zotero_push.py → 建条目+归子类+挂PDF（PDF作为附件）
   b. run obsidian_note.py --analysis "8字段|||分隔" → 精读笔记到 01-Papers/
8. VERIFY      确认云端有item+PDF附件 + 笔记已写 + frontmatter含category
9. REPORT      一行总结 + Zotero链接 + Obsidian笔记链接
```

**精读笔记是核心价值**：基于 PDF 全文（方法/实验/细节），不是摘要的浅复述。extract_text.py 提取全文后，Claude 要真正读懂并提炼，不是套模板。

**绝对不要跳过 CONFIRM 检查点**——尤其涉及SAR的论文（用户核心方向，误归类代价高）。

## 脚本调用（预制脚本，确定性，省token）

**所有路径相对本 skill 目录**（= 此 SKILL.md 所在目录，下称 `$SKILL_DIR`）。脚本在 `$SKILL_DIR/scripts/`，配置在 `$SKILL_DIR/config.json`（用户私有，含 pyzotero API key + Obsidian vault 路径，从 `config.example.json` 复制填写）。

```bash
# 1. 解析元数据（输入：URL或标题）
python "$SKILL_DIR/scripts/resolve_meta.py" "INPUT"
# 输出JSON：{title, authors, abstract, year, venue, arxiv_id, source_type}

# 2. 提取PDF全文（精读用，不只看摘要）
python "$SKILL_DIR/scripts/extract_text.py" paper.pdf
# 输出：全文文本（stdout）。Claude 据此做精读分析

# 3. 分类
python "$SKILL_DIR/scripts/classify.py" --title "TITLE" --abstract "ABSTRACT"
# 输出JSON：{main, sub, reason}

# 4. Zotero入库（元数据+分类+PDF路径）
python "$SKILL_DIR/scripts/zotero_push.py" --meta meta.json
# 输出：{item_key, collection, attached_pdf}

# 5. 写精读笔记（8字段用|||分隔：takeaway|||problem|||contributions|||method|||experiments|||details|||limitations|||thinking）
python "$SKILL_DIR/scripts/obsidian_note.py" --meta meta.json --analysis "..."
# 输出：note路径
```

> 执行时把 `$SKILL_DIR` 替换为本 SKILL.md 的实际所在目录绝对路径。脚本内部用 `__file__` 自定位 config.json，无需环境变量。

## 分类体系（30个，详见 references/classification.md）

主类（6）：📥 待整理 / 🛰️ SAR研究 / 🔬 图像超分辨率 / 🖼️ 图像复原增强 / 🌀 扩散模型 / 📚 基础与方法

判断优先级：**SAR > 任务(超分/复原) > 扩散纯理论 > 基础方法**。SAR相关全部进🛰️SAR研究（不论方法）。详见 `$SKILL_DIR/references/classification.md`。

## Obsidian笔记模板（核心：有印象+查得到）

frontmatter 必须含 `category`（子类全名）和 `tags`，Dataview 才能索引。模板结构见 `$SKILL_DIR/templates/paper.md`（obsidian_note.py 内联渲染，可改）。笔记结构：
- 💭 **一句话总结**（最关键，review时只读这句）
- 📝 摘要缩写（3-5句）
- 🎯 核心贡献
- 🔧 方法速览
- 💡 **我的思考**（可借鉴/可质疑/关联我的工作，这是吸收的本质）
- 🔗 Zotero跳转链接

## 关键约束（IRON RULES）

1. **CONFIRM 检查点不可跳**——尤其SAR论文
2. **PDF优先级**：arXiv有→下；限流→元数据先进Zotero，PDF标缺（后续补）
3. **公众号/知乎**：抓取后识别 underlying 论文（见 web mode 智能分流）。识别到→论文入Zotero+论文笔记，解读文章写06-Notes/并[[链接]]论文；没识别到→只写06-Notes/。**不要把公众号文章本身做成Zotero条目**（无规范元数据，会污染引用库）
4. **去重**：标题已存在则跳过入库（zotero_push.py自动查重）
5. **WebDAV注意**：用户Zotero用坚果云存PDF；pyzotero挂PDF走zotero.org存储，少量可接受，大量PDF建议用户Zotero客户端"查找可用PDF"
6. **路径用正斜杠**（Windows也用`/`）

## Dashboard（Dataview索引）

Dashboard 文件路径由 `config.json` 的 `vault_dir` + `dashboard_subdir` 决定（默认 `<vault>/00-Dashboard/论文地图.md`），用 Dataview 按 category 聚合。笔记 frontmatter 的 `category` 字段是索引键。`dashboard` mode 重生成该文件。**Obsidian 文件夹结构完全可配置**（papers/notes/dashboard 子目录名在 config 改），不强制 01-Papers/06-Notes 这种命名。

## 排错见 references/troubleshooting.md（arXiv限流/同步/分类冲突）
