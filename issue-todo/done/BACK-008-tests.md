# BACK-008: バックエンドテスト実装

## 概要
カバレッジ 80% 以上を達成する pytest テストを実装する。
CI でのマージブロック運用の前提条件。

## やること

### テスト環境整備
- [ ] `pyproject.toml` に `pytest`, `pytest-asyncio`, `pytest-cov`, `httpx` を dev 依存追加
- [ ] `back/tests/conftest.py` — SQLite (in-memory) を使った `test_db` fixture、テスト用 User・Sento シードデータ
- [ ] `back/tests/__init__.py`, `back/tests/unit/__init__.py`, `back/tests/integration/__init__.py`

### ユニットテスト (`back/tests/unit/`)
- [ ] `test_schemas.py` — 各スキーマの正常値・異常値・境界値（rating=0, 6 で ValidationError 等）
- [ ] `test_crud_sento.py` — get_sento, get_sentos, upsert_sento をモック DB で検証
- [ ] `test_crud_review.py` — get_reviews_by_sento, create_review をモック DB で検証
- [ ] `test_crud_user.py` — create_user でパスワードがハッシュ化されていることを確認
- [ ] `test_auth.py` — create_access_token, get_current_user の正常・異常ケース

### 統合テスト (`back/tests/integration/`)
- [ ] `test_auth_router.py` — register, login, /auth/me の一連フロー、エラーケース
- [ ] `test_sento_router.py` — GET /sentos, GET /sentos/{id}、存在しない ID で 404
- [ ] `test_review_router.py` — 未認証 POST は 401、認証済み POST は 201、GET 一覧

### カバレッジ
- [ ] `uv run pytest --cov=app --cov-report=term-missing` で 80% 以上達成

## 完了条件
- `uv run pytest` が全てパスする
- カバレッジ 80% 以上

## 依存
- BACK-004, BACK-005, BACK-006, BACK-007 (実装完了後)
