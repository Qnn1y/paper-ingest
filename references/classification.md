# 分类判定详解（30-collection 结构）

> classify.py 的判定规则说明。SKILL.md 引用本文档。

## 30 分类体系

**6 主类 + 24 子类**：

```
📥 待整理（无子类）

🛰️ SAR研究
   ├─ 🔬 SAR超分辨率      ← SAR + 超分（用户核心方向）
   ├─ 🌫️ SAR去噪去旁瓣    ← SAR + 去噪/散斑/旁瓣
   ├─ 🔍 SAR目标检测      ← SAR + 检测
   ├─ 👁️ SAR目标识别      ← SAR + 识别/分类
   └─ 🖼️ SAR图像生成      ← SAR + 生成/GAN

🔬 图像超分辨率
   ├─ 💡 光学图像SR       ← 默认光学超分
   ├─ ⚡ 轻量高效SR       ← lightweight/efficient/real-time
   ├─ 🎥 视频超分          ← video/VSR
   ├─ 🌍 遥感超分          ← remote sensing/satellite
   └─ 🌈 高光谱光场        ← hyperspectral/light field

🖼️ 图像复原增强
   ├─ 🌫️ 去噪降噪
   ├─ 🌀 去模糊
   ├─ 🌧️ 去雨去雾
   ├─ 🌙 低光增强          ← low-light/HDR/exposure
   ├─ 🎨 Inpainting修复    ← inpainting/shadow/reflection
   └─ 🔧 通用复原框架      ← agent/foundation model/通用

🌀 扩散模型（纯理论，不含应用）
   ├─ 📖 理论基础          ← DDPM/Score-SDE
   ├─ ⚡ 加速推理          ← LCM/一步/蒸馏
   ├─ 🔧 条件控制          ← ControlNet/IP-Adapter/LoRA
   └─ 🎓 训练优化          ← EDM/DiT/LDM

📚 基础与方法
   ├─ 🏗️ 架构创新          ← Transformer/Mamba/Capsule
   ├─ 🎓 训练策略          ← 对比学习/自监督
   ├─ 🧬 生成模型          ← GAN/VAE 理论
   └─ 🔗 跨领域方法        ← NLP/SLAM/图网络
```

## 判定优先级（关键）

```
1. SAR 优先（最高）—— 任何 SAR 论文都进 🛰️ SAR研究，不论用扩散/Transformer/GAN
2. 领域细分 —— SAR 内再按任务（超分/去噪/检测/识别/生成）
3. 其他领域 —— 视频/遥感/医学/高光谱 优先于光学
4. 任务优先于方法 —— 去噪/去模糊/去雨 > 超分 > 通用复原
5. 扩散纯理论 —— 只放不含具体应用任务的扩散方法论
6. 基础方法兜底
```

## CONFIRM 检查点的必要性

分类有歧义的典型场景（必须人工确认）：
- **SAR + 扩散**：按规则进 SAR超分，但用户可能想研究扩散方法本身 → 确认
- **扩散 + SR**：进 光学SR，但若是纯扩散理论贡献 → 可能归 扩散模型
- **中文标题**：正则可能漏匹配 → CONFIRM 时让用户纠偏
- **综述论文**：可归各领域，也可归 基础方法 → 确认

**IRON RULE**：涉及 SAR 的论文，CONFIRM 检查点绝不可跳。

## 调整规则

改 `scripts/classify.py` 的 `classify()` 函数。改完重跑对历史论文无影响（分类只在入库时判定一次）。
