#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""zotero_push.py — 把论文推入 Zotero（pyzotero 全自动）。

用法：
  python zotero_push.py --meta meta.json
  # meta.json 应含 resolve_meta + classify 的结果：
  #   {title, authors, abstract, year, venue, url, arxiv_id, main, sub, pdf_path?}

行为：查重（标题已存在则跳过并返回既有item）→ 建条目 → 归到子类 → 挂PDF（若有）。
输出 JSON: {item_key, collection, attached_pdf, action: created|skipped}
"""
import sys, json, argparse, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C


def main(meta_path: str) -> dict:
    meta = json.loads(open(meta_path, encoding="utf-8").read())
    title = meta.get("title", "").strip()
    if not title:
        raise SystemExit("meta 缺 title")

    zot = C.get_zotero()
    coll_data, _ = C.collection_map(zot)

    # 1. 查重
    existing = zot.everything(zot.items(q=title, limit=5, itemType="-attachment"))
    for it in existing:
        if (it["data"].get("title", "")).strip().lower() == title.lower():
            return {"action": "skipped", "item_key": it["key"],
                    "collection": meta.get("main", ""), "reason": "标题已存在"}

    # 2. 建条目
    item_type = "conferencePaper" if meta.get("venue") and "arxiv" not in (meta.get("venue","").lower()) else "preprint"
    template = zot.item_template(item_type)
    template["title"] = title
    if meta.get("abstract"): template["abstractNote"] = meta["abstract"]
    if meta.get("year"): template["date"] = meta["year"]
    if meta.get("url"): template["url"] = meta["url"]
    if meta.get("doi"): template["DOI"] = meta["doi"]
    venue = meta.get("venue", "")
    if venue and item_type == "conferencePaper":
        template["proceedingsTitle"] = venue
    # preprint 不设 venue 字段（用 archiveID 表达 arXiv 即可，避免 publicationTitle 报错）
    if meta.get("arxiv_id") and item_type == "preprint":
        template["repository"] = "arXiv"
        template["archiveID"] = f"arXiv:{meta['arxiv_id']}"
    # conferencePaper/journalArticle 没有 repository/archiveID 字段，arXiv 信息靠 url 保留
    # 作者
    creators = []
    for a in meta.get("authors", []):
        if a.get("name"):
            creators.append({"creatorType": "author", "name": a["name"]})
        else:
            creators.append({"creatorType": "author", "firstName": a.get("firstName", ""), "lastName": a.get("lastName", "")})
    if creators:
        template["creators"] = creators

    # 3. 归类
    main, sub = meta.get("main", ""), meta.get("sub", "")
    coll_keys = []
    sub_key = C.find_subcollection_key((coll_data, None), main, sub) if sub else None
    if sub_key:
        coll_keys = [sub_key]
    elif main:
        coll_keys = [coll_data.get(main, "")] if coll_data.get(main) else []
    template["collections"] = [k for k in coll_keys if k]

    # 4. 创建
    resp = zot.create_items([template])
    created = resp.get("successful", {}).get("0", {})
    if not created:
        err = resp.get("failed", {}).get("0", {})
        raise SystemExit(f"创建失败: {json.dumps(err, ensure_ascii=False)}")
    item_key = created["key"]

    # 5. 挂 PDF（注意：pyzotero 走 zotero.org 存储；用户主力走坚果云WebDAV，少量可接受）
    attached = False
    pdf_path = meta.get("pdf_path")
    if pdf_path and os.path.exists(pdf_path):
        try:
            zot.attachment_simple([pdf_path], parentid=item_key)
            attached = True
        except Exception as e:
            print(f"[警告] PDF挂载失败: {e}", file=sys.stderr)

    return {"action": "created", "item_key": item_key,
            "collection": f"{main}/{sub}" if sub else main, "attached_pdf": attached}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--meta", required=True, help="meta.json 路径")
    args = ap.parse_args()
    print(json.dumps(main(args.meta), ensure_ascii=False, indent=2))
