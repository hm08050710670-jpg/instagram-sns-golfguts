# Instagram 自動投稿｜セットアップ手順（あなたがやる部分）

所要：初回のみ 30〜60分。終わったら「設定した」と一言ください。私が check モードで動作確認します。
公式手順：[Instagram Platform – Content Publishing](https://developers.facebook.com/documentation/instagram-platform/content-publishing)

## 0. 前提（確認だけ）
- [ ] Instagram @golfguts が **プロアカウント**（ビジネス or クリエイター）
- [ ] GOLF GUTS の **Facebookページ** がある（なければ作る。投稿しなくてよい）
- [ ] Instagram の設定 → アカウント → 「Facebookページをリンク」でそのページと連携

## 1. Metaアプリを作る（無料）
1. https://developers.facebook.com/ にFacebookアカウントでログイン → 「マイアプリ」→「アプリを作成」
2. ユースケース：「その他」→ アプリタイプ「ビジネス」→ 名前は `GOLF GUTS Instagram` など
3. ダッシュボード → 「製品を追加」→ **Instagram** を追加
4. 「アプリの役割」→ 自分をテスター/管理者として確認（自分のアカウントに投稿するだけなら開発モードで動く見込み。動かなければ App Review を申請）

## 2. アクセストークンを取る
1. 「ツール」→ **グラフAPIエクスプローラ**
2. 右上でアプリを選び、「ユーザーまたはページ」→ 権限に次を追加
   `instagram_basic`, `instagram_content_publish`, `pages_show_list`, `pages_read_engagement`, `business_management`
3. 「Generate Access Token」→ Facebookでログインして、GOLF GUTSページとInstagramアカウントを許可
4. 出てきたトークン（短期）を **長期トークンに交換**：ブラウザで次のURLを開く（APP_ID／APP_SECRET はアプリの「設定 → ベーシック」）
   ```
   https://graph.facebook.com/v21.0/oauth/access_token?grant_type=fb_exchange_token&client_id=APP_ID&client_secret=APP_SECRET&fb_exchange_token=短期トークン
   ```
   返ってきた `access_token` が長期トークン（約60日）
5. **Instagram ユーザーID** を取る：グラフAPIエクスプローラで
   `me/accounts?fields=name,instagram_business_account` を実行 → GOLF GUTSページの `instagram_business_account.id`（数字）

## 3. GitHub に登録
リポジトリ `instagram-sns-golfguts` → Settings → Secrets and variables → Actions
- **Secrets**（New repository secret）
  - `IG_USER_ID`：手順2-5 の数字
  - `IG_ACCESS_TOKEN`：手順2-4 の長期トークン
- **Variables**（Variables タブ → New repository variable）
  - `POST_MODE`：最初は `dry-run`。動作確認が済んだら `live` に変える

## 4. 動作確認（私がやります）
1. Actions → 「Instagram daily post」→ Run workflow → mode: `check` → 画像URLの到達とトークンの有効性を確認（投稿しない）
2. 問題なければ、11/1 の投稿を `approved: true` にして mode: `live` で手動実行 → 実際に1件投稿して確認
3. 以後は毎日 12:00 JST に自動実行。`POST_MODE=live` にしておく

## 5. 日々の運用（人がやること）
- **承認**：`automation/schedule.json` の該当日の `"approved": false` を `true` に（GitHubのWeb編集で1行）。私に「11/3〜11/9 承認」と言っていただければ代理で反映します
- **堀コーチ確認が必要な日**（`needs_hori: true`）は、確認シートの回答が来てから承認
- 未承認の日は投稿されず、Issueが自動で立ちます（抜けに気づける）
- トークンは約60日で失効。**12月中旬までに再発行**（手順2-4）して Secrets を更新。期限は私がIssueで事前に知らせます

## 6. うまくいかないとき
- 「(#10) Application does not have permission」→ 権限が足りない or アプリが開発モードで対象アカウントがテスターでない → アプリの役割に自分を追加
- 「Media ID is not available」→ 画像URLにMetaが到達できていない → GitHub Pagesが公開されているか、JPEGか
- 「Page Publishing Authorization」→ Facebookページの認証が必要。ページ設定で本人確認を完了
- 投稿数上限：24時間で25〜100件。毎日1件なら無関係
