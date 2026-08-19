#!/usr/bin/env python3
"""探测 DashScope 图像模型额度。
用法: probe_quota.py [model]  （默认 qwen-image-3.0）
"""

import json
import os
import sys
import urllib.error
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


def main():
    model = sys.argv[1] if len(sys.argv) > 1 else "qwen-image-3.0"
    env = load_env(Path(__file__).with_name(".env"))
    key = os.environ.get("DASHSCOPE_API_KEY") or env.get("DASHSCOPE_API_KEY") or "sk-xxx"
    base = (os.environ.get("DASHSCOPE_BASE_URL") or env.get("DASHSCOPE_BASE_URL")
            or "https://dashscope.aliyuncs.com/compatible-mode/v1")
    req = urllib.request.Request(
        base.rstrip("/") + "/models",
        headers={"Authorization": f"Bearer {key}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode())
        ids = [m.get("id") for m in body.get("data", [])]
        print(f"OK: 可访问模型列表（{len(ids)}个）")
        print(f"{model} 在列表中: {model in ids}")
    except urllib.error.HTTPError as e:
        detail = e.read().decode()[:400]
        print(f"HTTP {e.code}: {detail}")
        if "FreeTierOnly" in detail or e.code == 403:
            print("提示：免费额度已用尽。请到百炼控制台充值并关闭'仅使用免费额度'模式。")


if __name__ == "__main__":
    main()
