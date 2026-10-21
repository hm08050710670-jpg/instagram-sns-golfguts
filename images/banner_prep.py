# -*- coding: utf-8 -*-
"""
依頼者提供の初回スイングdockバナー（2026-10-21）を、リールの背景色に合わせて変換する。
  python3 images/banner_prep.py   → photos/banners/*.png から photos/banners/prepped/*.png を作る
- 背景（クリーム）と装飾の円 → リールの背景 #E8DFD3 に置き換え（円はクリップされて見えるため消す）
- 文字・区切り線・ボタンは元の色のまま残す（ボタン上の白文字は #E8DFD3 になる＝配色ルールの「濃色面の上の文字」と同じ）
- 端の余白を詰め、リールの幅（左右64pxの余白）に収まる 952px 幅に縮小
"""
import os, glob
import numpy as np
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "photos", "banners"); OUT = os.path.join(SRC, "prepped")
BG = np.array([0xE8, 0xDF, 0xD3], float)
LINE = np.array([0xC4, 0xB6, 0xA3], float)
WIDTH = 952

def prep(path):
    im = np.array(Image.open(path).convert("RGB")).astype(float)
    lum = im @ [0.299, 0.587, 0.114]
    bg_l = np.percentile(lum, 90)            # 最も多いクリームの明るさ
    diff = bg_l - lum
    a = np.clip((diff - 28) / 30.0, 0, 1)[..., None]   # 背景・装飾の円（差15〜25）→ 0、文字・ボタン → 1
    out = BG * (1 - a) + im * a
    # 見出し下の区切り線（円と同じ薄さのため上で消える）を、配色ルールの罫線色 #C4B6A3 で同じ位置に引き直す
    h, w = diff.shape; c0, c1 = int(w * 0.2), int(w * 0.8)
    hits = [y for y in range(h) if 8 < diff[y, c0:c1].mean() < 30 and diff[y, c0:c1].std() < 4]
    hits = [y for y in hits if y - hits[0] <= 2]   # 最初の1本だけ（2本に見えないように）
    for y in hits:
        if True:
            xs_ = np.where(diff[y] > 8)[0]
            out[y, xs_.min():xs_.max() + 1] = LINE
    img = Image.fromarray(out.clip(0, 255).astype(np.uint8))
    # 文字のある範囲だけ切り出す（上下左右の余白を詰める）
    mask = (a[..., 0] > 0.5)
    ys, xs = np.where(mask)
    pad = 24
    box = (max(xs.min() - pad, 0), max(ys.min() - pad, 0), min(xs.max() + pad, im.shape[1]), min(ys.max() + pad, im.shape[0]))
    img = img.crop(box)
    if img.width > WIDTH:
        img = img.resize((WIDTH, round(img.height * WIDTH / img.width)), Image.LANCZOS)
    return img

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for f in sorted(glob.glob(os.path.join(SRC, "*.png"))):
        img = prep(f); img.save(os.path.join(OUT, os.path.basename(f))); print("wrote", os.path.basename(f), img.size)
