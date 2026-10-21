# -*- coding: utf-8 -*-
"""
Instagram 2.0 段階1・2：承認ファイルの指紋（SHA-256）と、投稿前の自動検証。

  python3 automation/integrity.py hash <file> ...           # 指紋を表示
  python3 automation/integrity.py check <date|stock-id>     # 予定レコードを検証して結果を表示（投稿はしない）
  python3 automation/integrity.py backfill                  # 承認済みで指紋のないレコードに、今のファイルの指紋を記録

方針
  - 承認時に、投稿されるファイル（MP4・カバーJPEG）の指紋を schedule.json に記録する（news_job.approve が呼ぶ）
  - 投稿直前に指紋を照合し、違えば「承認後に変更された」として投稿しない
  - 動画は ffprobe／ffmpeg で、長さ・縦横比・音声の有無・真っ黒な時間を確認する
  - ffprobe が無い環境では動画検証を「unavailable」として扱い、合否に使わない（捏造しない）
"""
import hashlib, json, os, shutil, subprocess, sys, datetime as dt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS = os.path.join(ROOT, "docs", "posts")
SCHED = os.path.join(ROOT, "automation", "schedule.json")
FEATURES = os.path.join(ROOT, "automation", "features.json")
JST = dt.timezone(dt.timedelta(hours=9))

# 動画の合格基準（指示書 1-2 / 4-1）。Instagram リールの許容範囲は 3〜90 秒
REEL_MIN_SEC, REEL_MAX_SEC = 3.0, 90.0
REEL_TARGET_SEC, REEL_TOLERANCE = 15.0, 1.0   # 15秒±1秒から外れたら警告（不合格にはしない）
BLACK_MAX_RATIO = 0.5                          # 真っ黒な時間が全体の半分を超えたら不合格


def features():
    try:
        return json.load(open(FEATURES, encoding="utf-8"))
    except Exception:
        return {}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def hashes_for(record):
    """レコードが参照するファイルの指紋 {ファイル名: sha256}。無いファイルは None"""
    out = {}
    for name in record.get("images", []):
        p = os.path.join(POSTS, name)
        out[name] = sha256(p) if os.path.exists(p) else None
    return out


def stamp_approval(record, approver, method):
    """承認情報と指紋をレコードに記録する（承認のたびに版を1つ進める）"""
    record["approved_hashes"] = hashes_for(record)
    hist = record.setdefault("approval_history", [])
    version = len(hist) + 1
    hist.append({
        "version": version,
        "approved_at": dt.datetime.now(JST).isoformat(timespec="seconds"),
        "approver": approver,
        "method": method,
        "hashes": record["approved_hashes"],
    })
    record["approval_version"] = version
    return record


def verify_hashes(record):
    """(ok, messages)。指紋の記録がない旧レコードは ok=True＋警告"""
    want = record.get("approved_hashes")
    if not want:
        return True, ["承認時の指紋の記録なし（旧形式のレコード）。照合をスキップ"]
    now = hashes_for(record)
    bad = [n for n in want if want.get(n) != now.get(n)]
    if bad:
        return False, [f"承認後にファイルが変わっています: {n}" for n in bad]
    return True, [f"指紋一致: {n}" for n in want]


def _ffprobe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                          "stream=codec_type,width,height,duration:format=duration",
                          "-of", "json", path], capture_output=True, text=True, timeout=60)
    return json.loads(out.stdout or "{}")


def _black_seconds(path):
    out = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-vf", "blackdetect=d=0.5:pix_th=0.10",
                          "-an", "-f", "null", "-"], capture_output=True, text=True, timeout=180)
    total = 0.0
    for line in out.stderr.splitlines():
        if "black_duration:" in line:
            try: total += float(line.split("black_duration:")[1].split()[0])
            except Exception: pass
    return total


def check_video(path):
    """(ok, messages)。ffprobe が無ければ ok=True＋unavailable"""
    if not shutil.which("ffprobe") or not shutil.which("ffmpeg"):
        return True, ["動画検証: unavailable（ffprobe／ffmpeg なし）"]
    msgs, ok = [], True
    info = _ffprobe(path)
    streams = info.get("streams", [])
    v = [s for s in streams if s.get("codec_type") == "video"]
    a = [s for s in streams if s.get("codec_type") == "audio"]
    if not v:
        return False, ["映像ストリームがありません"]
    w, h = int(v[0].get("width", 0)), int(v[0].get("height", 0))
    dur = float(info.get("format", {}).get("duration") or v[0].get("duration") or 0)
    if not (w and h and abs(w / h - 9 / 16) < 0.01):
        ok = False; msgs.append(f"縦横比が 9:16 ではありません（{w}x{h}）")
    else:
        msgs.append(f"縦横比 OK（{w}x{h}）")
    if not (REEL_MIN_SEC <= dur <= REEL_MAX_SEC):
        ok = False; msgs.append(f"長さがリールの範囲外です（{dur:.1f}秒）")
    elif abs(dur - REEL_TARGET_SEC) > REEL_TOLERANCE:
        msgs.append(f"警告：長さが原則の15秒から外れています（{dur:.1f}秒）")
    else:
        msgs.append(f"長さ OK（{dur:.1f}秒）")
    msgs.append("音声 OK" if a else "警告：音声なし（BGMが入っていません）")
    black = _black_seconds(path)
    if dur and black / dur > BLACK_MAX_RATIO:
        ok = False; msgs.append(f"真っ黒な時間が長すぎます（{black:.1f}秒／{dur:.1f}秒）")
    else:
        msgs.append(f"黒画面チェック OK（{black:.1f}秒）")
    return ok, msgs


def preflight(record, check_hash=True, check_media=True):
    """投稿前の検証。(ok, messages)"""
    msgs, ok = [], True
    for name in record.get("images", []):
        if not os.path.exists(os.path.join(POSTS, name)):
            ok = False; msgs.append(f"ファイルがありません: docs/posts/{name}")
    if not ok:
        return ok, msgs
    if check_hash:
        h_ok, h_msgs = verify_hashes(record); ok &= h_ok; msgs += h_msgs
    if check_media and record.get("kind") == "reel":
        v_ok, v_msgs = check_video(os.path.join(POSTS, record["images"][0])); ok &= v_ok; msgs += v_msgs
    return ok, msgs


def _load():
    return json.load(open(SCHED, encoding="utf-8"))


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "hash":
        for p in sys.argv[2:]: print(sha256(p), p)
    elif cmd == "check":
        key = sys.argv[2]; S = _load()
        recs = [r for r in S if r["date"] == key or r.get("stock_id") == key or (r["date"] == "stock" and key in r["images"][0])]
        if not recs: sys.exit(f"{key}: 該当なし")
        for r in recs:
            ok, msgs = preflight(r)
            print(("OK " if ok else "NG ") + r["date"], r["label"]); [print("  -", m) for m in msgs]
    elif cmd == "backfill":
        S = _load(); n = 0
        for r in S:
            if r.get("approved") and r.get("status") != "posted" and not r.get("approved_hashes"):
                stamp_approval(r, r.get("approved_by", "") or "不明", "指紋の後付け（2026-10-21 段階1導入時。導入前に承認済みのファイルをそのまま記録）")
                n += 1
        json.dump(S, open(SCHED, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("指紋を後付けしたレコード:", n)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
