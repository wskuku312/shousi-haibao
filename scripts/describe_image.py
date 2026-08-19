#!/usr/bin/env python3
"""视觉识别/质检：调用 DashScope OpenAI 兼容接口描述图片。
用法: describe_image.py <图片路径> [问题]
"""

import base64
import json
import os
import sys
import urllib.request
from pathlib import Path


def load_env(path):
    env = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    return env


def data_uri(path):
    ext = Path(path).suffix.lower().lstrip(".")
    mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "gif": "gif",
            "webp": "webp", "bmp": "bmp"}.get(ext, "jpeg")
    raw = Path(path).read_bytes()
    return f"data:image/{mime};base64," + base64.b64encode(raw).decode()


def main():
    if len(sys.argv) < 2:
        print("用法: describe_image.py <图片路径> [问题]")
        sys.exit(1)
    img_path = sys.argv[1]
    prompt = sys.argv[2] if len(sys.argv) > 2 else "请用中文详细描述这张图片的内容。"
    env = load_env(Path(__file__).with_name(".env"))
    key = os.environ.get("DASHSCOPE_API_KEY") or env.get("DASHSCOPE_API_KEY") or "sk-xxx"
    base = (os.environ.get("DASHSCOPE_BASE_URL") or env.get("DASHSCOPE_BASE_URL")
            or "https://dashscope.aliyuncs.com/compatible-mode/v1")
    model = os.environ.get("VISION_MODEL") or env.get("VISION_MODEL") or "qwen3.8-max"
    if key == "sk-xxx":
        print("请设置 DASHSCOPE_API_KEY 环境变量或脚本同目录 .env")
        sys.exit(1)
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": data_uri(img_path)}},
            {"type": "text", "text": prompt},
        ]}],
        "max_tokens": 1024,
    }
    req = urllib.request.Request(
        base.rstrip("/") + "/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            body = json.loads(resp.read().decode())
        print(body["choices"][0]["message"]["content"])
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.read().decode()[:400]}")
        sys.exit(1)


if __name__ == "__main__":
    main()
