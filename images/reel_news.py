# -*- coding: utf-8 -*-
"""
ニュース投稿のリール版（1080x1920・9:16・約15秒・無音）を文字アニメーションで生成する。
使い方: cd images && python3 reel_news.py candidate.json out/news_MMDD_reel.mp4
candidate.json は news_job.py と同じ形式（card / detail / date）。
構成: 0-2s 日付＋ラベル → 2-6s 見出しが1行ずつスライドイン → 6-7s 要約 → 7-12s 事実3点が順に出る → 12-15s 締め（橋渡し＋ロゴ）
"""
import json, os, sys, subprocess, importlib.util
from PIL import Image, ImageDraw
sm = importlib.util.spec_from_file_location("m", os.path.join(os.path.dirname(os.path.abspath(__file__)), "make_post_images.py"))
m = importlib.util.module_from_spec(sm); sm.loader.exec_module(m)
W, H, FPS = 1080, 1920, 30
BG, CARD, INK, SUB, SAGE, LINE, ON_DARK = m.BG, m.CARD, m.INK, m.SUB, m.SAGE, m.LINE, m.ON_DARK

def ease(t):  # ease-out cubic, t in [0,1]
    t = max(0.0, min(1.0, t)); return 1 - (1 - t) ** 3

def blend(a, b, t):
    a = Image.new("RGB", (1, 1), a).getpixel((0, 0)); b = Image.new("RGB", (1, 1), b).getpixel((0, 0))
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

LOGO_FULL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "photos", "logo", "golfguts_logo_brown.png")
LOGO_H = 72
BANNER_BOTTOM = H - 318   # 下に案内1行＋出典（H-230）。2026-10-21 案内行を追加
GAP_BAR_MIN = 60          # バーは原則いつも入れる（2026-10-21 依頼者決定）。空きが極端に狭いときだけ省く
BAR_W = 160
BANNER_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "photos", "banners", "prepped")
# banner_01「最初の60分で、変わる。」は brand_guide の禁止表現（60分で変わる＝効果の保証）に当たるため使わない（2026-10-21）
BANNER_EXCLUDE = {"banner_01_60min.png"}
_banner_cache = {}

def banner_style(spec):
    """endcard＝記事のあとに締めの画面へ切り替える／panel＝記事の下にカード面で区切って置く／inline＝従来"""
    if spec.get("banner_style"): return spec["banner_style"]
    try:
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "automation", "features.json")
        return json.load(open(p, encoding="utf-8")).get("reel_banner_style", "inline")
    except Exception:
        return "inline"

def banner_enabled():
    try:
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "automation", "features.json")
        return bool(json.load(open(p, encoding="utf-8")).get("reel_banner"))
    except Exception:
        return False

def pick_banner(seed):
    """photos/banners/prepped/*.png から日付で1枚選ぶ（BGMとは別の順番）。無ければ None"""
    import glob
    files = [f for f in sorted(glob.glob(os.path.join(BANNER_DIR, "*.png"))) if os.path.basename(f) not in BANNER_EXCLUDE]
    if not files: return None
    return files[(sum(map(ord, str(seed))) * 7 + 3) % len(files)]

def load_banner(spec):
    """spec["banner"] があればそれ（"none" で無し）、無ければ日付で選ぶ。features.json の reel_banner が false なら None"""
    if not banner_enabled() or spec.get("banner") == "none": return None
    path = os.path.join(BANNER_DIR, spec["banner"]) if spec.get("banner") else pick_banner(spec.get("date", ""))
    if path and banner_style(spec) == "panel":
        path = os.path.join(os.path.dirname(BANNER_DIR), "prepped_card", os.path.basename(path))
    if not path or not os.path.exists(path): return None
    if path not in _banner_cache: _banner_cache[path] = Image.open(path).convert("RGB")
    return _banner_cache[path]

def spread(spec, size):
    """バナーの上に余る空きを、見出し・要約・箇条書きの間にも配分して、1か所に大きな空白が出ないようにする（2026-10-21 依頼者指示「全体のバランス」）。
    戻り値：(見出し下の追加, 要約下の追加, 箇条書き同士の追加)。バナーなしの日は 0"""
    bn = load_banner(spec)
    if bn is None: return 0, 0, 0
    card = spec["card"]; nb = len(spec["detail"].get("bullets", [])[:3])
    y_end = 320 + len(card["title"].split("\n")) * (size + 16) + 80 + len(m.wrap(card.get("sub", ""), 24)) * 58 + 40 + nb * 118
    slack = min((BANNER_BOTTOM - bn.height) - (y_end + 110), 360)   # 110＝箇条書き〜バナーの最低限の間（バー込み）
    if slack <= 0: return 0, 0, 0
    return int(slack * 0.25), int(slack * 0.2), int(slack * 0.1)   # 残り約35％は箇条書き〜バナーの間に残る

def frame_article(spec, s):
    """s = 秒"""
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    # 右上の円（ゆっくり拡大）
    r = 420 + 40 * ease(s / 15)
    d.ellipse([W - r, -r * 0.6, W + r * 0.6, r], fill=CARD)
    card = spec["card"]; det = spec["detail"]
    # ラベルと日付（0〜0.6s フェード）
    t0 = ease(s / 0.6)
    m.pill(d, 64, 120, spec.get("label", "ゴルフニュース"), blend(BG, SAGE, t0), m.sans(30, "Bold"), h=66)
    d.text((64, 230), card.get("eyebrow", ""), font=m.sans(44, "Bold"), fill=blend(BG, SAGE, t0))
    # 見出し：1行ずつ 0.35s 間隔でスライドイン（1.0s から）
    lines = card["title"].split("\n")
    # 見出しが4行以上でバナーを出す日は、バナーの場所を空けるため見出しを少し小さく（2026-10-21）
    size = 88 if (len(lines) >= 4 and banner_enabled() and spec.get("banner") != "none") else 100; y = 320
    e_title, e_sub, e_bul = spread(spec, size)
    for i, ln in enumerate(lines):
        t = ease((s - 1.0 - i * 0.35) / 0.5)
        if t > 0:
            d.text((64 + (1 - t) * 160, y), ln, font=m.serif(size, "Bold"), fill=blend(BG, INK, t))
        y += size + 16
    # 下線
    tl = ease((s - 1.0 - len(lines) * 0.35) / 0.4)
    if tl > 0: d.line([64, y + 20, 64 + 300 * tl, y + 20], fill=SAGE, width=6)
    y += 80 + e_title
    # 要約（3.2s〜）
    t = ease((s - 3.2) / 0.5)
    if t > 0:
        y = m.text_lines(d, m.wrap(card.get("sub", ""), 24), 64, y, m.sans(40), blend(BG, INK, t), 58)
    y += 40 + e_sub
    # 事実3点（6.0s から 0.9s 間隔でスライドイン）
    for i, b in enumerate(det.get("bullets", [])[:3]):
        t = ease((s - 6.0 - i * 0.9) / 0.5)
        if t > 0:
            rh = 100; x = 64 + (1 - t) * 120
            d.rounded_rectangle([x, y, W - 64, y + rh], radius=24, fill=blend(BG, CARD, t), outline=blend(BG, LINE, t), width=2)
            d.ellipse([x + 34, y + rh / 2 - 9, x + 52, y + rh / 2 + 9], fill=blend(BG, SAGE, t))
            d.text((x + 80, y + 26), b, font=m.sans(38, "Bold"), fill=blend(BG, INK, t))
        y += 100 + 18 + (e_bul if i < len(det.get("bullets", [])[:3]) - 1 else 0)
    # 締め（10.5s〜）：橋渡しの一言＋CTA
    t = ease((s - 10.5) / 0.6)
    if t > 0 and not spec.get("_no_closing"):
        bn = load_banner(spec)
        cy = y + 70   # 箇条書きの3点目との間（2026-10-21 依頼者指示で 30→70）
        if bn is not None and BANNER_BOTTOM - cy < bn.height:
            cy = y + 36   # 場所が足りない日だけ間を詰める（バーは省かれる）
        # 橋渡しの一言（detail.cta）は、バナーがある場合は出さない（2026-10-21 依頼者決定「キャッチフレーズはなしで」。橋渡しはバナーとキャプションが担う）
        if bn is None:
            d.text((64, cy), det.get("cta", ""), font=m.sans(44, "Bold"), fill=blend(BG, INK, t)); cy += 74
        room = BANNER_BOTTOM - cy   # 案内行・出典の上までに収める
        if bn is not None and room >= 200:
            if bn.height > room:
                bn = bn.resize((int(bn.width * room / bn.height), room), Image.LANCZOS)
            # バナーは下寄せ（出典の少し上に下端をそろえる。2026-10-21 依頼者指示「もうちょっと下に」）
            top = max(cy, BANNER_BOTTOM - bn.height)
            gap = top - y   # 箇条書きの下端からバナー上端までの空き
            if gap >= GAP_BAR_MIN:
                # 空きが目立つときは区切りのバーを入れる（2026-10-21 依頼者指示）
                # バーはバナー寄りに置く（2026-10-21 依頼者指示「下に下げて全体のバランスを」）。空きが大きいほど少し離す
                gy = y + int(gap * 0.6); bw = int(BAR_W * t)
                d.rounded_rectangle([(W - bw) // 2, gy - 2, (W + bw) // 2, gy + 2], radius=2, fill=blend(BG, LINE, t))
            bx = (W - bn.width) // 2; by = top + int((1 - t) * 40)
            if banner_style(spec) == "panel":
                pad = 20
                d.rounded_rectangle([bx - pad, by - pad, bx + bn.width + pad, by + bn.height + pad], radius=28, fill=blend(BG, CARD, t))
                im.paste(Image.blend(Image.new("RGB", bn.size, blend(BG, CARD, t)), bn, t), (bx, by))
            else:
                im.paste(Image.blend(Image.new("RGB", bn.size, BG), bn, t), (bx, by))
            # リール内はタップできないため、予約の入口を明記（2026-10-21 依頼者決定）
            msg = "ご予約はプロフィールのリンクから"; f = m.sans(32)
            tw = d.textlength(msg, font=f); d.text(((W - tw) / 2, by + bn.height + (36 if banner_style(spec) == "panel" else 16)), msg, font=f, fill=blend(BG, SUB, t))
        else:
            m.pill(d, 64, cy, spec.get("cta_pill", "初回スイングdock｜目安60分"), blend(BG, SAGE, t), m.sans(34, "Bold"), h=72); cy += 90
            d.text((64, cy), "詳細・ご予約はプロフィールのリンクから", font=m.sans(32), fill=blend(BG, SUB, t))
    # 出典（常時・小さく）
    if card.get("source"):
        m.text_lines(d, m.wrap("出典：" + card["source"], 34), 64, H - 230, m.sans(26), SUB, 36)
    # フッター（ロゴ）
    if os.path.exists(LOGO_FULL):
        # 公式ロゴ（GOLF GUTS＋DESIGN YOUR GOLF LIFE）。2026-10-21 依頼者指示で文字だけの版から変更
        lg = Image.open(LOGO_FULL).convert("RGBA"); k = LOGO_H / lg.height
        lg = lg.resize((int(lg.width * k), LOGO_H), Image.LANCZOS); im.paste(lg, (64, H - LOGO_H - 80), lg)
    elif os.path.exists(m.LOGO_PATH):
        lg = Image.open(m.LOGO_PATH).convert("RGBA"); k = 28 / lg.height
        lg = lg.resize((int(lg.width * k), 28), Image.LANCZOS); im.paste(lg, (64, H - 120), lg)
    else:
        d.text((64, H - 120), "golfguts", font=m.sans(28), fill=SUB)
    return im

END_START = 10.0   # 締めの画面に切り替える時刻（endcard）

def endcard(spec, s):
    """締めの画面：記事とは別の画面にバナーを大きく置く（2026-10-21 依頼者指示「記事とバナーがつながって見える」への対策）"""
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    r = 420 + 40 * ease(s / 15)
    d.ellipse([W - r, -r * 0.6, W + r * 0.6, r], fill=CARD)
    bn = load_banner(spec); t = ease((s - END_START - 0.3) / 0.6)
    if bn is not None:
        k = 1000 / bn.width; b2 = bn.resize((1000, int(bn.height * k)), Image.LANCZOS)
        by = int(H * 0.40 - b2.height / 2 + (1 - t) * 40)
        im.paste(Image.blend(Image.new("RGB", b2.size, BG), b2, t), ((W - b2.width) // 2, by))
        msg = "ご予約はプロフィールのリンクから"; f = m.sans(38)
        tw = d.textlength(msg, font=f); d.text(((W - tw) / 2, by + b2.height + 60), msg, font=f, fill=blend(BG, SUB, t))
    if os.path.exists(LOGO_FULL):
        lg = Image.open(LOGO_FULL).convert("RGBA"); kk = LOGO_H / lg.height
        lg = lg.resize((int(lg.width * kk), LOGO_H), Image.LANCZOS); im.paste(lg, (64, H - LOGO_H - 80), lg)
    return im

def frame(spec, s):
    if banner_style(spec) == "endcard" and load_banner(spec) is not None:
        art = dict(spec, _no_closing=True, banner="none")   # 記事は従来のレイアウト（見出しの縮小・余白の配分なし）
        if s < END_START: return frame_article(art, s)
        k = ease((s - END_START) / 0.5)
        if k >= 1: return endcard(spec, s)
        return Image.blend(frame_article(art, s), endcard(spec, s), k)
    return frame_article(spec, s)

BGM_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "photos", "audio")
BGM_GAIN_DB = -14   # 「うっすら」。0 が原音量

def pick_bgm(seed):
    """photos/audio/*.mp3 からローテーションで1曲選ぶ（seed=日付など）。無ければ None"""
    import glob
    files = sorted(glob.glob(os.path.join(BGM_DIR, "*.mp3")))
    if not files: return None
    return files[sum(map(ord, str(seed))) % len(files)]

def render(spec, out, seconds=15, bgm=None):
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
    if bgm:
        cmd += ["-stream_loop", "-1", "-i", bgm,
                "-filter_complex", f"[1:a]volume={BGM_GAIN_DB}dB,afade=t=in:st=0:d=1.0,afade=t=out:st={seconds-1.5}:d=1.5[a]",
                "-map", "0:v", "-map", "[a]", "-c:a", "aac", "-b:a", "128k", "-shortest"]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.1", "-movflags", "+faststart", "-r", str(FPS), "-t", str(seconds), out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    n = seconds * FPS
    for i in range(n):
        s = i / FPS
        # 最後 0.6 秒はフェードアウト
        im = frame(spec, s)
        if s > seconds - 0.6:
            k = (seconds - s) / 0.6; im = Image.blend(Image.new("RGB", (W, H), BG), im, k)
        p.stdin.write(im.tobytes())
    p.stdin.close(); p.wait()
    return out

if __name__ == "__main__":
    spec = json.load(open(sys.argv[1], encoding="utf-8")); out = sys.argv[2]
    bgm = pick_bgm(spec.get("date", out))
    bn = (os.path.join(BANNER_DIR, spec["banner"]) if spec.get("banner") else pick_banner(spec.get("date", ""))) if banner_enabled() else None
    render(spec, out, bgm=bgm); print("wrote", out, "bgm:", os.path.basename(bgm) if bgm else "none", "banner:", os.path.basename(bn) if bn else "none")
