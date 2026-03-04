# FRONT-003: 認証ページ実装 (login, register)

## 概要
`front/src/app/pages/` にユーザー登録・ログインページを実装する。
口コミ投稿のために必要。モバイルファーストで実装する。

## やること
- [ ] `front/src/app/pages/login/login.component.ts` + `.html` + `.css`
  - email / password フォーム（ReactiveFormsModule）
  - バリデーション表示（required, email 形式）
  - 送信後 JWT を localStorage に保存 → 地図ページへリダイレクト
  - エラーメッセージ表示（401 時「メールアドレスまたはパスワードが違います」）
- [ ] `front/src/app/pages/register/register.component.ts` + `.html` + `.css`
  - username / email / password / password_confirm フォーム
  - password_confirm の一致バリデーション
  - 成功後ログインページへリダイレクト
- [ ] `front/src/app/app.routes.ts` に `/login`, `/register` ルート追加
- [ ] 認証済みユーザーが `/login` を開いた場合は地図ページへリダイレクト（AuthGuard）

## 完了条件
- ログインフローが E2E で動作する
- 未入力・不正入力でエラーメッセージが表示される
- モバイル表示で崩れない

## 依存
- FRONT-002 (AuthService)
