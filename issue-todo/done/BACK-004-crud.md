# BACK-004: CRUD 関数実装

## 概要
`back/app/crud/` に DB 操作を集約する。ルーターから直接 ORM を触る実装を禁止し、
テスタビリティと保守性を確保する。

## やること
- [ ] `back/app/crud/__init__.py` 作成
- [ ] `back/app/crud/sento.py`
  - `get_sento(db, sento_id)` — 1件取得
  - `get_sentos(db, skip, limit)` — 一覧取得（ページネーション）
  - `upsert_sento(db, data)` — バッチからの差分更新用（name or url でユニーク判定）
- [ ] `back/app/crud/review.py`
  - `get_reviews_by_sento(db, sento_id, skip, limit)`
  - `create_review(db, user_id, data: ReviewCreate)`
  - `get_review(db, review_id)` — 存在確認用
- [ ] `back/app/crud/user.py`
  - `get_user_by_email(db, email)`
  - `create_user(db, data: UserCreate)` — bcrypt ハッシュ化込み
  - `get_user(db, user_id)`
- [ ] `back/app/database.py` — AsyncSession factory (`get_db` dependency)

## 完了条件
- 各関数が型ヒント付きで実装されている
- `get_db` が FastAPI の Depends で使える

## 依存
- BACK-001 (モデル)
- BACK-003 (スキーマ)
