# GOLF GUTS｜SNS集客（Instagram毎日投稿＋初回スイングdock LP）

恵比寿のインドアゴルフスクール GOLF GUTS のSNS運用・LP制作の作業リポジトリ。
基準はすべて `CLAUDE.md`。新しい作業はこれを読んでから始める。

## 構成
| フォルダ | 内容 |
|---|---|
| `CLAUDE.md` | 運用仕様（事業情報・ゴール・ルール・決定事項・進捗） |
| `brand_guide.md` / `brand_colors.png` | デザイン指定書（配色・フォント・写真） |
| `docs/index.html` | 初回スイングdock 予約LP（単一ファイル。GitHub Pagesで確認用に公開可） |
| `sns/` | 4週間の企画・原稿、堀コーチ確認依頼シート、撮影リスト |
| `images/` | SNS画像の生成スクリプト `make_post_images.py`、原稿データ `posts.json`、出力 `out/` |
| `data/weekly_review.xlsx` | 週次振り返り記録表（個人名は書かない） |
| `photos/` | 店内写真（リポジトリを非公開にしてから追加） |

## 画像の生成
```
cd images && python3 make_post_images.py
```
`posts.json` に文言を書くと、ブランド配色の 1080×1080 PNG が `images/out/` に出力される。

## LPの確認用公開（GitHub Pages）
Settings → Pages → Source: Deploy from a branch → Branch: main / `/docs` → Save。
本番は golf-guts.co.jp 側に設置する（Pagesは確認用）。

## 注意
- 予約URL・店内写真・記録表を含むため **非公開リポジトリ** で運用する
- 指導内容に関わる原稿は、堀コーチの確認後に投稿する（`sns/review_request_hori.md`）
