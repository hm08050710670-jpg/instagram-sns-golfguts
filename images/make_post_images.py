# -*- coding: utf-8 -*-
"""
GOLF GUTS Instagram 画像生成（1080x1080）
使い方: python3 make_post_images.py
  posts.json のスペックから PNG を out_images/ に出力します。
配色はナチュラルテイスト（温かい白 #F8F5EF／墨 #2B2622／オーク #C9A77C／砂色 #EFE9DF）。
フォント: Noto Sans CJK JP（Google Fontsの Noto Sans JP と同系統）
"""
import json, os, textwrap
from PIL import Image, ImageDraw, ImageFont

W = H = 1080
BG, INK, DARK, SUB, ACCENT, MUTED = "#F8F5EF", "#2B2622", "#2B2622", "#EFE9DF", "#C9A77C", "#7A7169"
ACCENT_INK = "#2B2622"  # オーク色の上の文字
SAGE = "#7E9A7A"
FONT_DIR = "/usr/share/fonts/opentype/noto/"
def font(size, weight="Regular"):
    return ImageFont.truetype(FONT_DIR + f"NotoSansCJK-{weight}.ttc", size, index=0)  # index0 = JP

KINSOKU = "。、）」』！？ー…"
def wrap(text, width):
    """日本語用の折り返し（行頭に句読点・閉じ括弧が来ないようにする）"""
    lines = []
    for para in text.split("\n"):
        if not para:
            lines.append(""); continue
        buf = ""
        for ch in para:
            buf += ch
            if len(buf) >= width:
                lines.append(buf); buf = ""
        if buf: lines.append(buf)
        # 行頭禁則：次行の先頭が句読点なら前行末へ移す
        i = 1
        while i < len(lines):
            if lines[i] and lines[i][0] in KINSOKU:
                lines[i-1] += lines[i][0]; lines[i] = lines[i][1:]
                if lines[i] == "": lines.pop(i); continue
            i += 1
    return lines

def draw_lines(d, lines, x, y, f, fill, lh):
    for ln in lines:
        d.text((x, y), ln, font=f, fill=fill)
        y += lh
    return y

def render(spec, path):
    dark = spec.get("dark", False)
    bg = DARK if dark else (SUB if spec.get("sub") else BG)
    ink = "#FFFFFF" if dark else INK
    muted = "#B8AE9F" if dark else MUTED
    im = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(im)
    M = 88  # 余白（スマホのフィード表示で欠けにくい）

    # 上部：eyebrow（枠名やページ番号）
    y = M
    if spec.get("eyebrow"):
        d.text((M, y), spec["eyebrow"], font=font(30, "Medium"), fill=muted)
    if spec.get("page"):
        p = spec["page"]; f = font(30, "Medium")
        tw = d.textlength(p, font=f)
        d.text((W - M - tw, y), p, font=f, fill=muted)
    y += 60
    # アクセントバー
    d.rectangle([M, y, M + 64, y + 4], fill=ACCENT)
    y += 56

    # 見出し
    hf = font(spec.get("head_size", 72), "Medium")
    hl = wrap(spec["head"], spec.get("head_wrap", 12))
    lh = int(spec.get("head_size", 72) * 1.35)
    for ln in hl:
        # 黄色の下線強調（見出し各行の下に細く）
        d.text((M, y), ln, font=hf, fill=ink)
        y += lh
    y += 28

    # 本文
    if spec.get("body"):
        bf = font(48, "Regular")
        y = draw_lines(d, wrap(spec["body"], 18), M, y, bf, ink if not dark else "#EDE7DD", 76)
        y += 20

    # 箇条書き
    for item in spec.get("bullets", []):
        d.ellipse([M, y + 22, M + 18, y + 40], fill=ACCENT)
        bf = font(44, "Medium")
        y = draw_lines(d, wrap(item, 17), M + 44, y, bf, ink, 66)
        y += 10

    # 下段の一言（結論）
    if spec.get("kicker"):
        kf = font(40, "Bold")
        lines = wrap(spec["kicker"], 20)
        ky = H - 190 - len(lines) * 60
        d.rectangle([M, ky - 12, M + 4, ky + len(lines) * 60 - 4], fill=ACCENT)
        draw_lines(d, lines, M + 28, ky, kf, ink, 60)

    # フッター
    fy = H - 120
    d.line([M, fy - 30, W - M, fy - 30], fill="#4A433D" if dark else "#E4DCCF", width=2)
    d.text((M, fy), spec.get("footer", "GOLF GUTS｜恵比寿" if spec.get("cta") else "GOLF GUTS｜恵比寿 マンツーマンゴルフレッスン"), font=font(28, "Medium"), fill=muted)
    if spec.get("cta"):
        cf = font(28, "Bold"); c = spec["cta"]; tw = d.textlength(c, font=cf)
        pad = 22
        d.rounded_rectangle([W - M - tw - pad * 2, fy - 12, W - M, fy + 48], radius=28, fill=ACCENT)
        d.text((W - M - tw - pad, fy - 2), c, font=cf, fill=ACCENT_INK)

    im.save(path, optimize=True)

if __name__ == "__main__":
    os.makedirs("out", exist_ok=True)
    specs = json.load(open("posts.json", encoding="utf-8"))
    for s in specs:
        render(s, os.path.join("out", s["file"]))
        print("wrote", s["file"])
