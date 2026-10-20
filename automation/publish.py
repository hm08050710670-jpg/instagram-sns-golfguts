# -*- coding: utf-8 -*-
"""
Instagram 自動投稿スクリプト（Facebookページ連携・ページアクセストークン方式）

使い方
  python3 publish.py --date 2026-11-03            # その日の投稿を公開
  python3 publish.py --today                       # 今日（JST）の投稿を公開
  python3 publish.py --today --dry-run             # 公開せず、何をするか表示（API呼び出しなし）
  python3 publish.py --today --check               # 画像URLの到達確認＋トークン確認まで（投稿はしない）

環境変数（GitHub Secrets から渡す）
  IG_USER_ID       Instagram ビジネスアカウントの ID（me/accounts の instagram_business_account.id）
  IG_ACCESS_TOKEN  ページアクセストークン（長期ユーザートークンから取得したもの。期限なし）
  FB_PAGE_ID       （任意）Facebookページ ID。設定すると同じ内容をページにも投稿する
  PAGES_BASE_URL   例 https://hm08050710670-jpg.github.io/instagram-sns-golfguts/posts/

ルール
  - schedule.json の date が一致し、approved == true のものだけ投稿する
  - kind: image（1枚）／carousel（2〜20枚）／reel（images[0]=MP4 の公開URL、images[1]=カバーJPEG 任意。Facebook同時投稿は動画未対応のためスキップ）
  - needs_hori == true で approved == false の場合は投稿せず、理由を出力して終了コード 2（未承認）
  - 画像は公開URL（GitHub Pages）の JPEG を参照
  - Instagram 投稿が成功したら schedule.json の status / ig_media_id / posted_at を更新する（Actions 側で commit）
  - Facebook への同時投稿は補助。失敗しても Instagram の結果は保持し、警告として出力する
  - 同じ日に status == "posted" が既にあれば二重投稿しない
"""
import argparse, datetime as dt, json, os, sys, time, urllib.parse, urllib.request

GRAPH = "https://graph.facebook.com/v21.0"
JST = dt.timezone(dt.timedelta(hours=9))

def http(method, url, data=None):
    body = urllib.parse.urlencode(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code} {url.split('?')[0]}: {e.read().decode(errors='replace')[:600]}")

def head_ok(url):
    try:
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status == 200 and "image/jpeg" in r.headers.get("Content-Type", "")
    except Exception as e:
        print("  URL check failed:", url, e); return False

def head_ok_video(url):
    try:
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status == 200 and "video/mp4" in r.headers.get("Content-Type", "")
    except Exception as e:
        print("  URL check failed:", url, e); return False

def wait_ready(container_id, token, tries=60):
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

def create_reel_container(ig, token, video_url, caption, cover_url=None):
    data = {"media_type": "REELS", "video_url": video_url, "caption": caption, "share_to_feed": "true", "access_token": token}
    if cover_url: data["cover_url"] = cover_url
    return http("POST", f"{GRAPH}/{ig}/media", data)["id"]

def publish(ig, token, container_id):
    return http("POST", f"{GRAPH}/{ig}/media_publish", {"creation_id": container_id, "access_token": token})["id"]

def post_to_facebook(page, token, urls, message):
    """Facebookページへ同じ画像・本文を投稿。1枚なら /photos、複数なら未公開写真→/feed にまとめる。"""
    if len(urls) == 1:
        res = http("POST", f"{GRAPH}/{page}/photos", {"url": urls[0], "message": message, "access_token": token})
        return res.get("post_id") or res.get("id")
    ids = [http("POST", f"{GRAPH}/{page}/photos", {"url": u, "published": "false", "access_token": token})["id"] for u in urls]
    data = {"message": message, "access_token": token}
    for i, pid in enumerate(ids):
        data[f"attached_media[{i}]"] = json.dumps({"media_fbid": pid})
    return http("POST", f"{GRAPH}/{page}/feed", data)["id"]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date"); ap.add_argument("--today", action="store_true")
    ap.add_argument("--dry-run", action="store_true"); ap.add_argument("--check", action="store_true")
    ap.add_argument("--slot", default="noon", choices=["noon", "evening"], help="noon=12:00 の投稿／evening=18:00 のリール")
    ap.add_argument("--schedule", default=os.path.join(os.path.dirname(__file__), "schedule.json"))
    a = ap.parse_args()
    date = a.date or (dt.datetime.now(JST).date().isoformat() if a.today else None)
    if not date: sys.exit("--date か --today を指定してください")

    S = json.load(open(a.schedule, encoding="utf-8"))
    todays = [r for r in S if r["date"] == date and r.get("slot", "noon") == a.slot]
    r = todays[0] if todays else None
    if r: print(f"{date} [{r['kind']}] {r['label']}  images={len(r['images'])}  needs_hori={r['needs_hori']}  approved={r['approved']}  status={r['status']}")
    else: print(f"{date}: 予定なし")

    if r and r["status"] == "posted":
        print("  既に投稿済み（二重投稿を防止）"); return 0
    if not r or not r["approved"]:
        # 当日分が無い／未承認 → ストック（date=="stock"、approved、未投稿）を順番に使う
        stock = [x for x in S if x["date"] == "stock" and x["approved"] and x["status"] != "posted"] if a.slot == "noon" else []
        if a.slot == "evening" and not r:
            print("  夕方枠の予定なし（ニュースのリールが承認されていない日は投稿しない）"); return 0
        if not stock:
            print("  未承認で、ストックもありません。", ("堀コーチ確認が必要です。" if r and r["needs_hori"] else "schedule.json の approved を確認してください。") if r else "")
            return 2
        if r: print("  未承認のため、ストック投稿に差し替えます。")
        r = stock[0]; r["posted_for"] = date
        print(f"  STOCK [{r['kind']}] {r['label']}  images={len(r['images'])}")

    base = os.environ.get("PAGES_BASE_URL", "").rstrip("/") + "/"
    urls = [base + img for img in r["images"]]
    caption = r["caption"] + "\n\n" + r["hashtags"]
    page = os.environ.get("FB_PAGE_ID", "").strip()
    print("  caption chars:", len(caption), " facebook:", "yes" if page else "no (FB_PAGE_ID 未設定)")
    for u in urls: print("  ", u)

    if a.dry_run:
        print("  DRY RUN: API は呼びません"); return 0

    ig, token = os.environ.get("IG_USER_ID"), os.environ.get("IG_ACCESS_TOKEN")
    if not base.startswith("http") or not ig or not token:
        sys.exit("環境変数 PAGES_BASE_URL / IG_USER_ID / IG_ACCESS_TOKEN が未設定です")

    bad = [u for u in urls if not (head_ok_video(u) if r["kind"] == "reel" and u.endswith(".mp4") else head_ok(u))]
    if bad: sys.exit("画像URLに到達できません: " + ", ".join(bad))
    me = http("GET", f"{GRAPH}/{ig}?fields=id,username&access_token={token}")
    print("  instagram:", me.get("username"), me.get("id"))
    page_token = token
    if page:
        # ユーザートークンからページトークンを取り出す（ページ投稿にはページトークンが必要）
        try:
            accts = http("GET", f"{GRAPH}/me/accounts?fields=id,name,access_token&access_token={token}").get("data", [])
            hit = [a for a in accts if a.get("id") == page]
            if hit: page_token = hit[0]["access_token"]
        except Exception as e:
            print("  me/accounts 取得に失敗（渡されたトークンをそのまま使用）:", e)
        pg = http("GET", f"{GRAPH}/{page}?fields=id,name&access_token={page_token}")
        print("  facebook page:", pg.get("name"), pg.get("id"))
    if a.check:
        print("  CHECK OK（投稿はしていません）"); return 0

    if r["kind"] == "reel":
        # images[0] = MP4、images[1]（任意）= カバーJPEG
        cid = create_reel_container(ig, token, urls[0], caption, urls[1] if len(urls) > 1 else None)
        if not wait_ready(cid, token): sys.exit("reel container not ready")
        media_id = publish(ig, token, cid)
    elif r["kind"] == "image":
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
    print("  POSTED instagram media_id =", media_id)

    if page and r["kind"] == "reel":
        print("  Facebook同時投稿はリール未対応のためスキップ")
    elif page:
        try:
            r["fb_post_id"] = post_to_facebook(page, page_token, urls, caption)
            print("  POSTED facebook post_id =", r["fb_post_id"])
        except Exception as e:
            r["fb_post_id"] = ""; print("  WARNING: Facebook 投稿に失敗（Instagram は投稿済み）:", e)

    json.dump(S, open(a.schedule, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return 0

if __name__ == "__main__":
    sys.exit(main())
