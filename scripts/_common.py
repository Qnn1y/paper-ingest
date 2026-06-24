#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""共享工具：配置加载、pyzotero 客户端、collection 缓存、arXiv/S2 元数据获取。"""
from __future__ import annotations
import json, re, sys, time, urllib.request, urllib.parse
from pathlib import Path
import xml.etree.ElementTree as ET

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# skill 根目录 = scripts/ 的父目录；config.json 就在根目录（相对脚本定位，跨机器可移植）
SKILL_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = SKILL_DIR / "config.json"

ATOM = "{http://www.w3.org/2005/Atom}"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"


def load_config() -> dict:
    """读 config.json。所有用户相关配置（vault路径/zotero凭证）都在这，便于移植。"""
    if not CONFIG_PATH.exists():
        raise SystemExit(f"找不到 config.json：{CONFIG_PATH}\n请复制 config.example.json 为 config.json 并填写")
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def paths() -> dict:
    """从 config 读 vault 路径（运行时解析，不硬编码）。"""
    cfg = load_config()
    vault = Path(cfg["vault_dir"])
    return {
        "vault": vault,
        "papers": vault / cfg.get("papers_subdir", "01-Papers"),
        "notes": vault / cfg.get("notes_subdir", "06-Notes"),
        "dashboard": vault / cfg.get("dashboard_subdir", "00-Dashboard") / "论文地图.md",
        "storage": Path(cfg.get("storage_dir", str(vault / "attachments" / "papers"))),
    }


# 兼容旧引用（obsidian_note.py 等）：惰性取值
class _P:
    def __getattr__(self, k):
        p = paths()
        return p[{"PAPERS_DIR": "papers", "NOTES_DIR": "notes", "DASHBOARD": "dashboard", "STORAGE": "storage"}[k]]


# 这些常量保留向后兼容（实际从 config 读）
def __getattr__(name):  # 模块级惰性属性（PEP 562）
    if name in ("PAPERS_DIR", "NOTES_DIR", "DASHBOARD", "STORAGE", "VAULT"):
        p = paths()
        return {"PAPERS_DIR": p["papers"], "NOTES_DIR": p["notes"],
                "DASHBOARD": p["dashboard"], "STORAGE": p["storage"], "VAULT": p["vault"]}[name]
    raise AttributeError(name)


def get_zotero():
    """返回已连接的 pyzotero 客户端。"""
    from pyzotero import zotero
    cfg = load_config()
    return zotero.Zotero(cfg["library_id"], cfg["library_type"], cfg["api_key"])


def collection_map(zot=None) -> dict:
    """返回 {collection全名(含父级上下文唯一): key}。同名子类按"父||子"消歧。"""
    if zot is None:
        zot = get_zotero()
    cols = zot.everything(zot.collections())
    by_key = {c["key"]: c for c in cols}
    m = {}
    for c in cols:
        name = c["data"]["name"]
        parent = c["data"].get("parentCollection")
        if parent and parent in by_key:
            m[f"{by_key[parent]['data']['name']}||{name}"] = c["key"]  # 子类：父||子
        else:
            m[name] = c["key"]  # 主类
    return m, cols


def find_subcollection_key(coll_map_data, main: str, sub: str) -> str | None:
    """从 collection_map 的输出找子类 key。"""
    coll_map, _ = coll_map_data
    return coll_map.get(f"{main}||{sub}")


def fetch_url(url: str, timeout: int = 30) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def arxiv_meta(arxiv_id: str, retries: int = 3) -> dict | None:
    """从 arXiv API 取元数据。失败返回 None（让上层走 S2 兜底）。"""
    url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
    for i in range(retries):
        try:
            xml = fetch_url(url).decode("utf-8")
            root = ET.fromstring(xml)
            entry = root.find(f"{ATOM}entry")
            if entry is None:
                return None
            title = re.sub(r"\s+", " ", entry.findtext(f"{ATOM}title", "").strip())
            abstract = re.sub(r"\s+", " ", entry.findtext(f"{ATOM}summary", "").strip())
            year = (entry.findtext(f"{ATOM}published", "") or "")[:4]
            authors = []
            for a in entry.findall(f"{ATOM}author"):
                name = (a.findtext(f"{ATOM}name", "") or "").strip()
                if name:
                    parts = name.rsplit(" ", 1)
                    authors.append({"firstName": parts[0], "lastName": parts[1]} if len(parts) == 2
                                   else {"name": name})
            cats = [c.get("term", "") for c in entry.findall("{http://arxiv.org/schemas/atom}primary_category")]
            return {"title": title, "abstract": abstract, "year": year, "authors": authors,
                    "arxiv_id": arxiv_id, "url": f"https://arxiv.org/abs/{arxiv_id}",
                    "venue": "arXiv"}
        except Exception:
            time.sleep(3 * (i + 1))
    return None


def s2_meta(title: str) -> dict | None:
    """Semantic Scholar 标题搜索兜底。"""
    q = urllib.parse.quote(title)
    url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={q}&limit=1&fields=title,abstract,year,authors,externalIds,venue"
    for i in range(3):
        try:
            data = json.loads(fetch_url(url, 20).decode("utf-8"))
            papers = data.get("data", [])
            if not papers:
                return None
            p = papers[0]
            authors = [{"firstName": (a.get("name", "").rsplit(" ", 1) + [""])[0],
                        "lastName": (a.get("name", "").rsplit(" ", 1) + [""])[-1]}
                       for a in p.get("authors", []) if a.get("name")]
            ext = p.get("externalIds", {}) or {}
            return {"title": p.get("title", ""), "abstract": p.get("abstract", "") or "",
                    "year": str(p.get("year", "") or ""), "authors": authors,
                    "arxiv_id": ext.get("ArXiv"), "doi": ext.get("DOI"),
                    "url": f"https://arxiv.org/abs/{ext['ArXiv']}" if ext.get("ArXiv") else "",
                    "venue": p.get("venue", "") or "arXiv"}
        except Exception:
            time.sleep(5 * (i + 1))
    return None


def download_pdf(arxiv_id: str, dest_dir: Path, retries: int = 2) -> Path | None:
    """下载 arXiv PDF（用浏览器级 UA，arXiv 对 urllib 默认 UA 更易限流）。限流/失败返回 None。"""
    dest = dest_dir / f"{arxiv_id}.pdf"
    if dest.exists() and dest.stat().st_size > 10000:
        return dest
    for i in range(retries):
        try:
            data = fetch_url(f"https://arxiv.org/pdf/{arxiv_id}.pdf", 60)
            if data[:4] == b"%PDF":
                dest.write_bytes(data)
                return dest
        except Exception:
            time.sleep(8 * (i + 1))  # arXiv 限流退避拉长
    return None
