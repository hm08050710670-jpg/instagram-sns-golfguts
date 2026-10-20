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
# 配色ルール【更新版】2026-10-20：5色のみ（純白・真っ黒は使わない）
BG      = "#E8DFD3"   # ベース背景：ウォームベージュ
CARD    = "#D6C8B6"   # サブ背景・カード：サンドベージュ
ROW     = "#D6C8B6"   # 箇条書きの行（カードと同色。輪郭は罫線で出す）
INK     = "#3F3A36"   # メイン文字：チャコールブラウン
SUB     = "#8B857E"   # サブ文字：ソフトグレー
SAGE    = "#4F6B57"   # アクセント・CTA：ディープグリーン
PILL    = "#3F3A36"   # ページ番号ピル（アクセントを増やさないため文字色で）
CIRCLE  = "#D6C8B6"   # 装飾の円：サンドベージュ
LINE    = "#C4B6A3"   # 罫線（サンドベージュをやや濃く）
TAN     = "#C4B6A3"   # 番号バッジ
ON_DARK = "#E8DFD3"   # 濃色の上の文字
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
    d.text((x+pad, y + (h - f.size)/2 - 4), label, font=f, fill=ON_DARK)
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
        c = SAGE if i == page-1 else LINE
        d.ellipse([x0 + i*gap - r, y - r, x0 + i*gap + r, y + r], fill=c)

def header(d, spec, label_fill=SAGE):
    if spec.get("label"):
        pill(d, 52, 56, spec["label"], label_fill, sans(26, "Bold"))
    if spec.get("page"):
        pill(d, W-52, 56, f'{spec["page"]}/{spec["total"]}', PILL, sans(28, "Bold"), right=True)

LOGO_PATH = "../photos/logo/golfguts_wordmark_brown.png"
_logo_cache = {}
def footer(d, spec, im=None):
    if im is not None and os.path.exists(LOGO_PATH):
        if "wm" not in _logo_cache:
            lg = Image.open(LOGO_PATH).convert("RGBA"); r = 22/lg.height
            _logo_cache["wm"] = lg.resize((int(lg.width*r), 22), Image.LANCZOS)
        lg = _logo_cache["wm"]; im.paste(lg, (62, H-78), lg)
    else:
        d.text((60, H-78), "golfguts", font=sans(26, "Regular"), fill=SUB)
    if spec.get("page"): dots(d, spec["page"], spec["total"], H-66)


# ---------- 図解（線画） ----------
def _panel(d, x, y, w, h):
    d.rounded_rectangle([x, y, x+w, y+h], radius=22, fill=BG, outline=LINE, width=2)

def draw_ball_flight(d, x, y, w, h, kind="both"):
    """右打ち基準の球筋を2枚並べて比較。左：右に出て右へ／右：左に出て右へ"""
    _panel(d, x, y, w, h)
    half = w/2
    def one(ox, start_dx, bend, color, title, sub):
        gx = ox + half*0.5; gy = y + h*0.84; L = h*0.58
        d.line([gx, gy, gx, gy-L-20], fill=LINE, width=4)
        d.polygon([(gx, gy-L-34), (gx-10, gy-L-18), (gx+10, gy-L-18)], fill=LINE)
        pts=[]
        for i in range(41):
            t=i/40
            pts.append((gx + (start_dx*t + bend*t*t)*L, gy - t*L))
        d.line(pts, fill=color, width=10, joint="curve")
        ex,ey=pts[-1]; d.ellipse([ex-10,ey-10,ex+10,ey+10], fill=color)
        d.ellipse([gx-12, gy-12, gx+12, gy+12], fill=INK)
        tf=sans(30,"Bold"); tw=d.textlength(title,font=tf)
        d.text((ox+half/2-tw/2, y+26), title, font=tf, fill=color)
        sf=sans(24); sw=d.textlength(sub,font=sf)
        d.text((ox+half/2-sw/2, y+66), sub, font=sf, fill=SUB)
    one(x,        0.30, 0.30, SAGE,     "右に出て、右へ",   "打ち出しから右")
    one(x+half,  -0.30, 0.75, INK, "左に出て、右へ", "途中から大きく右")
    d.line([x+half, y+24, x+half, y+h-24], fill=LINE, width=2)
    nf=sans(22); note="※右打ちの場合。左打ちは左右が逆"; nw=d.textlength(note,font=nf)
    d.text((x+w-nw-26, y+h-40), note, font=nf, fill=SUB)

def draw_face_path(d, x, y, w, h):
    """上から見た図：ターゲットライン、外から内に入るクラブ軌道、開いたフェース"""
    import math
    _panel(d, x, y, w, h)
    cx = x + w*0.44; cy = y + h*0.58
    # ターゲットライン（横・灰）
    d.line([x+w*0.08, cy, x+w*0.92, cy], fill=LINE, width=5)
    d.polygon([(x+w*0.92+18, cy), (x+w*0.92-8, cy-12), (x+w*0.92-8, cy+12)], fill=LINE)
    d.text((x+w*0.70, cy+16), "ターゲット方向", font=sans(24), fill=SUB)
    # クラブ軌道（外から内）：右上→左下、角度35°
    a=math.radians(35); L=h*0.42
    sx,sy = cx+L*math.cos(a), cy-L*math.sin(a)
    ex,ey = cx-L*math.cos(a), cy+L*math.sin(a)
    d.line([sx,sy,ex,ey], fill=INK, width=12)
    hx,hy = ex-22*math.cos(a), ey+22*math.sin(a)
    d.polygon([(hx,hy),(ex+22*math.sin(a),ey+22*math.cos(a)),(ex-22*math.sin(a),ey-22*math.cos(a))], fill=INK)
    d.text((sx-320, sy-48), "クラブ軌道：外から内", font=sans(28,"Medium"), fill=INK)
    # ボール
    d.ellipse([cx-16, cy-16, cx+16, cy+16], fill=INK)
    # フェース：ターゲットより右（上）を向く＝垂線を15°傾ける。ボール上に太い短線＋法線矢印
    f=math.radians(15); fl=95
    d.line([cx-fl*math.sin(f), cy-fl*math.cos(f), cx+fl*math.sin(f), cy+fl*math.cos(f)], fill=SAGE, width=14)
    nx,ny = cx+150*math.cos(f), cy-150*math.sin(f)
    d.line([cx,cy,nx,ny], fill=SAGE, width=6)
    d.polygon([(nx+16*math.cos(f),ny-16*math.sin(f)),(nx-14*math.sin(f),ny-14*math.cos(f)),(nx+14*math.sin(f),ny+14*math.cos(f))], fill=SAGE)
    d.text((nx+18, ny-18), "フェース：右を向く", font=sans(28,"Medium"), fill=SAGE)
    d.text((x+26, y+h-44), "※右打ち・上から見た図。軌道とフェースの差が大きいほど曲がる", font=sans(22), fill=SUB)

DIAGRAMS = {"push_vs_pull": draw_ball_flight, "face_path": draw_face_path}

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
    d.line([120, cy, W-120, cy], fill=LINE, width=4); cy += 22
    if spec.get("sub"):
        f = serif(46); cy = text_lines(d, [spec["sub"]], 0, cy, f, INK, 60, "center", W/2)
    if spec.get("note"):
        f = sans(34); cy = text_lines(d, [spec["note"]], 0, cy + 4, f, INK, 48, "center", W/2)
    ph_top = max(cy + 30, 700)
    if spec.get("photo") and os.path.exists(spec["photo"]):
        p = photo(spec["photo"], W, H - ph_top, tuple(spec.get("photo_pos", (0.5, 0.45))))
        im.paste(p, (0, ph_top))
    else:
        d.rectangle([0, ph_top, W, H], fill=CARD)
        d.text((W/2 - 120, (ph_top + H)/2 - 20), "写真差し替え枠", font=sans(32), fill=SUB)
    return im

def render_step(spec, return_y=False):
    """写真＋見出し＋説明＋箇条書き（STEP ページ）"""
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    d.ellipse([-160, -120, 300, 340], fill=CIRCLE)
    d.rounded_rectangle([42, 118, W-42, H-110], radius=34, fill=CARD, outline=LINE, width=2)
    header(d, spec)
    y = 148
    if spec.get("diagram"):
        pw, ph = W-124, spec.get("photo_h", 500)
        DIAGRAMS[spec["diagram"]](d, 62, y, pw, ph); y += ph + 60
    elif spec.get("photo"):
        pw, ph = W-124, spec.get("photo_h", 500)
        if os.path.exists(spec["photo"]):
            rounded_paste(im, photo(spec["photo"], pw, ph, tuple(spec.get("photo_pos", (0.5, 0.45)))), 62, y)
        else:
            d.rounded_rectangle([62, y, 62+pw, y+ph], radius=26, fill=CARD)
            d.text((W/2 - 120, y + ph/2 - 20), "写真差し替え枠", font=sans(32), fill=SUB)
        y += ph + 60
    else:
        y += 20
    big = not spec.get("photo") and not spec.get("diagram")   # 写真・図なしページは文字を大きく
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
        d.rounded_rectangle([62, y, W-62, y+rh], radius=24, fill=BG, outline=LINE, width=2)
        if spec.get("numbered"):
            d.rounded_rectangle([86, y+rh/2-26, 138, y+rh/2+26], radius=14, fill=TAN)
            nf = sans(28, "Bold"); tw = d.textlength(str(i+1), font=nf)
            d.text((112 - tw/2, y+rh/2-20), str(i+1), font=nf, fill=INK)
        else:
            d.ellipse([92, y+rh/2-9, 110, y+rh/2+9], fill=SAGE)
        text_lines(d, lines, 156, y + (31 if big else 24), sans(bf_size, "Medium"), INK, lh_b)
        y += rh + (22 if big else 18)
    footer(d, spec, im)
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
        d.text((bx + 40, by + 20), spec["cta"], font=f, fill=ON_DARK)
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
    d.line([160, y, W-160, y], fill=LINE, width=3); y += 36
    if spec.get("sub"):
        y = text_lines(d, wrap(spec["sub"], 30), 0, y, sans(34), INK, 52, "center", W/2) + 30
    for item in spec.get("bullets", []):
        lines = wrap(item, 20); rh = 48 + len(lines)*52
        d.rounded_rectangle([62, y, W-62, y+rh], radius=24, fill=BG, outline=LINE, width=2)
        d.ellipse([92, y+rh/2-9, 110, y+rh/2+9], fill=SAGE)
        text_lines(d, lines, 150, y + 22, sans(38, "Medium"), INK, 52); y += rh + 18
    if spec.get("cta"):
        f = sans(44, "Bold"); tw = d.textlength(spec["cta"], font=f)
        bw, bh = tw + 80, 96; bx = W/2 - bw/2; by = max(y + 30, H - 330)
        d.rounded_rectangle([bx, by, bx+bw, by+bh], radius=bh//2, fill=SAGE)
        d.text((bx + 40, by + 20), spec["cta"], font=f, fill=ON_DARK)
        if spec.get("cta_note"):
            text_lines(d, wrap(spec["cta_note"], 34), 0, by + bh + 24, sans(26), SUB, 38, "center", W/2)
    footer(d, spec, im)
    return im

RENDER = {"cover": render_cover, "step": render_step, "list": render_list, "cta": render_cta}

if __name__ == "__main__":
    os.makedirs("out", exist_ok=True)
    specs = json.load(open("posts.json", encoding="utf-8"))
    for s in specs:
        im = RENDER[s.get("type", "step")](s)
        im.save(os.path.join("out", s["file"]), optimize=True)
        print("wrote", s["file"])
