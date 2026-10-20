# Instagram 自動投稿｜セットアップ手順（あなたがやる部分）

所要：初回のみ 40〜60分。スマホでもできますが、PCのブラウザのほうが楽です。
各ステップが終わるごとに「○番まで終わった」と教えてください。詰まったらスクショを送ってください。
公式：[Instagram Platform – Content Publishing](https://developers.facebook.com/documentation/instagram-platform/content-publishing)

---

## STEP 1｜Facebookページを作る（5分）
Instagram APIは「Facebookページに紐づいたInstagram」にしか投稿できません。ページ自体に投稿する必要はありません。

1. https://www.facebook.com/pages/create を開く（個人のFacebookアカウントでログイン）
2. ページ名：`GOLF GUTS`　カテゴリ：`ゴルフ場` または `スポーツ・レクリエーション`
3. 自己紹介は任意（例：恵比寿のインドアゴルフスクール）→「ページを作成」
4. プロフィール写真・カバーは任意。スキップしてOK

## STEP 2｜InstagramをプロアカウントにしてFacebookページと連携（5分）
1. Instagramアプリ → プロフィール → 右上≡ → **設定とプライバシー** → **アカウントの種類とツール**
2. 「プロアカウントに切り替える」→ **ビジネス** を選ぶ（すでにプロなら次へ）
3. 設定 → **ビジネスツールと管理** → **Facebookページをリンク** → STEP 1 のページを選ぶ
   （出てこない場合：Facebook側で ページ → 設定 → **リンク済みのアカウント** → Instagram → 接続）

## STEP 3｜Meta開発者アカウントとアプリを作る（10分）
1. https://developers.facebook.com/ → 右上「ログイン」（Facebookアカウント）
2. 初回は「Meta for Developersに登録」→ 電話/メール認証
3. **マイアプリ** → **アプリを作成**
4. ユースケース：「**その他**」→ アプリタイプ：「**ビジネス**」→ アプリ名 `GOLF GUTS Instagram`、連絡先メール → 作成
5. アプリのダッシュボード → 「製品を追加」→ **Instagram** の「設定」をクリック（追加されればOK）

## STEP 4｜アクセストークンを取る（15分・いちばん大事）
**ポイント：最後に「ページのアクセストークン」を取ると、期限なしで使えます（60日ごとの更新が不要）。**

1. 上部メニュー **ツール** → **グラフAPIエクスプローラ**（https://developers.facebook.com/tools/explorer/）
2. 右側「Metaアプリ」で `GOLF GUTS Instagram` を選ぶ
3. 「ユーザーまたはページ」→ **ユーザートークンを取得**
4. 「アクセス許可」に以下を追加（検索欄に入力して追加）
   - `pages_show_list`
   - `pages_read_engagement`
   - `instagram_basic`
   - `instagram_content_publish`
   - `business_management`
5. **Generate Access Token** → Facebookの許可画面 → GOLF GUTSページとInstagramアカウントに**チェックを入れて**許可
6. 画面に出た**短期トークン**をコピー（長い文字列）
7. **長期トークンに交換**：アプリの「アプリ設定 → ベーシック」で **アプリID** と **app secret**（「表示」を押す）を確認し、ブラウザのアドレス欄に次を貼って開く（3か所を置き換え）
   ```
   https://graph.facebook.com/v21.0/oauth/access_token?grant_type=fb_exchange_token&client_id=アプリID&client_secret=appsecret&fb_exchange_token=短期トークン
   ```
   表示された `"access_token":"..."` が長期ユーザートークン
8. **ページトークン（期限なし）とInstagram IDを取る**：アドレス欄に次を貼って開く（長期トークンを置き換え）
   ```
   https://graph.facebook.com/v21.0/me/accounts?fields=name,access_token,instagram_business_account&access_token=長期ユーザートークン
   ```
   GOLF GUTSページの行にある
   - `"access_token"` → **これが IG_ACCESS_TOKEN**（期限なし）
   - `"instagram_business_account": {"id": "数字"}` → **これが IG_USER_ID**
   （`instagram_business_account` が出ない場合は STEP 2 の連携ができていません）

## STEP 5｜GitHub に登録（5分）
https://github.com/hm08050710670-jpg/instagram-sns-golfguts/settings/secrets/actions
- **New repository secret** を2回
  - Name `IG_USER_ID`　Secret：STEP 4-8 の数字
  - Name `IG_ACCESS_TOKEN`　Secret：STEP 4-8 のページトークン
- 上の **Variables** タブ → **New repository variable**
  - Name `POST_MODE`　Value `dry-run`（動作確認が済んだら私が `live` に変えるよう案内します）

## STEP 6｜動作確認（私がやります）
1. Actions の「Instagram daily post」を `check` で実行 → トークン有効・画像URL到達を確認（投稿しない）
2. 11/1 の投稿を承認して `live` で1件だけ手動実行 → Instagramに出るか確認
3. 以後は毎日12:00 JSTに自動。トークンの健全性は毎週自動チェックし、異常があればIssueで知らせます

---

## うまくいかないとき
| 症状 | 原因と対処 |
|---|---|
| 許可画面にInstagramアカウントが出ない | STEP 2 の連携未完了。Facebookページ側の「リンク済みのアカウント」から接続 |
| `(#10) Application does not have permission` | STEP 4-4 の権限不足、またはアプリが開発モードで自分がテスターでない → アプリの「アプリの役割」に自分を追加 |
| `instagram_business_account` が返らない | Instagramがプロアカウントでない／ページ連携が別アカウント |
| `Media ID is not available` | 画像URLにMetaが到達できない → Pagesの公開を確認 |
| Page Publishing Authorization の警告 | Facebookページで本人確認が求められている → ページ設定で完了 |
| 審査（App Review）を求められる | 自分のアカウントへの投稿は開発モードで動く見込み。動かない場合のみ `instagram_content_publish` の審査を申請（私が申請文を用意します） |
