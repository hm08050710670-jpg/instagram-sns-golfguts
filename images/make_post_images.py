# -*- coding: utf-8 -*-
"""
GOLF GUTS Instagram 画像生成（1080x1350 縦長 4:5）
使い方: cd images && python3 make_post_images.py
  posts.json のスペックから PNG を out/ に出力します。

デザイン：GOLF GUTS公式Instagramの既存投稿の型に合わせる（2026-10-20 依頼者指示）
  - 生成りの地（#F4F0E4）、左上に大きな淡い円、角丸カード、白い箇条書きの行
  - 左上：セージ色のラベル（STEP 01 / 価格案内 など）、右上：グレーのページ番号
  - 表紙：明朝体の大見出し＋下半分に写真
  - 下部：golfguts ＋ ページのドット
テンプレート（spec["type"]）：cover / step / list / cta
フォント：Noto Sans CJK JP／Noto Serif CJK JP
"""
import json, os
from PIL import Image, ImageDraw, ImageFont, ImageOps

W, H = 1080, 1350
BG      = "#F4F0E4"   # 生成り
CARD    = "#F7F4EC"   # カード地
ROW     = "#FCF8F4"   # 箇条書きの行
INK     = "#2B2622"   # 文字
SUB     = "#6E6660"   # サブ文字
SAGE    = "#7C9070"   # ラベル・ドット・CTA
PILL    = "#5C5450"   # ページ番号
CIRCLE  = "#E4DCD0"   # 装飾の円
LINE    = "#DAD5CA"   # 枠線
TAN     = "#D9C58F"   # 番号バッジ
FONT_DIR = "/usr/share/fonts/opentype/noto/"

def sans(size, w="Regular"): return ImageFont.truetype(FONT_DIR + f"NotoSansCJK-{w}.ttc", size, index=0)
def serif(size, w="Regular"): return ImageFont.truetype(FONT_DIR + f"NotoSerifCJK-{w}.ttc", size, index=0)

KINSOKU = "。、）」』！？ー…"
def wrap(text, width):
    lines = []
    for para in text.split("\n"):
        if not para: lines.append(""); continue
        buf = ""
        for ch in para:
            buf += ch
            if len(buf) >= width: lines.append(buf); buf = ""
        if buf: lines.append(buf)
    i = 1
    while i < len(lines):
        if lines[i] and lines[i][0] in KINSOKU:
            lines[i-1] += lines[i][0]; lines[i] = lines[i][1:]
            if lines[i] == "": lines.pop(i); continue
        i += 1
    return lines

def text_lines(d, lines, x, y, f, fill, lh, align="left", cx=None):
    for ln in lines:
        if align == "center":
            tw = d.textlength(ln, font=f); d.text((cx - tw/2, y), ln, font=f, fill=fill)
        else:
            d.text((x, y), ln, font=f, fill=fill)
        y += lh
    return y

def pill(d, x, y, label, fill, f, pad=26, h=58, right=False):
    tw = d.textlength(label, font=f)
    w = tw + pad*2
    if right: x = x - w
    d.rounded_rectangle([x, y, x+w, y+h], radius=h//2, fill=fill)
    d.text((x+pad, y + (h - f.size)/2 - 4), label, font=f, fill="#FFFFFF")
    return w

def photo(path, w, h, pos=(0.5, 0.45)):
    im = ImageOps.exif_transpose(Image.open(path).convert("RGB"))
    return ImageOps.fit(im, (w, h), Image.LANCZOS, centering=pos)

def rounded_paste(base, im, x, y, r=26):
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, im.width-1, im.height-1], radius=r, fill=255)
    base.paste(im, (x, y), mask)

def dots(d, page, total, y):
    gap = 26; r = 7
    x0 = W/2 - (total-1)*gap/2
    for i in range(total):
        c = SAGE if i == page-1 else "#C9C3B6"
        d.ellipse([x0 + i*gap - r, y - r, x0 + i*gap + r, y + r], fill=c)

def header(d, spec, label_fill=SAGE):
    if spec.get("label"):
        pill(d, 52, 56, spec["label"], label_fill, sans(26, "Bold"))
    if spec.get("page"):
        pill(d, W-52, 56, f'{spec["page"]}/{spec["total"]}', PILL, sans(28, "Bold"), right=True)

def footer(d, spec):
    d.text((60, H-78), "golfguts", font=sans(26, "Regular"), fill=SUB)
    if spec.get("page"): dots(d, spec["page"], spec["total"], H-66)

# ---------- templates ----------
def render_cover(spec):
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    d.ellipse([-120, -180, 330, 270], fill=CIRCLE)
    header(d, spec)
    cy = 150
    if spec.get("eyebrow"):
        f = serif(60); cy = text_lines(d, [spec["eyebrow"]], 0, cy, f, INK, 76, "center", W/2) + 4
    f = serif(spec.get("title_size", 150), "Bold")
    for ln in spec["title"].split("\n"):
        tw = d.textlength(ln, font=f); d.text((W/2 - tw/2, cy), ln, font=f, fill=INK); cy += spec.get("title_size", 150) + 10
    cy += 44
    d.line([120, cy, W-120, cy], fill="#CFC8B8", width=4); cy += 22
    if spec.get("sub"):
        f = serif(46); cy = text_lines(d, [spec["sub"]], 0, cy, f, INK, 60, "center", W/2)
    if spec.get("note"):
        f = sans(34); cy = text_lines(d, [spec["note"]], 0, cy + 4, f, INK, 48, "center", W/2)
    ph_top = max(cy + 30, 700)
    if spec.get("photo") and os.path.exists(spec["photo"]):
        p = photo(spec["photo"], W, H - ph_top, tuple(spec.get("photo_pos", (0.5, 0.45))))
        im.paste(p, (0, ph_top))
    else:
        d.rectangle([0, ph_top, W, H], fill="#E2DCCF")
        d.text((W/2 - 120, (ph_top + H)/2 - 20), "写真差し替え枠", font=sans(32), fill=SUB)
    return im

def render_step(spec, return_y=False):
    """写真＋見出し＋説明＋箇条書き（STEP ページ）"""
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    d.ellipse([-160, -120, 300, 340], fill=CIRCLE)
    d.rounded_rectangle([42, 118, W-42, H-110], radius=34, fill=CARD, outline=LINE, width=2)
    header(d, spec)
    y = 148
    if spec.get("photo"):
        pw, ph = W-124, spec.get("photo_h", 500)
        if os.path.exists(spec["photo"]):
            rounded_paste(im, photo(spec["photo"], pw, ph, tuple(spec.get("photo_pos", (0.5, 0.45)))), 62, y)
        else:
            d.rounded_rectangle([62, y, 62+pw, y+ph], radius=26, fill="#E2DCCF")
            d.text((W/2 - 120, y + ph/2 - 20), "写真差し替え枠", font=sans(32), fill=SUB)
        y += ph + 60
    else:
        y += 20
    big = not spec.get("photo")          # 写真なしページは文字を大きく
    hs = spec.get("head_size", 84 if big else 72)
    bf_size, lh_b, wrap_b = (46, 62, 18) if big else (38, 52, 20)
    f = sans(hs, "Bold")
    y = text_lines(d, wrap(spec["head"], 12 if big else 13), 64, y + (30 if big else 0), f, INK, int(hs*1.3))
    if spec.get("sub"):
        y = text_lines(d, wrap(spec["sub"], 22 if big else 24), 64, y + 8, sans(36 if big else 32), SUB, 52 if big else 46) + (34 if big else 24)
    else:
        y += 24
    for i, item in enumerate(spec.get("bullets", [])):
        lines = wrap(item, wrap_b)
        rh = (62 if big else 48) + len(lines)*lh_b
        d.rounded_rectangle([62, y, W-62, y+rh], radius=24, fill=ROW, outline=LINE, width=2)
        if spec.get("numbered"):
            d.rounded_rectangle([86, y+rh/2-26, 138, y+rh/2+26], radius=14, fill=[TAN, "#C9D3BC", "#E1D8C3"][i % 3])
            nf = sans(28, "Bold"); tw = d.textlength(str(i+1), font=nf)
            d.text((112 - tw/2, y+rh/2-20), str(i+1), font=nf, fill=INK)
        else:
            d.ellipse([92, y+rh/2-9, 110, y+rh/2+9], fill=SAGE)
        text_lines(d, lines, 156, y + (31 if big else 24), sans(bf_size, "Medium"), INK, lh_b)
        y += rh + (22 if big else 18)
    footer(d, spec)
    return (im, y) if return_y else im

def render_list(spec):
    """写真なし。見出し＋説明＋箇条書き（番号付き可）＋小さな写真3枚（任意）＋CTAボタン（任意）"""
    spec = dict(spec); spec.pop("photo", None)
    im, y_end = render_step(spec, return_y=True)
    d = ImageDraw.Draw(im)
    if spec.get("cta"):
        f = sans(44, "Bold"); tw = d.textlength(spec["cta"], font=f)
        bw, bh = tw + 80, 96
        bx = 62
        by = H - 300 if y_end + 30 <= H - 300 else min(y_end + 30, H - 110 - bh - 70)
        d.rounded_rectangle([bx, by, bx+bw, by+bh], radius=bh//2, fill=SAGE)
        d.text((bx + 40, by + 20), spec["cta"], font=f, fill="#FFFFFF")
        if spec.get("cta_note"):
            d.text((62, by + bh + 22), spec["cta_note"], font=sans(28), fill=SUB)
    return im

def render_cta(spec):
    """最終ページ：料金・予約案内"""
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    d.ellipse([-160, -120, 300, 340], fill=CIRCLE)
    d.rounded_rectangle([42, 118, W-42, H-110], radius=34, fill=CARD, outline=LINE, width=2)
    header(d, spec)
    y = 190
    f = serif(spec.get("head_size", 88), "Bold")
    y = text_lines(d, spec["head"].split("\n"), 0, y, f, INK, int(spec.get("head_size", 88)*1.25), "center", W/2) + 20
    d.line([160, y, W-160, y], fill="#CFC8B8", width=3); y += 36
    if spec.get("sub"):
        y = text_lines(d, wrap(spec["sub"], 30), 0, y, sans(34), INK, 52, "center", W/2) + 30
    for item in spec.get("bullets", []):
        lines = wrap(item, 20); rh = 48 + len(lines)*52
        d.rounded_rectangle([62, y, W-62, y+rh], radius=24, fill=ROW, outline=LINE, width=2)
        d.ellipse([92, y+rh/2-9, 110, y+rh/2+9], fill=SAGE)
        text_lines(d, lines, 150, y + 22, sans(38, "Medium"), INK, 52); y += rh + 18
    if spec.get("cta"):
        f = sans(44, "Bold"); tw = d.textlength(spec["cta"], font=f)
        bw, bh = tw + 80, 96; bx = W/2 - bw/2; by = max(y + 30, H - 330)
        d.rounded_rectangle([bx, by, bx+bw, by+bh], radius=bh//2, fill=SAGE)
        d.text((bx + 40, by + 20), spec["cta"], font=f, fill="#FFFFFF")
        if spec.get("cta_note"):
            text_lines(d, wrap(spec["cta_note"], 34), 0, by + bh + 24, sans(26), SUB, 38, "center", W/2)
    footer(d, spec)
    return im

RENDER = {"cover": render_cover, "step": render_step, "list": render_list, "cta": render_cta}

if __name__ == "__main__":
    os.makedirs("out", exist_ok=True)
    specs = json.load(open("posts.json", encoding="utf-8"))
    for s in specs:
        im = RENDER[s.get("type", "step")](s)
        im.save(os.path.join("out", s["file"]), optimize=True)
        print("wrote", s["file"])
