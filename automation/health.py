# -*- coding: utf-8 -*-
"""週次ヘルスチェック：トークンの有効性、Facebookページ到達、今後7日の承認状況、画像の存在。問題があれば終了コード1。"""
import datetime as dt, json, os, sys, urllib.request
GRAPH="https://graph.facebook.com/v21.0"; JST=dt.timezone(dt.timedelta(hours=9))
problems=[]
ig, tok, page = os.environ.get("IG_USER_ID"), os.environ.get("IG_ACCESS_TOKEN"), os.environ.get("FB_PAGE_ID","").strip()
def get(url):
    with urllib.request.urlopen(url, timeout=30) as r: return json.loads(r.read())
if not ig or not tok:
    problems.append("Secrets IG_USER_ID / IG_ACCESS_TOKEN が未設定（SETUP.md STEP 5）")
else:
    try:
        me=get(f"{GRAPH}/{ig}?fields=id,username&access_token={tok}"); print("token OK: instagram", me.get("username"), me.get("id"))
        print("publish quota:", get(f"{GRAPH}/{ig}/content_publishing_limit?access_token={tok}"))
        if page:
            pg=get(f"{GRAPH}/{page}?fields=id,name&access_token={tok}"); print("facebook page OK:", pg.get("name"), pg.get("id"))
        else:
            print("FB_PAGE_ID 未設定（Facebook同時投稿なし）")
    except Exception as e:
        problems.append(f"トークン確認でエラー（ページトークンを再発行して IG_ACCESS_TOKEN を更新）: {e}")
S=json.load(open(os.path.join(os.path.dirname(__file__),"schedule.json"),encoding="utf-8"))
today=dt.datetime.now(JST).date()
for r in S:
    if r["date"]=="stock": continue
    d=dt.date.fromisoformat(r["date"])
    if today<=d<=today+dt.timedelta(days=7):
        flag="" if r["approved"] or r["status"]=="posted" else "  <-- 未承認" + ("（堀コーチ確認要）" if r["needs_hori"] else "")
        print(f"{r['date']} {r['kind']:8} approved={r['approved']} {r['label']}{flag}")
        if flag: problems.append(f"{r['date']} が未承認")
        for img in r["images"]:
            if not os.path.exists(os.path.join(os.path.dirname(__file__),"..","docs","posts",img)): problems.append(f"{r['date']} 画像なし: {img}")
stock=[x for x in S if x["date"]=="stock" and x["approved"] and x["status"]!="posted"]
print("stock remaining:",len(stock))
if len(stock)<2: problems.append("ストック投稿が2本未満")
if problems:
    print("\nPROBLEMS:"); [print(" -",p) for p in problems]; sys.exit(1)
print("\nALL OK")
