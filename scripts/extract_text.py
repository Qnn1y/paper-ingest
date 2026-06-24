#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""extract_text.py — 从 PDF 提取全文文本（供 Claude 精读分析）。

用法：
  python extract_text.py paper.pdf                 # 输出文本到 stdout
  python extract_text.py paper.pdf -o out.md       # 写到文件
  python extract_text.py paper.pdf --max 80000     # 限制最大字符

提取策略：PyMuPDF 逐页提取 → 清理多余空行/页眉页脚启发式 → 保留章节结构。
输出尽量干净完整的全文，让 Claude 能读到方法/实验细节（不只摘要）。
"""
import sys, re, argparse, os
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
import fitz  # pymupdf


def clean_page(text: str) -> str:
    """清理单页：去多余空行、常见页眉页脚。"""
    # 折叠 3+ 连续空行为 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    # 去行尾空格
    lines = [ln.rstrip() for ln in text.split("\n")]
    text = "\n".join(lines)
    # 启发式去页眉页脚：纯数字行（页码）、短的全大写/期刊名行（前几行）
    # 保守处理，只去首尾的纯数字行
    while lines and re.fullmatch(r"\s*\d+\s*", lines[0]):
        lines.pop(0)
    while lines and re.fullmatch(r"\s*\d+\s*", lines[-1]):
        lines.pop()
    return "\n".join(lines).strip()


def extract(pdf_path: str, max_chars: int = 60000) -> str:
    doc = fitz.open(pdf_path)
    pages = []
    for i, page in enumerate(doc, 1):
        t = clean_page(page.get_text())
        if t:
            pages.append(f"<!-- Page {i} -->\n{t}")
    doc.close()
    full = "\n\n".join(pages)
    if len(full) > max_chars:
        # 保留前 max_chars（通常 abstract→method→experiment 在前，references 在后可截）
        full = full[:max_chars] + "\n\n[...全文过长，已截断。前半含 abstract/method/experiment...]"
    return full


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf", help="PDF 文件路径")
    ap.add_argument("-o", "--out", help="输出文件（默认 stdout）")
    ap.add_argument("--max", type=int, default=60000, help="最大字符数（默认60000）")
    args = ap.parse_args()

    if not os.path.exists(args.pdf):
        sys.exit(f"PDF 不存在: {args.pdf}")
    text = extract(args.pdf, args.max)
    if args.out:
        open(args.out, "w", encoding="utf-8").write(text)
        print(f"已写到 {args.out}（{len(text)} 字符）", file=sys.stderr)
    else:
        print(text)
