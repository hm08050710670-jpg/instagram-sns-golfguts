# -*- coding: utf-8 -*-
"""
毎朝のニュース投稿ジョブの補助スクリプト。

  python3 news_job.py draft candidate.json   # 候補（下書き）を登録：画像生成＋ docs/posts へ書き出し＋ news_candidate.json 保存
  python3 news_job.py approve                # 候補を当日の投稿として承認（既存の当日分はストックへ退避）
  python3 news_job.py discard                # 候補を破棄

candidate.json の形式:
{
  "date": "2026-10-23",
  "label": "ニュース｜...",
  "card": {  # 1枚目（newscard）
    "eyebrow": "2026.10.23", "title": "見出し（\\nで改行）", "sub": "1〜2文", "source": "媒体名 日付", "cta": "続きは→"
  },
  "detail": {  # 2枚目（list）
    "head": "見出し", "sub": "説明", "bullets": ["事実1","事実2","事実3"], "cta": "一言"
  },
  "caption": "...（出典URLを含む）", "hashtags": "#..."
}
"""
import json, os, sys, subprocess, datetime as dt
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHED = os.path.join(ROOT, "automation", "schedule.json")
CAND = os.path.join(ROOT, "automation", "news_candidate.json")

def load(): return json.load(open(SCHED, encoding="utf-8"))
def save(S): json.dump(S, open(SCHED, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

def draft(path):
    c = json.load(open(path, encoding="utf-8"))
    d = c["date"]; tag = "news_" + d.replace("-", "")[4:]
    # 画像内の日付は必ず投稿日（c["date"]）から生成する（原稿側の eyebrow は無視）
    card = dict(c["card"], type="newscard", file=f"{tag}_01.png", label="ゴルフニュース", page=1, total=2, eyebrow=d.replace("-", "."))
    detail = dict(c["detail"], type="list", file=f"{tag}.png", label="ゴルフニュース", page=2, total=2)
    os.chdir(os.path.join(ROOT, "images"))
    json.dump([card], open("_cand_hero.json", "w", encoding="utf-8"), ensure_ascii=False)
    subprocess.run([sys.executable, "hero.py", "_cand_hero.json"], check=True)
    import importlib.util
    sm = importlib.util.spec_from_file_location("m", "make_post_images.py"); m = importlib.util.module_from_spec(sm); sm.loader.exec_module(m)
    im = m.RENDER["list"](detail); im.save("out/" + detail["file"], optimize=True)
    im.convert("RGB").save("../docs/posts/" + detail["file"].replace(".png", ".jpg"), quality=90)
    # リール版（BGM付き）も生成
    reel_out = f"out/{tag}_reel.mp4"
    # 左上のピルは短い「ゴルフニュース」固定（長い label だと右上のロゴと重なる。2026-10-22 確認）。schedule 側の label は c["label"] のまま
    json.dump(dict(c, date=d, label=c.get("pill_label", "ゴルフニュース")), open("_cand_reel.json", "w", encoding="utf-8"), ensure_ascii=False)
    subprocess.run([sys.executable, "reel_news.py", "_cand_reel.json", reel_out], check=True)
    os.remove("_cand_reel.json")
    import shutil; shutil.copy(reel_out, "../docs/posts/" + os.path.basename(reel_out))
    P = json.load(open("posts.json", encoding="utf-8"))
    P = [p for p in P if p["file"] not in (card["file"], detail["file"])] + [card, detail]
    json.dump(P, open("posts.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    os.remove("_cand_hero.json")
    rec = {"date": d, "kind": "carousel", "label": c["label"], "images": [f"{tag}_01.jpg", f"{tag}.jpg"],
           "caption": c["caption"], "hashtags": c["hashtags"], "needs_hori": False, "approved": False,
           "approved_by": "", "status": "pending", "ig_media_id": "", "posted_at": "", "sources": c.get("sources", [])}
    # 依頼者決定（2026-10-20 20:57）：ニュースはリールのみ（カルーセルは出さない）。12:00 枠に1本
    reel = dict(rec, kind="reel", label=c["label"] + "（リール）", images=[f"{tag}_reel.mp4", f"{tag}_01.jpg"])
    json.dump(reel, open(CAND, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("候補を保存:", CAND); print("リール:", reel["images"], "（カバー画像 =", reel["images"][1], "）")

def approve():
    c = json.load(open(CAND, encoding="utf-8")); S = load()
    recs = [c["carousel"], c["reel"]] if "carousel" in c else [c]
    d = recs[0]["date"]
    for r in S:
        # 当日の昼枠の既存投稿はすべてストックへ退避（全投稿がリール化された 2026-10-20 以降、kind による除外は行わない。
        # 除外すると下の絞り込みで承認済みの当日分が消えてしまう）
        if r["date"] == d and r["status"] != "posted" and r.get("slot", "noon") == "noon":
            r["date"] = "stock"; r["label"] = "【ストック】" + r["label"].replace("【ストック】", "")
            print("既存の当日分をストックへ退避:", r["label"])
    stamp = f"依頼者（{dt.datetime.now().strftime('%Y-%m-%d %H:%M')} OK）"
    for r in recs: r["approved"] = True; r["approved_by"] = stamp
    # Instagram 2.0 段階1：承認したファイルの指紋を記録（投稿直前に照合される）
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import integrity
    for r in recs: integrity.stamp_approval(r, "依頼者", "Claude定期タスクのチャットで「OK」")
    S = [r for r in S if not (r["date"] == d and r["status"] != "posted")] + recs
    S.sort(key=lambda r: (r["date"] == "stock", r["date"], r.get("slot", "noon")))
    save(S); os.remove(CAND); print("承認:", d, [r["label"] for r in recs])

def discard():
    if os.path.exists(CAND): os.remove(CAND)
    print("候補を破棄")

if __name__ == "__main__":
    {"draft": lambda: draft(sys.argv[2]), "approve": approve, "discard": discard}[sys.argv[1]]()
