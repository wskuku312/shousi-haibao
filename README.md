# 手撕海报 · shousi-haibao

复古旅行手账式撕纸拼贴海报生成 Skill（Codex Skill）。把风景照片变成竖版 3:5 手撕拼贴旅行海报：手撕白纤维毛边、S 形碎片排布、钴蓝路线贯穿、按风景特色设计手绘底图（如普者黑喀斯特地貌）、左下角打字机英文小字。

## 特性

- 自动分析参考拼贴图的剪切与排版手法（整块撕块 / 半轮廓撕法 / 精确剪影 / 白纤维毛边）
- 按风景标志元素设计手绘底图（喀斯特峰林、荷塘水系、水岸峰林、湿地水网……）
- 视觉模型生成海报（DashScope qwen-image-3.0，1536x2560 → 1800x3000）
- 视觉模型质检 + 程序化修正（文字精确覆盖、黑色元素染色、额度探测）
- 支持一次使用 4 张以上照片：自动拼成 2x2 四宫格拼板输入，每格分别做成独立手撕碎片

## 目录结构

```text
shousi-haibao/
├── SKILL.md                  # 技能说明（Codex 自动发现）
├── agents/openai.yaml        # 界面元数据（显示名：手撕海报）
├── references/
│   ├── workflow.md           # 剪切/排版手法、底图主题表、质检清单、修正流程
│   └── prompts.md            # 提示词模板（通用/荷塘/峰林/船游）
└── scripts/
    ├── gen_poster.py         # AI 生成海报
    ├── describe_image.py     # 视觉识别/质检
    ├── overlay_text.py       # 精确覆盖文字（纸纹补丁+打字机字体）
    ├── recolor_region.py     # 区域染色修正（羽化蒙版）
    └── probe_quota.py        # 探测模型额度
```

## 安装

方式一：把本仓库放到 `~/.codex/skills/shousi-haibao`（Windows：`C:\Users\<你>\.codex\skills\shousi-haibao`）。

方式二：用 Codex skill-installer 从本仓库安装：

```bash
python ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo wskuku312/shousi-haibao --path . --name shousi-haibao
```

## 环境要求

- Python 3 + Pillow
- 阿里云百炼 API Key（`DASHSCOPE_API_KEY`，可放 `scripts/.env` 或环境变量）
- `qwen-image-3.0` 模型额度：免费额度用尽会返回 403，需在百炼控制台充值并关闭"仅使用免费额度"模式

## 快速使用

```bash
# 1. 识别素材
python scripts/describe_image.py "<风景照片>" "请用中文描述：主体、构图、色调、元素、有无人物、氛围"

# 2. 生成海报（lotus / peakland / boat，或按 prompts.md 模板新增配置）
python scripts/gen_poster.py lotus \
  --src-dir "<素材目录>" \
  --ref "<参考拼贴图>" \
  --out "<输出目录>"

# 四图合一示例（无需参考图，自动四宫格拼板）
python scripts/gen_poster.py puzhehei4 \
  --src-dir "<素材目录>" \
  --out "<输出目录>"

# 3. 质检
python scripts/describe_image.py "<输出海报>" "请检查：碎片分布、手撕毛边、蓝线、底图主题、文字、人物"

# 4. 修正
python scripts/overlay_text.py "<海报>" "Lotus / Pond / Silence" "PUZHEHEI"
python scripts/recolor_region.py "<海报>" 75 33 96 46   # 黑色元素染粉（坐标为百分比）
python scripts/probe_quota.py
```

## 设计原则

- 手撕毛边 + 白色纸芯纤维边，禁止整齐矩形边框
- S 形碎片排布，大小对比悬殊，纸缝留白
- 手绘底图体现风景标志地貌（普者黑 → 喀斯特峰林/溶洞/水网）
- 无人物、无水印；左下角打字机英文小字，拼写必须正确

详细手法与模板见 `references/workflow.md` 和 `references/prompts.md`。
