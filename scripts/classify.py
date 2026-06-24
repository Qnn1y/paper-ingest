#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""classify.py — 论文分类到 30-collection 结构（确定性规则）。

用法：
  python classify.py --title "..." --abstract "..."
  python classify.py --json meta.json   # 从 resolve_meta 输出读

输出 JSON: {"main":..., "sub":..., "reason":...}
"""
import sys, re, json, argparse, os
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# 30 分类结构（与 zotero 实际 collection 一致）
STRUCTURE = {
    "🛰️ SAR研究": ["🔬 SAR超分辨率", "🌫️ SAR去噪去旁瓣", "🔍 SAR目标检测", "👁️ SAR目标识别", "🖼️ SAR图像生成"],
    "🔬 图像超分辨率": ["💡 光学图像SR", "⚡ 轻量高效SR", "🎥 视频超分", "🌍 遥感超分", "🌈 高光谱光场"],
    "🖼️ 图像复原增强": ["🌫️ 去噪降噪", "🌀 去模糊", "🌧️ 去雨去雾", "🌙 低光增强", "🎨 Inpainting修复", "🔧 通用复原框架"],
    "🌀 扩散模型": ["📖 理论基础", "⚡ 加速推理", "🔧 条件控制", "🎓 训练优化"],
    "📚 基础与方法": ["🏗️ 架构创新", "🎓 训练策略", "🧬 生成模型", "🔗 跨领域方法"],
}


def classify(title: str, abstract: str) -> tuple[str, str, str]:
    """返回 (主类, 子类, 理由)。优先级：SAR > 任务 > 扩散纯理论 > 基础。"""
    t = (title or "").lower()
    a = (abstract or "").lower()
    c = t + " " + a

    is_sar = bool(re.search(r"\bsars?\b|synthetic aperture|合成孔径|机载|极化雷达", c))
    domain = ("sar" if is_sar
              else "video" if re.search(r"video|\bvsr\b|视频", c)
              else "medical" if re.search(r"medical.*imag|mri.*imag|ct.*scan|医学影像", c)
              else "remote_sensing" if re.search(r"remote.*sens|satellite.*imag|遥感", c)
              else "hyperspectral" if re.search(r"hyperspectral|light.*field|高光谱|光场", c)
              else "optical")

    task = ("sr" if re.search(r"super.?res|\bsr\b|upsampl|超分", c)
            else "denoise" if re.search(r"denois|despeckl|speckle|去噪", c)
            else "deblur" if re.search(r"deblur|去模糊", c)
            else "derain" if re.search(r"derain|dehaz|去雨|去雾", c)
            else "lowlight" if re.search(r"low.?light|hdr\b|illumination|exposure|低光", c)
            else "inpaint" if re.search(r"inpaint|shadow.*remov|reflection.*remov|修复", c)
            else "detect" if re.search(r"detect|检测", c)
            else "recognize" if re.search(r"recogni|classif|atr\b|识别|分类", c)
            else "generate" if re.search(r"\bgan\b|generat|synthe|生成", c)
            else "restoration" if re.search(r"restor|enhance|复原|增强", c)
            else None)

    is_survey = bool(re.search(r"survey|review|tutorial|综述", c))
    is_framework = bool(re.search(r"agent|foundation.*model|unified.*framework|通用.*框架", c))
    is_lightweight = bool(re.search(r"lightweight|efficient|mobile|real.?time|轻量", c))
    method = ("diffusion" if re.search(r"diffus|扩散", c)
              else "gan" if re.search(r"\bgan\b|generative adversarial", c)
              else "physical" if re.search(r"frequ|fourier|wavelet|physic", c)
              else "cnn")

    # === SAR 优先 ===
    if domain == "sar":
        if task == "sr" or task is None:
            return "🛰️ SAR研究", "🔬 SAR超分辨率", "SAR超分"
        return {"denoise": ("🛰️ SAR研究", "🌫️ SAR去噪去旁瓣", "SAR去噪"),
                "detect": ("🛰️ SAR研究", "🔍 SAR目标检测", "SAR检测"),
                "recognize": ("🛰️ SAR研究", "👁️ SAR目标识别", "SAR识别"),
                "generate": ("🛰️ SAR研究", "🖼️ SAR图像生成", "SAR生成")}.get(
            task, ("🛰️ SAR研究", "🔬 SAR超分辨率", "SAR其他→超分"))

    # === 超分 ===
    if task == "sr":
        if domain == "video": return "🔬 图像超分辨率", "🎥 视频超分", "视频SR"
        if domain == "remote_sensing": return "🔬 图像超分辨率", "🌍 遥感超分", "遥感SR"
        if domain == "hyperspectral": return "🔬 图像超分辨率", "🌈 高光谱光场", "高光谱/光场"
        if is_lightweight: return "🔬 图像超分辨率", "⚡ 轻量高效SR", "轻量SR"
        return "🔬 图像超分辨率", "💡 光学图像SR", "光学SR"

    if is_lightweight and task == "restoration":
        return "🔬 图像超分辨率", "⚡ 轻量高效SR", "轻量复原"
    if domain == "video" and re.search(r"fusion|fuse", t):
        return "🔬 图像超分辨率", "🎥 视频超分", "视频融合"
    if is_framework and re.search(r"agent|foundation|unified.*framework", t):
        return "🖼️ 图像复原增强", "🔧 通用复原框架", "通用框架"

    # === 复原 ===
    if task == "denoise": return "🖼️ 图像复原增强", "🌫️ 去噪降噪", "去噪"
    if task == "deblur": return "🖼️ 图像复原增强", "🌀 去模糊", "去模糊"
    if task == "derain": return "🖼️ 图像复原增强", "🌧️ 去雨去雾", "去雨/去雾"
    if task == "lowlight": return "🖼️ 图像复原增强", "🌙 低光增强", "低光/HDR"
    if task == "inpaint": return "🖼️ 图像复原增强", "🎨 Inpainting修复", "修复"
    if task == "restoration":
        if a:
            if re.search(r"denois", a): return "🖼️ 图像复原增强", "🌫️ 去噪降噪", "去噪(摘要)"
            if re.search(r"deblur", a): return "🖼️ 图像复原增强", "🌀 去模糊", "去模糊(摘要)"
            if re.search(r"inpaint", a): return "🖼️ 图像复原增强", "🎨 Inpainting修复", "修复(摘要)"
            if re.search(r"low.?light", a): return "🖼️ 图像复原增强", "🌙 低光增强", "低光(摘要)"
            if re.search(r"super.?res", a): return "🔬 图像超分辨率", "💡 光学图像SR", "SR(摘要)"
        if is_survey: return "📚 基础与方法", "🔗 跨领域方法", "复原综述"
        return "🖼️ 图像复原增强", "🔧 通用复原框架", "通用复原"

    # === 基础 ===
    if method == "gan" and not task: return "📚 基础与方法", "🧬 生成模型", "GAN基础"
    if re.search(r"capsule|detr|mamba.*network|架构", t): return "📚 基础与方法", "🏗️ 架构创新", "架构创新"
    if re.search(r"contrastive|self.?supervis|distill.*knowledge", c): return "📚 基础与方法", "🎓 训练策略", "训练策略"
    if re.search(r"\bnlp\b|language.*model|graph.*neural|slam", t): return "📚 基础与方法", "🔗 跨领域方法", "跨领域"

    return "📥 待整理", "", "待人工分类"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", default="")
    ap.add_argument("--abstract", default="")
    ap.add_argument("--json", dest="jsonfile", help="从 resolve_meta 输出的 json 文件读")
    args = ap.parse_args()
    if args.jsonfile:
        m = json.loads(open(args.jsonfile, encoding="utf-8").read())
        args.title = m.get("title", "")
        args.abstract = m.get("abstract", "")
    main, sub, reason = classify(args.title, args.abstract)
    print(json.dumps({"main": main, "sub": sub, "reason": reason}, ensure_ascii=False, indent=2))
