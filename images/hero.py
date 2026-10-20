# -*- coding: utf-8 -*-
"""hero テンプレート：1枚目用。大きな見出し＋線画イラスト（5色のみ、写真・ロゴ・肖像なし）"""
import math, importlib.util
from PIL import Image, ImageDraw
sm = importlib.util.spec_from_file_location("m", "make_post_images.py"); m = importlib.util.module_from_spec(sm); sm.loader.exec_module(m)
W,H,BG,CARD,INK,SUB,SAGE,LINE = m.W,m.H,m.BG,m.CARD,m.INK,m.SUB,m.SAGE,m.LINE

def art_hole18(d, cx, cy):
    # グリーン＋ホール＋旗、背後に大きな「18」
    f = m.serif(420, "Bold"); t="18"; tw=d.textlength(t,font=f)
    d.text((cx-tw/2, cy-330), t, font=f, fill=CARD)
    d.ellipse([cx-300, cy+40, cx+300, cy+200], fill=SAGE)
    d.ellipse([cx-24, cy+108, cx+24, cy+132], fill=INK)
    d.line([cx, cy+120, cx, cy-140], fill=INK, width=8)
    d.polygon([(cx, cy-140),(cx+150, cy-100),(cx, cy-60)], fill=INK)
    d.ellipse([cx-250, cy+60, cx-220, cy+90], fill=BG)  # ボール

def art_ruler46(d, cx, cy):
    # ドライバーの線画＋定規＋46"
    f = m.serif(300, "Bold"); t='46"'; tw=d.textlength(t,font=f)
    d.text((cx-tw/2, cy-330), t, font=f, fill=CARD)
    x0,y0 = cx-330, cy-130; x1,y1 = cx+230, cy+40
    d.line([x0,y0,x1,y1], fill=INK, width=10)
    d.rounded_rectangle([x0-10,y0-30,x0+70,y0+18], radius=12, fill=INK)
    d.rounded_rectangle([x1-40,y1-10,x1+110,y1+70], radius=30, fill=SAGE)
    ay = cy+150
    d.line([cx-380, ay, cx+380, ay], fill=SAGE, width=6)
    d.polygon([(cx-380,ay),(cx-350,ay-16),(cx-350,ay+16)], fill=SAGE)
    d.polygon([(cx+380,ay),(cx+350,ay-16),(cx+350,ay+16)], fill=SAGE)
    ry = cy+180
    d.rounded_rectangle([cx-380, ry, cx+380, ry+54], radius=10, fill=CARD, outline=INK, width=4)
    for i in range(0,761,38):
        hgt = 26 if (i//38)%5==0 else 14
        d.line([cx-380+i, ry+54, cx-380+i, ry+54-hgt], fill=INK, width=3)

def art_golfer(d, cx, cy, lefty=True):
    # アドレスのシルエット（線画・オリジナル、正面やや斜め）。lefty=True で左右反転
    s = -1 if lefty else 1
    k = 0.82
    def P(x,y): return (cx + s*x*k, cy + y*k)
    def L(a,b,w): d.line([P(*a),P(*b)], fill=INK, width=int(w*k))
    # 頭
    hx,hy=P(-40,-320); r=48*k
    d.ellipse([hx-r,hy-r,hx+r,hy+r], fill=INK)
    # 背骨（前傾）→ 腰
    L((-30,-265),(30,-40),44)
    # 腕：肩からハンド（体の前、やや下）
    L((-20,-230),(-110,-30),28)
    # 脚
    L((30,-40),(-30,190),36); L((30,-40),(110,190),36)
    # 足
    L((-60,196),(0,196),22); L((80,196),(150,196),22)
    # クラブ：ハンドからボールへ
    L((-110,-30),(-230,195),9)
    hx2,hy2=P(-230,195)
    d.rounded_rectangle([min(hx2,hx2-s*50),hy2-6,max(hx2,hx2-s*50),hy2+26], radius=12, fill=SAGE)
    bx,by=P(-280,200); rb=14*k
    d.ellipse([bx-rb,by-rb,bx+rb,by+rb], fill=BG, outline=INK, width=3)
    d.line([cx-400, cy+215*k, cx+400, cy+215*k], fill=LINE, width=6)

ART = {"hole18": art_hole18, "ruler46": art_ruler46, "golfer_left": lambda d,cx,cy: art_golfer(d,cx,cy,True)}

def render_hero(spec):
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    d.ellipse([W-420, -260, W+260, 420], fill=CARD)
    m.header(d, spec)
    y = 170
    if spec.get("eyebrow"):
        f = m.sans(40, "Bold"); d.text((64, y), spec["eyebrow"], font=f, fill=SAGE); y += 70
    f = m.serif(spec.get("title_size", 120), "Bold")
    for ln in spec["title"].split("\n"):
        d.text((64, y), ln, font=f, fill=INK); y += spec.get("title_size",120) + 14
    # イラスト領域
    ay = y + 70; ah = H - ay - 330
    ART[spec["art"]](d, W/2, ay + ah/2 + spec.get('art_dy',0))
    # 下：サブ文＋CTA
    sy = H - 300
    if spec.get("sub"):
        f = m.sans(36); sy = m.text_lines(d, m.wrap(spec["sub"], 26), 64, sy, f, SUB, 50)
    if spec.get("cta"):
        f = m.sans(34, "Bold"); m.pill(d, 64, H-190, spec["cta"], SAGE, f, h=66)
    m.footer(d, spec, im)
    return im

def render_newscard(spec):
    """文字だけのニュース表紙：日付・大見出し・出典。イラスト不要。"""
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    d.ellipse([W-420, -260, W+260, 420], fill=CARD)
    m.header(d, spec)
    y = 200
    f = m.sans(40, "Bold"); d.text((64, y), spec.get("eyebrow","GOLF NEWS"), font=f, fill=SAGE); y += 90
    size = spec.get("title_size", 100)
    f = m.serif(size, "Bold")
    for ln in m.wrap(spec["title"], spec.get("title_wrap", 8)):
        d.text((64, y), ln, font=f, fill=INK); y += size + 16
    y += 30; d.line([64, y, 360, y], fill=SAGE, width=6); y += 50
    if spec.get("sub"):
        f = m.sans(40); y = m.text_lines(d, m.wrap(spec["sub"], 22), 64, y, f, INK, 58) + 20
    if spec.get("source"):
        f = m.sans(30); m.text_lines(d, m.wrap("出典：" + spec["source"], 30), 64, H-310, f, SUB, 42)
    if spec.get("cta"):
        f = m.sans(34, "Bold"); m.pill(d, 64, H-190, spec["cta"], SAGE, f, h=66)
    m.footer(d, spec, im)
    return im

RENDER = {"hero": render_hero, "newscard": render_newscard}

if __name__ == "__main__":
    import sys, json as _j, os
    specs = _j.load(open(sys.argv[1], encoding="utf-8"))
    for s in specs:
        im = RENDER[s["type"]](s); im.save("out/" + s["file"], optimize=True)
        im.convert("RGB").save("../docs/posts/" + s["file"].replace(".png", ".jpg"), quality=90); print("wrote", s["file"])
