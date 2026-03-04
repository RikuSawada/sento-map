# BACK-001: SQLAlchemy DB モデル実装

## 概要
`back/app/models/` に SQLAlchemy ORM モデルを定義する。
後続の Alembic マイグレーション・CRUD 実装の土台となるため最初に着手する。

## 対象テーブル
- `users` (User モデル)
- `sentos` (Sento モデル)
- `reviews` (Review モデル)

## やること
- [ ] `back/app/models/__init__.py` 作成
- [ ] `back/app/models/user.py` — id, username, email, hashed_password, created_at
- [ ] `back/app/models/sento.py` — id, name, address, lat, lng, phone, url, open_hours, holiday, created_at, updated_at
- [ ] `back/app/models/review.py` — id, sento_id (FK), user_id (FK), rating (1-5), comment, created_at
- [ ] `back/app/models/base.py` — DeclarativeBase + 共通カラム (created_at 等)
- [ ] 各モデルに型ヒント付与 (Mapped[...])
- [ ] Relationship 定義 (Sento.reviews, Review.user, Review.sento)

## 完了条件
- `uv run python -c "from app.models import User, Sento, Review"` がエラーなく通る
- 全カラムに型ヒントが付いている

## 依存
なし（最初に実装）
