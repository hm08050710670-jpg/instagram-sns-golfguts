# Instagram＋Facebook 自動投稿｜セットアップ手順（Facebookページ連携方式）

方式：**Facebookログイン＋ページアクセストークン**（Meta公式。Instagram と Facebookページの両方に投稿できる。ページトークンは期限なし）
前提：Facebookページ「GOLF GUTS」作成済み（2026-10-20）、Instagram @golfguts とリンク済み。
所要：初回のみ 20〜30分。**PCのブラウザ推奨**。
各ステップが終わるごとに「○番まで終わった」と教えてください。詰まったらスクショを送ってください。
公式：[Instagram Platform – Content Publishing](https://developers.facebook.com/documentation/instagram-platform/content-publishing)

---

## STEP 1｜リンクの確認（1分・済んでいれば飛ばす）
Instagram → プロフィールを編集 → 一番下「ビジネスの公開情報」→ **Facebook：GOLF GUTS** と出ていればOK。

## STEP 2｜Meta開発者アカウントとアプリを作る（10分）
1. https://developers.facebook.com/ → 右上「ログイン」→ Facebookアカウント **ゴルフ ガッツ**（ページの管理者）でログイン
2. 初回は「Meta for Developersに登録」→ 認証
3. **マイアプリ** → **アプリを作成**
4. ユースケース：「**その他**」→ アプリタイプ：「**ビジネス**」→ アプリ名 `GOLF GUTS SNS`、連絡先メール → **アプリを作成**
5. ダッシュボードの「製品を追加」で **Instagram** を「設定」（Facebookログインも自動で入ります）

## STEP 3｜トークンを取る（10分・いちばん大事）
1. https://developers.facebook.com/tools/explorer/ （グラフAPIエクスプローラ）を開く
2. 右上「Metaアプリ」で STEP 2 のアプリを選ぶ
3. 「アクセス許可」に次を追加する（検索して追加）
   `pages_show_list`　`pages_read_engagement`　`pages_manage_posts`　`instagram_basic`　`instagram_content_publish`　`business_management`
4. 「Generate Access Token」→ ログイン → **GOLF GUTS ページ**と **@golfguts** を選び、すべて許可
5. 出てきたトークン（短期・1時間）をコピーし、同じ画面の右上「ツール」→ **アクセストークンデバッガー**（https://developers.facebook.com/tools/debug/accesstoken/）に貼る → 下の「**アクセストークンを延長**」を押す → 延長されたトークン（長期・60日）をコピー
6. エクスプローラに戻り、アクセストークン欄に **長期トークン**を貼ってから、URL欄に次を入れて「送信」
   ```
   me/accounts?fields=name,id,access_token,instagram_business_account
   ```
7. 結果の中の GOLF GUTS ページの
   - `access_token` → **ページアクセストークン**（期限なし。これを使う）
   - `id` → **FB_PAGE_ID**
   - `instagram_business_account.id` → **IG_USER_ID**
   の3つを控える
   - `instagram_business_account` が出ない場合：STEP 1 のリンクが未完了か、許可画面でページ／Instagramを選び忘れ → 4からやり直し

## STEP 4｜GitHub に登録（5分）
https://github.com/hm08050710670-jpg/instagram-sns-golfguts/settings/secrets/actions
- **Secrets** タブ → **New repository secret** を3回
  - Name `IG_USER_ID`　Secret：STEP 3-7 の instagram_business_account.id
  - Name `IG_ACCESS_TOKEN`　Secret：STEP 3-7 のページアクセストークン
  - Name `FB_PAGE_ID`　Secret：STEP 3-7 のページ id（Facebookに同時投稿しない場合は登録しない）
- **Variables** タブ → **New repository variable**
  - Name `POST_MODE`　Value `dry-run`（動作確認後に `live` へ）

## STEP 5｜動作確認（私がやります）
1. Actions「Instagram daily post」を `check` で実行 → トークン・ページ・画像URL到達を確認（投稿しない）
2. 11/1 の投稿を承認し `live` で1件だけ手動実行 → Instagram と Facebookページに出るか確認
3. 以後は毎日12:00 JSTに自動。毎週月曜にヘルスチェック。問題はIssueで通知

---

## トークンの期限について
- STEP 3-7 で取る**ページアクセストークン**は、長期ユーザートークンから取得したものなので期限がありません（公式仕様）。
- ただし、パスワード変更・アプリの権限取り消し・Facebookのセキュリティ措置で失効することがあります。失効すると月曜のヘルスチェックがIssueで知らせるので、その時だけ STEP 3 をやり直して `IG_ACCESS_TOKEN` を更新してください。

## うまくいかないとき
| 症状 | 原因と対処 |
|---|---|
| me/accounts にページが出ない | ログイン中のFacebookアカウントがページ管理者でない／許可画面でページを選んでいない → STEP 3-4 からやり直し |
| `instagram_business_account` が出ない | Instagramとページのリンクが未完了（STEP 1）、またはInstagramがプロアカウントでない |
| 投稿時 `(#10) permission` | `instagram_content_publish` を許可していない → STEP 3-3〜4 |
| Facebookだけ失敗 | `pages_manage_posts` 未許可。Instagramは投稿されるので急ぎではない |
| `Media ID is not available` | 画像URLにMetaが到達できない → GitHub Pagesの公開を確認（私が見ます） |
| 審査（App Review）を求められる | 自分のアカウント・ページへの投稿は開発モードで動く見込み。求められた場合のみ申請（申請文は私が用意） |

---

## 実施記録（2026-10-20）
- STEP 1〜4 完了。アプリ名 `GOLF GUTS SNS`。ページトークンは「ユーザーまたはページ」で GOLF GUTS を選んで取得
- check 実行：成功（run 39383566756）
- live 実行：成功（2026-10-20 テスト投稿 → アーカイブ）
- 未完了：`pages_manage_posts`（Facebook同時投稿用）。アプリの「アクセス許可と機能」で追加 → エクスプローラで再度 Generate → ページトークンを取り直し → `IG_ACCESS_TOKEN` を更新
- 残り：`POST_MODE` を `live` に変更（10/31 まで）
