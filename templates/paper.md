---
title: "{{title}}"
authors: {{authors}}
year: {{year}}
venue: "{{venue}}"
category: "{{main}}/{{sub}}"
main: "{{main}}"
sub: "{{sub}}"
status: "📥 待读"
date-added: {{date}}
source: {{source_type}}
url: {{url}}
zotero: {{item_key}}
arxiv: {{arxiv_id}}
code: {{code_url}}
tags: ["paper"]
---

# {{title}}

> **精读笔记**（基于 PDF 全文）| {{authors}} | {{venue}} {{year}}
> arXiv: {{url}} {{code_url_label}}

## 💭 一句话总结
> {{takeaway}}

（只读这句也能回忆起这篇论文在讲什么）

## 📋 问题与动机
{{problem}}

这篇论文要解决什么问题？现有方法的痛点是什么？

## 🎯 核心贡献
{{contributions}}

## 🔧 方法详解
{{method}}

基于全文的深度解读：整体架构 / 关键模块 / 数学原理 / 训练策略。重点讲清楚"怎么做的"，包含关键公式或机制。

## 🧪 实验亮点
{{experiments}}

数据集 / 评估指标 / 关键对比结果 / 消融发现。引用具体数字。

## 🔑 关键细节与技巧
{{details}}

全文里值得记住的实现细节、工程技巧、容易被忽略的设计。

## ⚠️ 局限与可改进
{{limitations}}

## 💡 我的思考
{{thinking}}

- **可借鉴**：对我自己的工作（[[ATD-SAR]] 等）有什么启发
- **可质疑**：哪里不稳妥、假设是否成立
- **延伸方向**：能否改进/迁移/组合

## 🔗 相关
- Zotero: zotero://select/items/{{item_key}}
- 代码: {{code_url}}
- arXiv: {{url}}
- 相关论文: [[...]]

<!-- 精读笔记模板（基于 PDF 全文，非摘要）。
     obsidian_note.py 内联渲染。改格式编辑 build_note()。
     frontmatter 的 category/main/sub/status/date-added 是 Dataview 索引键，勿删。 -->
