# -*- coding: utf-8 -*-
"""
ストック投稿（いつでも使えるリール）を仕様から生成し、schedule.json の date:"stock" に登録する。

  python3 automation/build_stock.py automation/stock_specs.json [id ...]

- 各 spec（形式は stock_specs.json を参照）から、カバー（newscard、hero.py）とリール（reel_news.py、BGM付き）を生成
- docs/posts/<id>.mp4 と <id>_cover.jpg に書き出し、schedule.json の同 id の記録を置き換える（無ければ追加）
- approved は True（依頼者決定 2026-10-21「当たり障りのないいつでも使えるサブ投稿を作っておく」。未承認日の自動差し替え用）
"""
import json, os, sys, subprocess, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHED = os.path.join(ROOT, "automation", "schedule.json")
IMG = os.path.join(ROOT, "images")

def build(spec):
    sid = spec["id"]
    os.chdir(IMG)
    cover = dict(spec["card"], type="newscard", file=f"{sid}_cover.png", label=spec["label"])
    json.dump([cover], open("_stock_cover.json", "w", encoding="utf-8"), ensure_ascii=False)
    subprocess.run([sys.executable, "hero.py", "_stock_cover.json"], check=True); os.remove("_stock_cover.json")
    from PIL import Image
    Image.open(f"out/{sid}_cover.png").convert("RGB").save(f"../docs/posts/{sid}_cover.jpg", quality=90)
    reel_spec = {"date": sid, "label": spec["label"], "card": spec["card"], "detail": spec["detail"], "cta_pill": spec.get("cta_pill", "初回スイングdock｜目安60分")}
    json.dump(reel_spec, open("_stock_reel.json", "w", encoding="utf-8"), ensure_ascii=False)
    subprocess.run([sys.executable, "reel_news.py", "_stock_reel.json", f"out/{sid}.mp4"], check=True); os.remove("_stock_reel.json")
    shutil.copy(f"out/{sid}.mp4", f"../docs/posts/{sid}.mp4")
    return {"date": "stock", "kind": "reel", "label": spec["title_label"], "images": [f"{sid}.mp4", f"{sid}_cover.jpg"],
            "caption": spec["caption"], "hashtags": spec["hashtags"], "needs_hori": False, "approved": True,
            "approved_by": "依頼者決定（2026-10-21：いつでも使えるストック投稿）", "status": "pending", "ig_media_id": "", "posted_at": ""}

if __name__ == "__main__":
    specs = json.load(open(sys.argv[1], encoding="utf-8"))
    only = set(sys.argv[2:])
    S = json.load(open(SCHED, encoding="utf-8"))
    for sp in specs:
        if only and sp["id"] not in only: continue
        rec = build(sp)
        S = [r for r in S if not (r["date"] == "stock" and r["images"][0] == rec["images"][0] and r["status"] != "posted")] + [rec]
        print("registered:", rec["label"])
    S.sort(key=lambda r: (r["date"] == "stock", r["date"], r.get("slot", "noon")))
    json.dump(S, open(SCHED, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
