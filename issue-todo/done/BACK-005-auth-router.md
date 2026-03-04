# BACK-005: 認証ルーター実装 (JWT)

## 概要
`back/app/routers/auth.py` にユーザー登録・ログインエンドポイントを実装する。
口コミ投稿に必要な JWT 認証の基盤を提供する。

## エンドポイント
| Method | Path | 説明 |
|--------|------|------|
| POST | /auth/register | ユーザー登録 |
| POST | /auth/login | ログイン → JWT 発行 |
| GET | /auth/me | 現在ユーザー取得（要認証） |

## やること
- [ ] `back/app/routers/auth.py` 作成
- [ ] `back/app/auth.py` — JWT ユーティリティ
  - `create_access_token(data, expires_delta)` — python-jose 使用
  - `get_current_user(token)` — FastAPI Depends で使える形に
  - トークン有効期限は環境変数 `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`（デフォルト 60）
- [ ] `POST /auth/register` — email 重複時は 400
- [ ] `POST /auth/login` — パスワード不一致は 401、OAuth2PasswordRequestForm 形式
- [ ] `GET /auth/me` — Bearer トークン検証、無効なら 401
- [ ] `back/app/main.py` にルーター登録 (`prefix="/auth"`)
- [ ] `JWT_SECRET_KEY` を config.py の Settings に追加

## 完了条件
- register → login → /auth/me の一連フローが curl で確認できる
- 無効トークンで /auth/me を叩くと 401

## 依存
- BACK-003 (スキーマ)
- BACK-004 (crud.user)
