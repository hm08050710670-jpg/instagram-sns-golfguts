# -*- coding: utf-8 -*-
"""週次ヘルスチェック：トークンの有効性・期限、今後7日の承認状況、画像の存在。問題があれば終了コード1。"""
import datetime as dt, json, os, sys, urllib.request
GRAPH="https://graph.instagram.com/v21.0"; JST=dt.timezone(dt.timedelta(hours=9))
problems=[]
ig, tok = os.environ.get("IG_USER_ID"), os.environ.get("IG_ACCESS_TOKEN")
if not ig or not tok:
    problems.append("Secrets IG_USER_ID / IG_ACCESS_TOKEN が未設定（SETUP.md STEP 5）")
else:
    try:
        with urllib.request.urlopen(f"{GRAPH}/me?fields=user_id,username&access_token={tok}", timeout=30) as r:
            me=json.loads(r.read()); print("token OK:", me.get("username"), me.get("user_id"))
        # 期限は refresh_token.py が毎週延長する。ここでは有効性のみ確認
        with urllib.request.urlopen(f"{GRAPH}/{ig}/content_publishing_limit?access_token={tok}", timeout=30) as r:
            print("publish quota:", json.loads(r.read()))
    except Exception as e:
        problems.append(f"トークン確認でエラー: {e}")
S=json.load(open(os.path.join(os.path.dirname(__file__),"schedule.json"),encoding="utf-8"))
today=dt.datetime.now(JST).date()
for r in S:
    d=dt.date.fromisoformat(r["date"])
    if today<=d<=today+dt.timedelta(days=7):
        flag="" if r["approved"] or r["status"]=="posted" else "  <-- 未承認" + ("（堀コーチ確認要）" if r["needs_hori"] else "")
        print(f"{r['date']} {r['kind']:8} approved={r['approved']} {r['label']}{flag}")
        if flag: problems.append(f"{r['date']} が未承認")
        for img in r["images"]:
            if not os.path.exists(os.path.join(os.path.dirname(__file__),"..","docs","posts",img)): problems.append(f"{r['date']} 画像なし: {img}")
if problems:
    print("\nPROBLEMS:"); [print(" -",p) for p in problems]; sys.exit(1)
print("\nALL OK")
