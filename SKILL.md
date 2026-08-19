---
name: shousi-haibao
description: 制作"手撕海报"——复古旅行手账式撕纸拼贴竖版海报（3:5）。Use when the user asks to create or transform photos into hand-torn collage travel posters (撕纸拼贴海报 / 手撕海报 / 复古手账拼贴旅行海报), wants the style learned from a reference collage image, wants a scenery-themed hand-drawn base map (e.g. 普者黑喀斯特地貌、荷塘水系、水岸峰林), or wants an S-shaped torn-photo layout with a hand-drawn blue route line and small typewriter text. 工作流：分析素材与参考图 → 按风景特色设计手绘底图 → 用视觉模型生成（DashScope qwen-image-3.0）→ 视觉质检 → 程序化修正文字/颜色。
---

# 手撕海报 · Hand-Torn Collage Poster

复古旅行手账式撕纸拼贴海报：手撕白纤维毛边、S 形碎片排布、钴蓝路线贯穿、按风景特色设计手绘底图、左下角打字机英文小字。

## 工作流

1. **识别素材**：对每张风景照运行 `python scripts/describe_image.py "<图片路径>" "请用中文描述：主体、构图方向、色调光线、主要元素、有无人物、氛围，200字内"`，建立素材清单。
2. **学习参考图**（可选）：用户提供参考拼贴图时，先运行 `describe_image.py` 分析其剪切与排版手法，对照 references/workflow.md 的"手法清单"。
3. **设计手绘底图**：按风景的标志元素选择底图主题（见 references/workflow.md"底图主题表"；普者黑→喀斯特峰林+等高线+溶洞+湖网）。
4. **组装提示词**：用 references/prompts.md 模板（剪切手法、S 形排版、手绘底图、照片内容、呼应色、文字、禁止项），按素材替换照片内容。
5. **生成**：`python scripts/gen_poster.py <配置名> --src-dir <素材目录> [--ref <参考图>] --out <输出目录> [--variant line|river]`。模型 qwen-image-3.0，尺寸 1536x2560，输出放大到 1800x3000。`--variant river` 把贯穿钴蓝路线改为手绘河流（水域主题或用户要求时使用；见 references/prompts.md）。
6. **质检**：运行 `describe_image.py` 按 references/workflow.md"质检清单"逐条检查。
7. **修正**：
   - 文字乱码/拼错 → `scripts/overlay_text.py <图片> <第一行> <第二行>`
   - 黑色/异色元素（如黑色荷花）→ 先 `describe_image.py` 定位坐标，再 `scripts/recolor_region.py <图片> <x0> <y0> <x1> <y1>`
   - 额度问题 → 先 `scripts/probe_quota.py`
   - 布局/风格不达标 → 调整提示词重新生成，再做文字/颜色修正。

## 硬性规则

- 照片边界必须是不规则手撕毛边+白色纸芯纤维边，禁止整齐矩形/描边/拍立得白框。
- 蓝色路线单条连续、从左上贯穿到右下、穿过碎片纸缝；不画箭头、不分叉。
- 无人物（含远景人影）、无水印、无杂乱文字。
- 照片轻微做旧（降饱和/低对比），保持实景真实感。
- 文字默认左下角打字机英文，主文案≤5词，第二行 PUZHEHEI 或用户指定。

## 资源

- scripts/gen_poster.py — AI 生成（DashScope qwen-image-3.0，参考图+风景照）
- scripts/describe_image.py — 视觉识别/质检
- scripts/overlay_text.py — 覆盖文字（纸纹补丁+打字机字体）
- scripts/recolor_region.py — 区域染色修正（羽化蒙版）
- scripts/probe_quota.py — 探测模型额度
- references/workflow.md — 手法清单、底图主题表、质检清单、修正流程
- references/prompts.md — 提示词模板（通用/荷塘/峰林/船游）

## 环境

- 需要阿里云百炼 API Key：环境变量 `DASHSCOPE_API_KEY` 或脚本同目录 `.env`。
- 生成模型 `qwen-image-3.0`；免费额度用尽会返回 403，先运行 `probe_quota.py` 确认；恢复方法：百炼控制台充值并关闭"仅使用免费额度"。
- 输出默认 1800x3000 PNG。
