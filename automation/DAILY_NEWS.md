# 毎朝のニュース投稿ジョブ（手順書）

目的：毎日 09:00 JST に、その日の「ゴルフニュース」投稿の候補（**リール1本・BGM付き・昼（11:41 起動）**。カルーセルは出さない＝2026-10-20 依頼者決定）を作り、**作業者（AI）が自分で1本を選んで自動承認する（2026-11-26 依頼者決定「これからは君の選んだニュースのナンバーワンでいこう。OK を言わなくても投稿できるように」。それまでは依頼者の OK を待っていた）**。依頼者は通知を見て 11:45 までに「今日はなし」「差し替え」と返せば止められる。`draft` で画像2枚（1枚目はリールのカバーに使う）とリール（MP4）が生成される。投稿されるのはリールのみ。OK がなければ昼の自動投稿はストック（確認不要の投稿）に自動で差し替わる（`publish.py` の仕様）。

依頼者決定（2026-10-20）：「ニュースは毎日」「画像はイラスト不要、文字カードで」。

## 0. 準備
```
cd ~/instagram-sns-golfguts 2>/dev/null || gh repo clone hm08050710670-jpg/instagram-sns-golfguts ~/instagram-sns-golfguts
cd ~/instagram-sns-golfguts && git pull -q
# ロゴ（フッター用）。無ければ文字ロゴにフォールバックするので必須ではない
[ -f photos/logo/golfguts_wordmark_brown.png ] && ls photos/banners/prepped/*.png >/dev/null 2>&1 || (rm -rf /tmp/gg_photos; gh repo clone hm08050710670-jpg/photos-photos-photos-photos-photos- /tmp/gg_photos -q && mkdir -p photos/logo photos/audio photos/banners/prepped && cp /tmp/gg_photos/logo/*.png photos/logo/ && cp /tmp/gg_photos/audio/*.mp3 photos/audio/ && cp /tmp/gg_photos/banners/prepped/*.png photos/banners/prepped/)
# リール締めのCTAバナー（features.json の reel_banner が true のとき、日付で1枚を自動選択。banner_01 は禁止表現のため使わない）
```
`CLAUDE.md` を読む（ルールの正）。

## 1. ネタ探し（検索は必ず行う）
- 検索：「ゴルフ ニュース 昨日/今日」「JGTO」「JLPGA」「PGAツアー 結果」「ゴルフ 新製品 発表」「ゴルフ ルール 改正」など。日本語メディア優先（ALBA、ゴルフダイジェスト、JGA、JGTO、JLPGA 公式）
- 選ぶ基準：①事実が2つ以上の情報源で一致 ②日付が直近7日以内 ③アマチュアゴルファーにも関係づけられる ④選手の発言引用に頼らない
- 一致しない・古い・薄い場合は **ニュースを作らず**、「本日はニュース候補なし（理由）」と報告して終了（昼はストックが出る）

## 2. 原稿（禁止事項は CLAUDE.md §5 サブ枠・§6）
- 要約は自分の言葉。記事本文の転載・長文引用はしない。出典（媒体名・日付・URL）を明記
- 選手の写真・大会映像・メーカーロゴは使わない（画像は文字カードのみ）
- 「〇〇選手も実践」「真似すれば直る」「これを買えば直る」「必ず」「No.1」は不可
- 末尾は必ず初回スイングdock か「自分のスイングで確認」への橋渡し＋定型CTA：
  `初回スイングdockの詳細・ご予約はプロフィールのリンクから。予約画面で「会員登録せずに予約」をお選びください。`
- 文字量の上限（画像が崩れるため厳守）：card.title は1行8字以内×最大4行（`\n`で改行を指定）／card.sub 60字以内／detail.head 2行以内（各11字以内）／detail.sub 40字以内／detail.bullets は **3本まで・各17字以内**／cta 16字以内
- ハッシュタグ：`#ゴルフ #ゴルフレッスン #恵比寿 #インドアゴルフ #ゴルフスクール #GOLFGUTS #ゴルフニュース` ＋話題に合うもの1〜3個

## 3. 候補を登録（画像を自動生成）
candidate.json（形式は `news_job.py` の docstring）を書いて：
```
python3 automation/news_job.py draft /path/to/candidate.json
python3 automation/publish.py --date $(date +%F) --dry-run   # 当日の予定を確認（候補は未承認なのでまだ出ない）
git add -A && git commit -m "news candidate $(date +%F)" && git push
```
生成した `images/out/news_MMDD_01.png` と `news_MMDD.png` を **必ず開いて目視**（はみ出し・重なりがあれば文字を削って作り直す）。
**画像内の日付が今日の日付と一致しているか必ず確認する**（candidate.json の `date` は今日の日付にする。日付は `news_job.py` が投稿日から自動で入れる。2026-10-20 のテストで、別日の原稿をそのまま使い日付がずれた事故あり）。

## 4. 自動承認（2026-11-26〜）と依頼者への通知
承認の前に `schedule.json` を確認する。
- **今日の日付で approved=true・status≠posted の予定（依頼者が日付を指定して入れた承認済みリール）が既にある日は自動承認しない**。従来どおり候補を draft のまま提示し、「OK と返信いただければ今日 12:00 にこのニュースを投稿します（既存の予定リールは保留に入ります）。11:45 までに返信がなければ既存の予定リールが出ます」と添えて待つ（依頼者の日付指定を上書きしないため）
- それ以外の日は：
```
python3 automation/news_job.py approve auto      # approved_by に「自動承認」と記録
python3 automation/publish.py --date $(TZ=Asia/Tokyo date +%F) --dry-run   # 今日の予定がこのリールになり、検証 OK を確認
git add -A && git commit -m "news candidate $(date +%F): <見出し> reel draft + approve" && git push   # 11:30 JST より前に
```
- 通知（PushNotification）：先頭に「12:00 に投稿予定：<見出し>」、出典（媒体名・日付）、「差し替え・取りやめは 11:45 までに返信してください（『今日はなし』で豆知識のストックに切り替えます）」。チャットには見出し／キャプション全文／出典URL／リールMP4／カバー画像を出す
- 投稿の起動は別の定期タスク（11:45 JST、workflow_dispatch）が行う。このジョブは起動しない。**予定時刻に投稿が出ていなくても、勝手に手動起動せず依頼者に報告して指示を待つ**（2026-10-22）

## 5. 依頼者から返信があったら
- 「今日はなし」：`python3 automation/news_job.py cancel` → commit → push（当日のニュースレコードを削除し、保留に入れた当日分があれば当日に戻す。残りはストック＝豆知識が出る）
- 修正指示：candidate.json を直して `draft` → `approve auto` からやり直す（指紋が更新される）
- §4 で自動承認しなかった日に「OK」：
```
python3 automation/news_job.py approve     # 既存の当日分（承認済みの予定リール）があれば保留（date:"hold"）へ
git add -A && git commit -m "approve news $(date +%F)" && git push
```
**押し出された予定リールは保留（`date: "hold"`）に入り、自動では出ない。次の空き日へ移さない（2026-11-09 依頼者決定：OK がない日は必ず豆知識＝ストックを出すため）。保留のリールを出すのは、依頼者が日付を指定したときだけ（そのレコードの `date` を指定日に書き換える。承認済みの指紋はそのまま有効）。**
未承認の候補を捨てるだけなら `discard`。

## 6. 報告
最後に1行：日付／見出し／承認の有無／出典。
