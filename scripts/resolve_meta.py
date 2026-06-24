#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""resolve_meta.py — URL/标题/DOI → 论文元数据。

用法：
  python resolve_meta.py "https://arxiv.org/abs/2006.11239"
  python resolve_meta.py "FaithDiff"
  python resolve_meta.py "10.1109/CVPR.2022.001"

输出 JSON 到 stdout。无网络或查不到时 exit 1。
"""
import sys, re, json, os
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C


def detect_arxiv_id(s: str) -> str | None:
    m = re.search(r"(\d{4}\.\d{4,5})", s)
    return m.group(1) if m else None


def detect_doi(s: str) -> str | None:
    m = re.search(r"(10\.\d{4,9}/[^\s\"']+)", s)
    return m.group(1).rstrip(").,") if m else None


def main(inp: str) -> dict:
    inp = inp.strip()
    # arXiv
    aid = detect_arxiv_id(inp)
    if aid:
        meta = C.arxiv_meta(aid)
        if meta:
            meta["source_type"] = "arxiv"
            return meta
        # arXiv 失败走 S2（用 id）
    # DOI → CrossRef（暂用 S2 兜底，DOI 较少）
    doi = detect_doi(inp)
    if doi:
        meta = C.s2_meta(inp)
        if meta:
            meta["source_type"] = "doi"
            meta["doi"] = doi
            return meta
    # 纯标题 → S2
    meta = C.s2_meta(inp if not aid else inp)
    if meta:
        meta["source_type"] = "title"
        return meta
    raise SystemExit("未找到元数据（arXiv/S2 都没命中）")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python resolve_meta.py <URL或标题>", file=sys.stderr)
        sys.exit(2)
    meta = main(sys.argv[1])
    print(json.dumps(meta, ensure_ascii=False, indent=2))
