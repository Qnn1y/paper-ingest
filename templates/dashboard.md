---
title: 论文地图
category: dashboard
---

# 📚 论文地图

> 由 paper-ingest skill 维护。按笔记 frontmatter 的 `category` 字段自动聚合。把本文件放到你 Obsidian vault 的 dashboard 目录（config.json 的 `dashboard_subdir`）。

## 📊 最近入库

```dataview
TABLE status AS "状态", sub AS "子类", date-added AS "添加日期"
FROM "01-Papers" AND "06-Notes"
WHERE category
SORT date-added DESC
LIMIT 20
```

> 把上面的 `"01-Papers"` `"06-Notes"` 改成你 config.json 里实际的 papers_subdir / notes_subdir。

## 按主类聚合（改 main 字段值匹配你的分类）

```dataview
TABLE WITHOUT ID file.link AS "论文", sub AS "子类", date-added AS "日期"
FROM "01-Papers"
WHERE contains(main, "图像超分辨率")
SORT date-added DESC
```

## ⬜ 待读清单

```dataview
LIST
FROM "01-Papers"
WHERE status = "📥 待读"
SORT date-added DESC
```

## 状态流转

把笔记 frontmatter 的 `status` 从 `📥 待读` 改成 `🔍 已浏览` 或 `✅ 已精读`，上面查询自动更新。

---

**自定义 Dataview 查询**：按 `main` / `sub` / `tags` / `year` 任意字段聚合。frontmatter 的 `category` `main` `sub` `status` `date-added` `tags` 都是可查询键。
