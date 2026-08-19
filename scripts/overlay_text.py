#!/usr/bin/env python3
"""在图片左下角覆盖文字（纸纹补丁 + 打字机字体），保证拼写精确。
用法: overlay_text.py <图片> <第一行> [第二行] [--x X] [--y Y] [--size N] [--size2 N]
"""

import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


FONTS = [r"C:\Windows\Fonts\cour.ttf", r"C:\Windows\Fonts\consola.ttf",
         r"C:\Windows\Fonts\times.ttf"]


def paper_patch(size, seed=61):
    random.seed(seed)
    w, h = size
    tw, th = max(2, w // 4), max(2, h // 4)
    tile = Image.new("RGB", (tw, th), (225, 208, 173))
    px = tile.load()
    for y in range(th):
        for x in range(tw):
            n = random.randint(-8, 8)
            warm = random.randint(-2, 4)
            px[x, y] = (max(0, min(255, 225 + n + warm)),
                        max(0, min(255, 208 + n)),
                        max(0, min(255, 173 + n - warm)))
    return tile.resize((w, h), Image.Resampling.BILINEAR)


def letter_spaced(d, xy, text, font, fill, tracking=5):
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=font, fill=fill)
        x += d.textlength(ch, font=font) + tracking


def main():
    args = sys.argv[1:]
    if len(args) < 2:
        print("用法: overlay_text.py <图片> <第一行> [第二行] [--x X] [--y Y] [--size N] [--size2 N]")
        sys.exit(1)
    img_path = Path(args[0])
    lines = [a for a in args[1:] if not a.startswith("--")]
    opts = {}
    for i, a in enumerate(args[1:], start=1):
        if a in ("--x", "--y", "--size", "--size2"):
            opts[a] = int(args[i + 1])
    size1 = opts.get("--size", 42)
    size2 = opts.get("--size2", 27)
    base = Image.open(img_path).convert("RGBA")
    W, H = base.size
    x = opts.get("--x", int(W * 0.095))
    y = opts.get("--y", int(H * 0.915))
    # 纸纹补丁盖住旧文字
    max_w = max(len(t) for t in lines) * size1 * 0.72 + 140
    patch_h = len(lines) * size1 * 1.5 + 60
    patch = paper_patch((int(max_w), int(patch_h))).convert("RGBA")
    alpha = Image.new("L", patch.size, 0)
    pd = ImageDraw.Draw(alpha)
    pd.rectangle((8, 8, patch.size[0] - 8, patch.size[1] - 8), fill=250)
    alpha = alpha.filter(ImageFilter.GaussianBlur(8))
    tmp = Image.new("RGBA", base.size, (0, 0, 0, 0))
    tmp.paste(patch, (x - 30, y - 40), alpha)
    base = Image.alpha_composite(base, tmp)
    d = ImageDraw.Draw(base, "RGBA")
    font = ImageFont.truetype(FONTS[0], size1)
    small = ImageFont.truetype(FONTS[0], size2)
    letter_spaced(d, (x, y), lines[0], font, (58, 49, 38, 185))
    if len(lines) > 1:
        letter_spaced(d, (x + 6, y + int(H * 0.022)), lines[1], small,
                      (58, 49, 38, 160), tracking=8)
    base.convert("RGB").save(img_path, quality=96)
    print("text overlaid ->", img_path)


if __name__ == "__main__":
    main()
