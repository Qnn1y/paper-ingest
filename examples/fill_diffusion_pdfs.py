#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""示例：批量给 Zotero 已有论文补 PDF（arXiv 解封后用，克制间隔防再限流）。

演示如何遍历 Zotero 已有条目、下载 PDF、挂载。可改成你自己的论文清单。
"""
import sys, time, urllib.request, os
from pathlib import Path
# examples/ 脚本要能找到 ../scripts/_common.py
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import _common as C
from pyzotero import zotero

# 16 篇（DDIM 已有 PDF，会自动跳过）
CLASSICS = [
    ("2006.11239", "Denoising Diffusion Probabilistic Models"),
    ("2010.02502", "Denoising Diffusion Implicit Models"),
    ("2011.13456", "Score-Based Generative Modeling through Stochastic Differential Equations"),
    ("1907.05600", "Generative Modeling by Estimating Gradients of the Data Distribution"),
    ("2208.11970", "Understanding Diffusion Models: A Unified Perspective"),
    ("2303.01469", "Consistency Models"),
    ("2310.04378", "Latent Consistency Models: Synthesizing High-Resolution Images with Few-Step Inference"),
    ("2206.00927", "DPM-Solver++: Fast Solver for Guided Sampling of Diffusion Probabilistic Models"),
    ("2202.00512", "Progressive Distillation for Fast Sampling of Diffusion Models"),
    ("2307.12348", "ResShift: Efficient Diffusion Model for Image Super-resolution by Residual Shifting"),
    ("2302.05543", "Adding Conditional Control to Text-to-Image Diffusion Models"),
    ("2207.12598", "Classifier-Free Diffusion Guidance"),
    ("2308.06721", "IP-Adapter: Text Compatible Image Prompt Adapter for Text-to-Image Diffusion Models"),
    ("2112.10752", "High-Resolution Image Synthesis with Latent Diffusion Models"),
    ("2206.00364", "Elucidating the Design Space of Diffusion-Based Generative Models"),
    ("2212.09748", "Scalable Diffusion Models with Transformers"),
]

DEST = C.paths()["storage"] / "_ingested"  # 从 config.json 读，可移植
DEST.mkdir(parents=True, exist_ok=True)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"

cfg = C.load_config()
zot = zotero.Zotero(cfg["library_id"], cfg["library_type"], cfg["api_key"])

ok, skip, fail = 0, 0, 0
for aid, title in CLASSICS:
    # 1. 按 title 找 Zotero item
    found = zot.everything(zot.items(q=title, limit=3, itemType="-attachment"))
    item = next((it for it in found if it["data"].get("title", "").strip().lower() == title.lower()), None)
    if not item:
        print(f"[跳过] Zotero找不到: {title[:40]}"); skip += 1; continue
    key = item["key"]
    # 2. 是否已有 PDF
    children = zot.children(key)
    if any(c["data"].get("contentType") == "application/pdf" for c in children):
        print(f"[已有] {aid}"); skip += 1; continue
    # 3. 下载 PDF
    pdf = DEST / f"{aid}.pdf"
    try:
        req = urllib.request.Request(f"https://arxiv.org/pdf/{aid}.pdf", headers={"User-Agent": UA})
        data = urllib.request.urlopen(req, timeout=60).read()
        if data[:4] != b"%PDF":
            print(f"[失败] {aid} 非PDF"); fail += 1; continue
        pdf.write_bytes(data)
    except Exception as e:
        msg = str(e)
        print(f"[失败] {aid}: {msg[:50]}")
        fail += 1
        if "429" in msg or "Too Many" in msg:
            print("⚠️ 又限流了，停止以免加重"); break
        continue
    # 4. 挂载
    zot.attachment_simple([str(pdf)], parentid=key)
    ok += 1
    print(f"[完成] {aid} {title[:35]}  ({pdf.stat().st_size//1024}KB)")
    time.sleep(10)  # 克制间隔

print(f"\n=== 补PDF完成: 新挂 {ok}, 跳过 {skip}, 失败 {fail} ===")
