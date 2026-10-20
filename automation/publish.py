# -*- coding: utf-8 -*-
"""
Instagram 自動投稿スクリプト（Instagram Graph API / Content Publishing）

使い方
  python3 publish.py --date 2026-11-03            # その日の投稿を公開
  python3 publish.py --today                       # 今日（JST）の投稿を公開
  python3 publish.py --today --dry-run             # 公開せず、何をするか表示（API呼び出しなし）
  python3 publish.py --today --check               # 画像URLの到達確認＋トークン確認まで（投稿はしない）

環境変数（GitHub Secrets から渡す）
  IG_USER_ID       Instagram プロアカウントの ID（数字）
  IG_ACCESS_TOKEN  長期アクセストークン
  PAGES_BASE_URL   例 https://hm08050710670-jpg.github.io/instagram-sns-golfguts/posts/

ルール
  - schedule.json の date が一致し、approved == true のものだけ投稿する
  - needs_hori == true で approved == false の場合は投稿せず、理由を出力して終了コード 2（未承認）
  - 画像は公開URL（GitHub Pages）の JPEG を参照
  - 成功したら schedule.json の status / ig_media_id / posted_at を更新する（Actions 側で commit）
  - 同じ日に status == "posted" が既にあれば二重投稿しない
"""
import argparse, datetime as dt, json, os, sys, time, urllib.parse, urllib.request

GRAPH = "https://graph.facebook.com/v21.0"
JST = dt.timezone(dt.timedelta(hours=9))

def http(method, url, data=None):
    body = urllib.parse.urlencode(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())

def head_ok(url):
    try:
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status == 200 and "image/jpeg" in r.headers.get("Content-Type", "")
    except Exception as e:
        print("  URL check failed:", url, e); return False

def wait_ready(container_id, token, tries=20):
    for _ in range(tries):
        s = http("GET", f"{GRAPH}/{container_id}?fields=status_code,status&access_token={token}")
        if s.get("status_code") == "FINISHED": return True
        if s.get("status_code") == "ERROR": print("  container error:", s); return False
        time.sleep(3)
    return False

def create_image_container(ig, token, url, caption=None, is_item=False):
    data = {"image_url": url, "access_token": token}
    if is_item: data["is_carousel_item"] = "true"
    elif caption is not None: data["caption"] = caption
    return http("POST", f"{GRAPH}/{ig}/media", data)["id"]

def create_carousel_container(ig, token, children, caption):
    data = {"media_type": "CAROUSEL", "children": ",".join(children), "caption": caption, "access_token": token}
    return http("POST", f"{GRAPH}/{ig}/media", data)["id"]

def publish(ig, token, container_id):
    return http("POST", f"{GRAPH}/{ig}/media_publish", {"creation_id": container_id, "access_token": token})["id"]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date"); ap.add_argument("--today", action="store_true")
    ap.add_argument("--dry-run", action="store_true"); ap.add_argument("--check", action="store_true")
    ap.add_argument("--schedule", default=os.path.join(os.path.dirname(__file__), "schedule.json"))
    a = ap.parse_args()
    date = a.date or (dt.datetime.now(JST).date().isoformat() if a.today else None)
    if not date: sys.exit("--date か --today を指定してください")

    S = json.load(open(a.schedule, encoding="utf-8"))
    todays = [r for r in S if r["date"] == date]
    if not todays: print(f"{date}: 予定なし"); return 0
    r = todays[0]
    print(f"{date} [{r['kind']}] {r['label']}  images={len(r['images'])}  needs_hori={r['needs_hori']}  approved={r['approved']}  status={r['status']}")

    if r["status"] == "posted":
        print("  既に投稿済み（二重投稿を防止）"); return 0
    if not r["approved"]:
        print("  未承認のため投稿しません。", "堀コーチ確認が必要です。" if r["needs_hori"] else "schedule.json の approved を true にしてください。")
        return 2

    base = os.environ.get("PAGES_BASE_URL", "").rstrip("/") + "/"
    urls = [base + img for img in r["images"]]
    caption = r["caption"] + "\n\n" + r["hashtags"]
    print("  caption chars:", len(caption))
    for u in urls: print("  ", u)

    if a.dry_run:
        print("  DRY RUN: API は呼びません"); return 0

    ig, token = os.environ.get("IG_USER_ID"), os.environ.get("IG_ACCESS_TOKEN")
    if not base.startswith("http") or not ig or not token:
        sys.exit("環境変数 PAGES_BASE_URL / IG_USER_ID / IG_ACCESS_TOKEN が未設定です")

    bad = [u for u in urls if not head_ok(u)]
    if bad: sys.exit("画像URLに到達できません: " + ", ".join(bad))
    me = http("GET", f"{GRAPH}/{ig}?fields=id,username&access_token={token}")
    print("  account:", me.get("username"), me.get("id"))
    if a.check:
        print("  CHECK OK（投稿はしていません）"); return 0

    if r["kind"] == "image":
        cid = create_image_container(ig, token, urls[0], caption)
        if not wait_ready(cid, token): sys.exit("container not ready")
        media_id = publish(ig, token, cid)
    else:
        children = []
        for u in urls:
            cid = create_image_container(ig, token, u, is_item=True)
            if not wait_ready(cid, token): sys.exit("carousel item not ready: " + u)
            children.append(cid)
        car = create_carousel_container(ig, token, children, caption)
        if not wait_ready(car, token): sys.exit("carousel container not ready")
        media_id = publish(ig, token, car)

    r["status"] = "posted"; r["ig_media_id"] = media_id; r["posted_at"] = dt.datetime.now(JST).isoformat(timespec="seconds")
    json.dump(S, open(a.schedule, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  POSTED media_id =", media_id)
    return 0

if __name__ == "__main__":
    sys.exit(main())
