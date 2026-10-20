# Instagram 自動投稿｜セットアップ手順（Facebookページ不要）

方式：**Instagram API with Instagram Login**（Meta公式。Facebookページを作らずに、Instagramのプロアカウントだけで投稿できる）
所要：初回のみ 20〜30分。PCのブラウザ推奨（スマホでも可）。
各ステップが終わるごとに「○番まで終わった」と教えてください。詰まったらスクショを送ってください。
公式：[Instagram API with Instagram Login](https://developers.facebook.com/documentation/instagram-platform/instagram-api-with-instagram-login) ／ [Get started](https://developers.facebook.com/documentation/instagram-platform/instagram-api-with-instagram-login/get-started)

---

## STEP 1｜Instagramをプロアカウントにする（2分。すでにプロなら飛ばす）
Instagramアプリ → プロフィール → 右上≡ → **設定とプライバシー** → **アカウントの種類とツール** → **プロアカウントに切り替える** → **ビジネス** を選ぶ。
（Facebookページとの連携を求められても「スキップ」でOK）

## STEP 2｜Meta開発者アカウントとアプリを作る（10分）
1. https://developers.facebook.com/ → 右上「ログイン」
   ※ Facebookアカウントでのログインになります。**ページは作りません**。個人アカウントで大丈夫です
2. 初回は「Meta for Developersに登録」→ 認証
3. **マイアプリ** → **アプリを作成**
4. ユースケース：「**その他**」→ アプリタイプ：「**ビジネス**」→ アプリ名 `GOLF GUTS Instagram`、連絡先メール → **アプリを作成**
5. ダッシュボード左メニュー → **Instagram** → **「API setup with Instagram business login」**（日本語表示では「Instagramビジネスログインを使用したAPI設定」）を開く

## STEP 3｜Instagramアカウントを追加してトークンを取る（5分・いちばん大事）
同じ画面（API setup with Instagram business login）で：
1. 「**Generate access tokens**」の欄 → **Add account**（Instagramアカウントを追加）→ @golfguts でログインして許可
2. 追加された @golfguts の横の **Generate token** を押す → ログイン → 権限の許可画面で全部にチェック → 表示されたトークンを**コピー**
   - これが **長期トークン（60日有効）**。私の仕組みが毎週自動で延長するので、以後の手作業は不要です
3. 同じ画面に表示される **Instagram account ID**（数字）をコピー
   - 出ていない場合：ブラウザのアドレス欄に `https://graph.instagram.com/me?fields=user_id,username&access_token=トークン` を貼って開くと `"user_id":"数字"` が出ます

## STEP 4｜GitHub に登録（5分）
https://github.com/hm08050710670-jpg/instagram-sns-golfguts/settings/secrets/actions
- **Secrets** タブ → **New repository secret** を2回
  - Name `IG_USER_ID`　Secret：STEP 3-3 の数字
  - Name `IG_ACCESS_TOKEN`　Secret：STEP 3-2 のトークン
- **Variables** タブ → **New repository variable**
  - Name `POST_MODE`　Value `dry-run`（動作確認後に `live` へ）

## STEP 5｜トークン自動延長用のPAT（5分・任意だが推奨）
トークンは60日で切れます。自動延長の仕組みが「新しいトークンをSecretsに書き戻す」ために、GitHubのPersonal Access Tokenが1つ必要です。
1. https://github.com/settings/personal-access-tokens/new （Fine-grained）
2. Token name `golfguts-secrets`、Expiration：1年、Repository access：**Only select repositories** → `instagram-sns-golfguts`
3. Permissions → Repository permissions → **Secrets: Read and write** → Generate
4. 表示されたトークンを、STEP 4 と同じ画面で **New repository secret** → Name `GH_PAT`
（これを省く場合は、約50日ごとに STEP 3-2 を手でやり直し、`IG_ACCESS_TOKEN` を更新する運用になります。ヘルスチェックのIssueで知らせます）

## STEP 6｜動作確認（私がやります）
1. Actions「Instagram daily post」を `check` で実行 → トークン有効・画像URL到達を確認（投稿しない）
2. 11/1 の投稿を承認し `live` で1件だけ手動実行 → Instagramに出るか確認
3. 以後は毎日12:00 JSTに自動。毎週月曜にトークン延長＋ヘルスチェック。問題はIssueで通知

---

## うまくいかないとき
| 症状 | 原因と対処 |
|---|---|
| 「API setup with Instagram business login」が見当たらない | アプリタイプが「ビジネス」でない → 作り直す（STEP 2-4） |
| Generate token でエラー | Instagramがプロアカウントでない（STEP 1）、またはブラウザで別のInstagramにログイン中 → 一度Instagramからログアウトして再試行 |
| 投稿時 `(#10) permission` | 許可画面で `instagram_business_content_publish` を許可していない → Generate token をやり直して全権限を許可 |
| `Media ID is not available` | 画像URLにMetaが到達できない → GitHub Pagesの公開を確認（私が見ます） |
| 審査（App Review）を求められる | 自分のアカウントへの投稿は開発モードで動く見込み。求められた場合のみ申請（申請文は私が用意） |
