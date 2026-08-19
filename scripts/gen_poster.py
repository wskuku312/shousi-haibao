#!/usr/bin/env python3
"""AI 生成手撕海报（DashScope qwen-image-3.0）。
用法: gen_poster.py <配置名> --src-dir <素材目录> [--ref <参考图>] [--out <输出目录>] [--variant line|river]
配置名: lotus | peakland | boat | puzhehei4（可在 CONFIGS 中新增）
变体: line = 贯穿钴蓝路线（默认）；river = 改为手绘河流
"""

import argparse
import base64
import io
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image, ImageOps


ENDPOINT = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
MODEL = "qwen-image-3.0"
SIZE = "1536*2560"


def load_env(path):
    env = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    return env


COMMON = """请参考参考图1的剪切和排版手法，用参考图2/3的{SCENE}实景照片，制作一张竖版3:5的复古旅行手账式撕纸拼贴海报：
1) 剪切手法：所有照片手撕毛边+白色纸芯纤维边；整块不规则撕块、半轮廓撕法、可有一小块精确剪影混用；碎片下有极轻投影。
2) 排版：非网格非对称，碎片沿S形路径从右上铺到左下；大小对比悬殊；照片块之间不互叠、靠奶白纸缝隔开；窄缝让蓝色路线穿过像缝合线。
3) 手绘底图（重点）：{MAP}；铅笔/淡褐墨线、低饱和淡彩（灰绿、灰褐），散布整张纸面作为底图；留白三到四成。
4) 照片内容：{PHOTOS}。
5) 装饰：点缀少量{ACCENT}小色块，小面积克制。
6) 文字：左下角一行小号打字机英文 {TEXT1}，下面一行更小的 PUZHEHEI，拼写必须正确。
7) 禁止：人物（含远景人影）、水印、杂乱文字、大标题、霓虹色、3D效果、整齐矩形照片、拍立得白框。"""


CONFIGS = {
    "lotus": {
        "files": ["4f70cb3eddffd8d7992c7973e7e1a803.jpg",
                  "57b4fb6a55407c0e8bc31a87aec879e1.jpg"],
        "prompt": COMMON.format(
            SCENE="普者黑荷花",
            MAP="普者黑喀斯特地貌风格：圆润锥形峰林、峰丘等高线、溶洞与地下河示意、湖泊水网线稿",
            PHOTOS="荷塘照片作为最大主块偏上，荷花特写作为中块，可再裁一块荷塘局部做小碎片",
            ACCENT="粉色荷花花瓣（散落点缀空白，稀疏自然）",
            TEXT1="Lotus / Pond / Silence",
        ) + "；禁止黑色或墨色荷花（所有荷花必须是粉色）",
    },
    "peakland": {
        "files": ["67a1ffb6a8eaaa23f2646124d4292ca7.jpg",
                  "d11fd73a09fde3c5f37a4ab986cb1b81.jpg"],
        "prompt": COMMON.format(
            SCENE="普者黑峰林田园",
            MAP="普者黑喀斯特地貌风格：圆润锥形峰林、峰丘等高线、溶洞与地下河示意、湿地水网/湖塘线稿",
            PHOTOS="俯瞰喀斯特峰林湿地（夕阳金光）作最大主块偏上；峰林村庄远景（已裁掉人物）作中块；可再裁一块湿地水面局部做小碎片",
            ACCENT="暖金色（与夕阳呼应）",
            TEXT1="Sun / Water / Ridge",
        ),
    },
    "boat": {
        "files": ["681fab74ba4fa4fd0ebb695fe1ec0e2a.jpg",
                  "67a1ffb6a8eaaa23f2646124d4292ca7.jpg"],
        "prompt": COMMON.format(
            SCENE="普者黑船游山水",
            MAP="水岸喀斯特地貌地图：沿水岸锥形峰林、峰丘等高线、湖泊水网与水路线稿、水面波纹、芦苇/溶洞示意",
            PHOTOS="粉色小船游湖照片作最大主块偏上居中（小船完整：船头、船身、荷叶彩绘）；俯瞰喀斯特峰林湿地作中块；可再裁一块山岸水面局部做小碎片",
            ACCENT="粉色（与粉色小船呼应）",
            TEXT1="Boat / Mist / Karst",
        ),
    },
    "puzhehei4": {
        "files": ["67a1ffb6a8eaaa23f2646124d4292ca7.jpg",
                  "681fab74ba4fa4fd0ebb695fe1ec0e2a.jpg",
                  "4f70cb3eddffd8d7992c7973e7e1a803.jpg",
                  "03680c9769930ba6b5d9c0c9d1fe8123.jpg"],
        "prompt": """请用这张参考图制作一张竖版3:5复古旅行手账式撕纸拼贴海报。参考图是一张2x2四宫格拼板，包含四张普者黑实景照片：左上=粉色小船游湖、右上=俯瞰喀斯特峰林湿地（夕阳）、左下=盛夏荷塘粉荷、右下=湿地荷塘芦苇与石山。
1) 剪切手法：把四格照片分别作为四块独立的手撕碎片（白色纸芯纤维毛边、带极轻投影）；主片用右上俯瞰峰林湿地放中上居中（最大），小船放右中，荷塘放左中，湿地小片放右下；禁止整齐矩形、描边、拍立得白框。
2) 排版：非网格非对称，碎片沿S形路径排布，大小对比悬殊，碎片间靠奶白纸缝隔开、互不重叠。
3) 手绘底图（重点）：纸面预印层为普者黑喀斯特地貌地图风格——圆润锥形峰林、峰丘等高线、溶洞与地下河示意、湖泊水网线稿；铅笔/淡褐墨线、低饱和淡彩（灰绿、灰褐）；留白占三到四成。
4) 蓝色路线：一条手绘钴蓝蜿蜒线从左上贯穿到右下，从碎片纸缝间穿过像缝合线；单条连续、无箭头、无分叉。
5) 装饰：少量粉色（呼应荷花与小船）小色块/花瓣点缀空白，小面积克制。
6) 文字：左下角一行小号打字机英文 Ridge / Bloom / Drift，下面一行更小的 PUZHEHEI，字距拉开、灰褐色，拼写必须正确。
7) 禁止：人物（含远景人影）、水印、杂乱文字、大标题、霓虹色、3D效果、整齐矩形照片、拍立得白框。""",
    },
}


def data_uri(path, max_dim=1536, quality=90):
    img = Image.open(path).convert("RGB")
    img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=quality)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def resolve_prompt(cfg, variant):
    prompt = cfg["prompt"]
    if variant == "river":
        prompt = prompt.replace(
            "窄缝让蓝色路线穿过像缝合线",
            "窄缝让手绘河流穿过，河流蜿蜒曲折、宽窄自然变化、带支流和水流短笔触，像一条河蜿蜒流过整张拼贴")
        prompt = prompt.replace(
            "4) 蓝色路线：一条手绘钴蓝蜿蜒线从左上贯穿到右下，从碎片纸缝间穿过像缝合线；单条连续、无箭头、无分叉。",
            "4) 手绘河流（重点）：画面中贯穿的蓝色元素改为一条手绘河流——像手绘地图上的河流水系：蜿蜒曲折、宽窄自然变化、带一两处小支流和细水流短笔触，颜色为钴蓝/淡蓝，从左上蜿蜒流过碎片纸缝到右下，像一条河穿过整张拼贴；不要等宽细线、不要箭头、不要过多分叉，保持手绘水彩/铅笔质感。")
        prompt = prompt.replace("蓝色路线", "手绘河流")
    return prompt


def contact_sheet(files, src_dir, cell=768, gutter=14):
    """超过3张输入时，拼成2x2四宫格拼板作为单张输入。"""
    n = len(files)
    cols = 2
    rows = (n + 1) // 2
    w = cols * cell + (cols + 1) * gutter
    h = rows * cell + (rows + 1) * gutter
    sheet = Image.new("RGB", (w, h), (255, 255, 255))
    for i, f in enumerate(files):
        img = Image.open(src_dir / f).convert("RGB")
        img = ImageOps.fit(img, (cell, cell), method=Image.Resampling.LANCZOS)
        r, c = divmod(i, cols)
        sheet.paste(img, (gutter + c * (cell + gutter), gutter + r * (cell + gutter)))
    buf = io.BytesIO()
    sheet.save(buf, "JPEG", quality=90)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def call_api(key, ref, files, src_dir, prompt):
    content = []
    if ref:
        content.append({"image": data_uri(ref)})
    if len(files) > 3:
        content.append({"image": contact_sheet(files, src_dir)})
    else:
        for f in files:
            content.append({"image": data_uri(src_dir / f)})
    content.append({"text": prompt})
    payload = {
        "model": MODEL,
        "input": {"messages": [{"role": "user", "content": content}]},
        "parameters": {"size": SIZE, "n": 1, "prompt_extend": False,
                       "watermark": False},
    }
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {key}",
                 "Content-Type": "application/json"},
        method="POST",
    )
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=600) as resp:
                body = json.loads(resp.read().decode())
            return body["output"]["choices"][0]["message"]["content"][0]["image"]
        except urllib.error.HTTPError as e:
            detail = e.read().decode()[:500]
            print(f"[attempt {attempt+1}] HTTP {e.code}: {detail}")
            if e.code == 429:
                time.sleep(40 * (attempt + 1))
                continue
            raise
    raise RuntimeError("rate limit retries exhausted")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name", choices=list(CONFIGS))
    ap.add_argument("--src-dir", required=True)
    ap.add_argument("--ref", default=None, help="参考拼贴图路径（可选）")
    ap.add_argument("--out", default=str(Path.cwd() / "output"))
    ap.add_argument("--variant", choices=["line", "river"], default="line",
                    help="line=钴蓝路线（默认），river=手绘河流")
    args = ap.parse_args()
    cfg = CONFIGS[args.name]
    env = load_env(Path(__file__).with_name(".env"))
    key = os.environ.get("DASHSCOPE_API_KEY") or env.get("DASHSCOPE_API_KEY") or "sk-xxx"
    if key == "sk-xxx":
        raise SystemExit("请设置 DASHSCOPE_API_KEY 环境变量或脚本同目录 .env")
    src_dir = Path(args.src_dir)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"poster-{args.name}-v1.png"
    print(f"[{args.name}] generating...")
    ref_path = Path(args.ref) if args.ref else None
    prompt = resolve_prompt(cfg, args.variant)
    url = call_api(key, ref_path, cfg["files"], src_dir, prompt)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=300) as resp:
        raw = resp.read()
    tmp = Path(os.environ.get("TEMP", ".")) / f"poster_{args.name}_raw.png"
    tmp.write_bytes(raw)
    img = Image.open(tmp).convert("RGB")
    if img.size != (1800, 3000):
        img = ImageOps.fit(img, (1800, 3000), method=Image.Resampling.LANCZOS,
                           centering=(0.5, 0.5))
    img.save(out, quality=96)
    print(f"[{args.name}] saved: {out}")


if __name__ == "__main__":
    main()
