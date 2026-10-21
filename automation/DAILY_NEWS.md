# 毎朝のニュース投稿ジョブ（手順書）

目的：毎日 09:00 JST に、その日の「ゴルフニュース」投稿の候補（**リール1本・BGM付き・昼（11:41 起動）**。カルーセルは出さない＝2026-10-20 依頼者決定）を作り、依頼者の OK を受けて承認する。`draft` で画像2枚（1枚目はリールのカバーに使う）とリール（MP4）が生成される。投稿されるのはリールのみ。OK がなければ昼の自動投稿はストック（確認不要の投稿）に自動で差し替わる（`publish.py` の仕様）。

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

## 4. 依頼者へ提示（この文面で）
- 見出し／本文（キャプション全文）／出典URL／2枚の画像
- リールMP4も添付する
- 「**OK と返信いただければ、今日の昼（11:41 以降）にリールを投稿します。11:30 までに返信がない場合は、確認不要のストック投稿が自動で出ます。**」

## 5. OK を受けたら
```
python3 automation/news_job.py approve     # 既存の当日分があればストックへ退避
git add -A && git commit -m "approve news $(date +%F)" && git push
```
修正指示があれば candidate.json を直して `draft` からやり直す。「今日はなし」なら `discard`。

## 6. 報告
最後に1行：日付／見出し／承認の有無／出典。
