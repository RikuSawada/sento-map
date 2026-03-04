# CI-001: GitHub Actions CI 設定

## 概要
PR のマージ品質ゲートとして GitHub Actions ワークフローを設定する。
カバレッジ 80% 未満の PR はマージブロックされる。

## やること
- [ ] `.github/workflows/ci-back.yml`
  - トリガー: PR open/update
  - ステップ: `uv sync` → `uv run pytest --cov=app --cov-fail-under=80`
  - PostgreSQL service container を使用（テスト DB）
- [ ] `.github/workflows/ci-front.yml`
  - トリガー: PR open/update
  - ステップ: `npm ci` → `npm test -- --watch=false --coverage --browsers=ChromeHeadless`
  - カバレッジ 80% 未満でワークフロー失敗
- [ ] `.github/workflows/ci-e2e.yml`
  - トリガー: main へのマージ時のみ
  - ステップ: Docker Compose で全サービス起動 → Playwright 実行
- [ ] GitHub リポジトリの Branch Protection Rules で CI 必須化
  - `ci-back`, `ci-front` を required status checks に追加

## 完了条件
- PR を出すと自動で pytest・npm test が走る
- カバレッジ不足の PR がマージできない状態になる
- main マージ時に E2E が動く

## 依存
- BACK-008 (バックエンドテスト実装完了後)
- FRONT-006 (フロントエンドテスト実装完了後)
