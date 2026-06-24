#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""obsidian_note.py — 渲染 Obsidian 笔记（含 Dataview 可索引的 frontmatter）。

用法：
  python obsidian_note.py --meta meta.json --analysis "一句话总结|||核心贡献|||方法速览|||我的思考"
  python obsidian_note.py --meta meta.json --analysis-file analysis.txt --web  # 公众号/知乎

笔记写到 01-Papers/（论文）或 06-Notes/（公众号/知乎）。
"""
import sys, json, argparse, re, os
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C


def safe_filename(title: str) -> str:
    s = re.sub(r"[\\/:*?\"<>|]", "", title).strip()
    return s[:80] or "untitled"


def build_note(meta: dict, analysis: dict, is_web: bool) -> str:
    title = meta.get("title", "Untitled")
    today = datetime.now().strftime("%Y-%m-%d")
    category = f"{meta.get('main','')}/{meta.get('sub','')}" if meta.get("sub") else meta.get("main", "")
    citekey = meta.get("citekey", "")
    zotero_key = meta.get("item_key", "")
    tags = meta.get("tags", [])

    # 作者列表（先算成字符串，避免嵌套 f-string）
    authors = []
    for a in meta.get("authors", [])[:5]:
        if a.get("name"):
            authors.append(a["name"])
        else:
            ln = a.get("lastName", "")
            fn = (a.get("firstName", "") or "")[0] if a.get("firstName") else ""
            authors.append((ln + " " + fn).strip())
    authors_str = json.dumps(authors, ensure_ascii=False)
    meta["authors_str"] = ", ".join(authors)

    # frontmatter（Dataview 索引键：category / status / date-added / tags）
    fm = ["---",
          f'title: "{title.replace(chr(34), "")}"',
          f"authors: {authors_str}",
          f"year: {meta.get('year','')}",
          f'venue: "{meta.get("venue","")}"',
          f"category: \"{category}\"",
          f"main: \"{meta.get('main','')}\"",
          f"sub: \"{meta.get('sub','')}\"",
          f"status: 📥 待读",
          f"date-added: {today}",
          f"source: {meta.get('source_type','web' if is_web else 'paper')}",
          f"url: {meta.get('url','')}",
          f"zotero: {zotero_key}"]
    if meta.get("arxiv_id"): fm.append(f"arxiv: {meta['arxiv_id']}")
    if meta.get("code_url"): fm.append(f"code: {meta['code_url']}")
    if citekey: fm.append(f"citekey: {citekey}")
    fm.append(f"tags: {json.dumps(['paper'] + (['web'] if is_web else []) + tags, ensure_ascii=False)}")
    fm.append("---")

    if is_web:
        # 公众号/知乎：精简笔记
        body = [f"# {title}", "",
                "## 💭 一句话总结", f"> {analysis.get('takeaway','（待填）')}", "",
                "## 📝 要点", analysis.get("contributions", "（待填）"), "",
                "## 💡 我的批注", analysis.get("thinking", "（待填）")]
    else:
        # 论文：精读笔记（基于 PDF 全文）
        body = [f"# {title}", "",
                f"> **精读笔记**（基于 PDF 全文）| {meta.get('authors_str','')} | {meta.get('venue','')} {meta.get('year','')}",
                f"> arXiv: {meta.get('url','')}" + (f" | 代码: {meta['code_url']}" if meta.get('code_url') else ""), "",
                "## 💭 一句话总结", f"> {analysis.get('takeaway','（待填）')}", "",
                "（只读这句也能回忆起这篇论文在讲什么）", "",
                "## 📋 问题与动机", analysis.get("problem", "（待填）"), "",
                "## 🎯 核心贡献", analysis.get("contributions", "（待填）"), "",
                "## 🔧 方法详解", analysis.get("method", "（待填）"), "",
                "## 🧪 实验亮点", analysis.get("experiments", "（待填）"), "",
                "## 🔑 关键细节与技巧", analysis.get("details", "（待填）"), "",
                "## ⚠️ 局限与可改进", analysis.get("limitations", "（待填）"), "",
                "## 💡 我的思考", analysis.get("thinking", "（待填）"),
                "", "## 🔗 相关",
                f"- Zotero: zotero://select/items/{zotero_key}" if zotero_key else "",
                f"- arXiv: {meta.get('url','')}"]
    return "\n".join(fm) + "\n\n" + "\n".join(body) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--meta", required=True)
    ap.add_argument("--analysis", help="用|||分隔的分析字段：takeaway|||digest|||contributions|||method|||thinking")
    ap.add_argument("--analysis-file", help="分析文本文件（JSON）")
    ap.add_argument("--web", action="store_true", help="公众号/知乎笔记")
    args = ap.parse_args()

    meta = json.loads(open(args.meta, encoding="utf-8").read())
    # 精读分析字段（基于PDF全文）：takeaway/problem/contributions/method/experiments/details/limitations/thinking
    ANALYSIS_KEYS = ["takeaway", "problem", "contributions", "method",
                     "experiments", "details", "limitations", "thinking"]
    if args.analysis_file:
        analysis = json.loads(open(args.analysis_file, encoding="utf-8").read())
    elif args.analysis:
        parts = args.analysis.split("|||")
        analysis = {k: (parts[i] if i < len(parts) else "") for i, k in enumerate(ANALYSIS_KEYS)}
    else:
        analysis = {k: "" for k in ANALYSIS_KEYS}

    is_web = args.web
    note = build_note(meta, analysis, is_web)
    fname = safe_filename(meta.get("title", "untitled")) + ".md"
    outdir = C.NOTES_DIR if is_web else C.PAPERS_DIR
    outdir.mkdir(parents=True, exist_ok=True)
    outpath = outdir / fname
    outpath.write_text(note, encoding="utf-8")
    print(json.dumps({"note_path": str(outpath), "category": meta.get("main","")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
