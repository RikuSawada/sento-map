# BACK-003: Pydantic スキーマ定義

## 概要
`back/app/schemas/` に API のリクエスト・レスポンス用 Pydantic スキーマを定義する。
ORM モデルとは分離し、DB の内部構造を API に露出しない設計にする。

## やること
- [ ] `back/app/schemas/__init__.py` 作成
- [ ] `back/app/schemas/user.py`
  - `UserCreate` (username, email, password)
  - `UserResponse` (id, username, email, created_at) ※ password 非公開
- [ ] `back/app/schemas/sento.py`
  - `SentoResponse` (id, name, address, lat, lng, phone, url, open_hours, holiday)
  - `SentoListResponse` (ページネーション対応: items, total, page, per_page)
- [ ] `back/app/schemas/review.py`
  - `ReviewCreate` (sento_id, rating, comment)
  - `ReviewResponse` (id, sento_id, user_id, username, rating, comment, created_at)
- [ ] `back/app/schemas/auth.py`
  - `TokenResponse` (access_token, token_type)
  - `LoginRequest` (email, password)
- [ ] 全フィールドに型ヒントと `Field(...)` バリデーション（rating は 1-5 制約等）
- [ ] `model_config = ConfigDict(from_attributes=True)` で ORM モード有効化

## 完了条件
- `uv run python -c "from app.schemas import UserResponse, SentoResponse, ReviewCreate"` が通る
- rating に 0 や 6 を渡すと ValidationError が発生する

## 依存
- BACK-001 (モデル定義参照)
