#!/usr/bin/env python3
"""区域染色修正：把指定区域内深色中性像素染成自然粉（羽化蒙版，避开蓝/绿/强彩色）。
用法: recolor_region.py <图片> <x0%> <y0%> <x1%> <y1%> [--exclude x0,y0,x1,y1]
"""

import sys
from pathlib import Path

from PIL import Image, ImageFilter


def pink_for(l):
    if l < 70:
        return (214, 108, 148)
    if l < 110:
        return (232, 148, 170)
    return (244, 186, 200)


def main():
    args = sys.argv[1:]
    if len(args) < 5:
        print("用法: recolor_region.py <图片> <x0%> <y0%> <x1%> <y1%> [--exclude x0,y0,x1,y1]")
        sys.exit(1)
    img_path = Path(args[0])
    x0, y0, x1, y1 = (float(v) / 100 for v in args[1:5])
    excludes = []
    if "--exclude" in args:
        i = args.index("--exclude")
        parts = [float(v) / 100 for v in args[i + 1].split(",")]
        excludes.append((parts[0], parts[1], parts[2], parts[3]))
    img = Image.open(img_path).convert("RGB")
    W, H = img.size
    X0, X1 = int(x0 * W), int(x1 * W)
    Y0, Y1 = int(y0 * H), int(y1 * H)
    mask = Image.new("L", img.size, 0)
    md = mask.load()
    for y in range(Y0, Y1):
        for x in range(X0, X1):
            md[x, y] = 255
    for ex in excludes:
        for y in range(int(ex[1] * H), int(ex[3] * H)):
            for x in range(int(ex[0] * W), int(ex[2] * W)):
                md[x, y] = 0
    mask = mask.filter(ImageFilter.GaussianBlur(16))
    px = img.load()
    changed = 0
    for y in range(max(0, Y0 - 50), min(H, Y1 + 50)):
        for x in range(max(0, X0 - 50), min(W, X1 + 50)):
            a = md[x, y]
            if a == 0:
                continue
            r, g, b = px[x, y]
            l = (r + g + b) // 3
            if l >= 150:
                continue
            mx, mn = max(r, g, b), min(r, g, b)
            if b > r + 40 and b > g + 30:
                continue  # 蓝色路线
            if mx - mn > 80:
                continue  # 强彩色
            if g > r + 25 and g > b + 15:
                continue  # 绿色照片元素
            nr, ng, nb = pink_for(l)
            w = a / 255
            px[x, y] = (int(r * (1 - w) + nr * w),
                        int(g * (1 - w) + ng * w),
                        int(b * (1 - w) + nb * w))
            changed += 1
    img.save(img_path, quality=96)
    print(f"recolored {changed} px -> {img_path}")


if __name__ == "__main__":
    main()
