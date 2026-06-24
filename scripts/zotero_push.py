#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""zotero_push.py — 把论文推入 Zotero。

用法：
  python zotero_push.py --meta meta.json
  # meta.json 应含 resolve_meta + classify 的结果：
  #   {title, authors, abstract, year, venue, url, arxiv_id, main, sub, pdf_path?}

行为：查重（标题已存在则跳过并返回既有 item）→ 建条目 → 归到子类。

⚠️ PDF 挂载【不走 pyzotero】（pyzotero 只能用 zotero.org 服务器存储，会撞 300MB 配额）。
   PDF 改为累积到 pending_attachments.json + 生成 attach_pending.js，
   用户在 Zotero 客户端 Run JavaScript 跑（走 WebDAV 坚果云，不占配额）。
   见 README「PDF 同步」一节。

输出 JSON: {item_key, collection, attached_pdf, action: created|skipped}
"""
import sys, json, argparse, os
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C

PENDING_PATH = C.SKILL_DIR / "pending_attachments.json"
ATTACH_JS_PATH = C.SKILL_DIR / "attach_pending.js"


def append_pending(key: str, pdf_path: str, title: str):
    """累积待挂 PDF 到 pending_attachments.json（去重同 key）。"""
    pend = []
    if PENDING_PATH.exists():
        try:
            pend = json.loads(PENDING_PATH.read_text(encoding="utf-8"))
        except Exception:
            pend = []
    pend = [p for p in pend if p.get("key") != key]
    pend.append({"key": key, "file": str(pdf_path), "title": title, "ts": datetime.now().isoformat()})
    PENDING_PATH.write_text(json.dumps(pend, ensure_ascii=False, indent=2), encoding="utf-8")


def _has_real_pdf(zot, parent_key: str) -> bool:
    """判断 parent 是否有【真正上传成功】的 PDF 附件。
    关键：必须同时有 md5 字段——否则是「幽灵附件」（413 失败残留，文件没传上去）。
    """
    for c in zot.children(parent_key):
        d = c["data"]
        if d.get("contentType") == "application/pdf" and d.get("md5"):
            return True
    return False


def gen_attach_js(zot=None):
    """读 pending → 剔除已挂载的（含幽灵附件检测）→ 生成 attach_pending.js。
    返回剩余待挂数。
    """
    if zot is None:
        zot = C.get_zotero()
    pend = json.loads(PENDING_PATH.read_text(encoding="utf-8")) if PENDING_PATH.exists() else []
    # prune：移除已在 Zotero 真正挂载 PDF 的（_has_real_pdf 用 md5 防幽灵误判）
    before = len(pend)
    pend = [p for p in pend if not _has_real_pdf(zot, p["key"])]
    if len(pend) != before:
        PENDING_PATH.write_text(json.dumps(pend, ensure_ascii=False, indent=2), encoding="utf-8")
    # Zotero importFromFile 要 OS 原生路径（Windows 反斜杠）；正斜杠会报 "Unexpected path value"
    tasks = [{"key": p["key"], "file": p["file"].replace("/", "\\")} for p in pend]
    js_data = json.dumps(tasks, ensure_ascii=False)
    js = f'''// === 挂载待挂 PDF（走 Zotero 客户端 → 坚果云 WebDAV，不占 zotero.org 配额）===
// 用法: Zotero → 工具 → 开发者 → Run JavaScript → 粘贴 → Run
// 跑完点右上角同步按钮，PDF 传到坚果云，另一台同步即可拉到。
// 挂载成功的条目下次本脚本自动从 pending 剔除。
(async function () {{
  const TASKS = {js_data};
  const libID = Zotero.Libraries.userLibraryID;
  const log = [];
  try {{
    let attached = 0, skip = 0, fail = 0;
    for (const t of TASKS) {{
      try {{
        const item = await Zotero.Items.getByLibraryAndKeyAsync(libID, t.key);
        if (!item) {{ log.push("找不到 " + t.key); fail++; continue; }}
        const atts = item.getAttachments();
        const hasPdf = atts.length > 0 && (await Promise.all(
          atts.map(id => Zotero.Items.getAsync(id))
        )).some(a => a && a.attachmentContentType === "application/pdf" && a.attachmentHash);
        if (hasPdf) {{ skip++; continue; }}
        await Zotero.Attachments.importFromFile({{ file: t.file, parentItemID: item.id }});
        attached++;
      }} catch (e) {{ fail++; log.push("失败 " + t.key + ": " + e.message); }}
    }}
    log.push("=== 挂载 " + attached + " / 已有跳过 " + skip + " / 失败 " + fail + " ===");
    log.push("完成后点右上角同步按钮");
    alert(log.join("\\n"));
  }} catch (e) {{ log.push("顶层错误: " + e.message); alert(log.join("\\n")); }}
}})();
'''
    ATTACH_JS_PATH.write_text(js, encoding="utf-8")
    return len(tasks)


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

    # 5. PDF：【不走 pyzotero】累积到 pending + 生成 attach_pending.js（走客户端 WebDAV）
    attached = False
    pdf_path = meta.get("pdf_path")
    if pdf_path and os.path.exists(pdf_path):
        append_pending(item_key, pdf_path, title)
        remaining = gen_attach_js(zot)
        attached = f"pending({remaining})"

    return {"action": "created", "item_key": item_key,
            "collection": f"{main}/{sub}" if sub else main, "attached_pdf": attached}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--meta", required=True, help="meta.json 路径")
    args = ap.parse_args()
    print(json.dumps(main(args.meta), ensure_ascii=False, indent=2))
