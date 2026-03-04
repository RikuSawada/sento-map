# BACK-002: Alembic マイグレーション設定・初期スキーマ

## 概要
`back/alembic/` を初期化し、BACK-001 のモデルを元に初回マイグレーションを生成・適用する。
DB スキーマ変更は必ずマイグレーション経由で行う運用を確立する。

## やること
- [ ] `cd back && uv run alembic init alembic` で初期化（既にある場合はスキップ）
- [ ] `alembic/env.py` を修正 — `DATABASE_URL` を `app.config.settings` から読み込む、asyncpg 対応
- [ ] `alembic.ini` の `sqlalchemy.url` を env 経由に変更
- [ ] `uv run alembic revision --autogenerate -m "init"` で初回マイグレーション生成
- [ ] 生成されたマイグレーションファイルを確認・修正（自動生成の抜けを補完）
- [ ] `uv run alembic upgrade head` が正常終了することを確認
- [ ] `alembic/versions/` を git 管理対象に含める

## 完了条件
- `uv run alembic upgrade head` でエラーなく全テーブルが作成される
- `uv run alembic downgrade -1` でロールバックできる

## 依存
- BACK-001 (モデル定義が必要)
