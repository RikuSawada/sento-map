# CLAUDE.md

## Claude Code への注意事項

- 挨拶・前置き・段階報告・絵文字禁止。結論ファースト
- 指摘すべきことは率直に指摘
- 実装前に必ず該当ファイルを読んでから変更すること
- テストなしで実装を完了させないこと
- 破壊的な変更（DB スキーマ変更など）は事前に確認を取ること
- コミットは日本語でわかりやすく書くこと

## 役割

- タスク管理のマネージャ
- システム開発

## コンテンツワークフロー

- ブレスト・構成の中間成果は `ideas/[YYYYMMDD]-[topic].md` に即保存
- 長時間タスクはステップ分割し、各完了後にファイル保存
- 説明には必ず具体例を含める

## Plan Mode

- プランファイルには**意図**（なぜ必要か）と**選択理由**を含める

## プロジェクト概要

- **目的**: 東京の銭湯情報を地図上で表示し、口コミを投稿できる Web アプリ
- **データソース**: https://www.1010.or.jp/map/ をバッチスクレイピングして PostgreSQL に格納
- **技術スタック**:
  - フロントエンド: Angular（`front/` ディレクトリ、バックエンドと分離）+ Google Maps JavaScript API
  - バックエンド: FastAPI（Python、`back/` ディレクトリ）、REST API として提供
  - DB: PostgreSQL
  - バッチ: スクレイピングスクリプト（`batch/` ディレクトリ、定期実行）
  - 認証: ユーザ登録・ログイン機能あり（口コミ投稿に必要）、JWT 認証
- **パッケージマネージャ**: バックエンド: uv / フロントエンド: npm

## 開発環境セットアップ

```bash
# バックエンド
cd back
uv sync
uv run uvicorn app.main:app --reload   # API サーバー起動 (port 8000)
uv run pytest                          # テスト実行
uv run alembic upgrade head            # DB マイグレーション適用

# フロントエンド
cd front
npm install
npm start                              # 開発サーバー起動 (port 4200)
npm test                               # テスト実行
npm run build                          # プロダクションビルド

# バッチ
cd batch
uv run python scraper.py               # スクレイピング実行
```

## アーキテクチャ

```
sento-map/
├── front/                    # Angular アプリ
│   ├── src/app/
│   │   ├── pages/            # ページコンポーネント（map, sento-detail, login, register）
│   │   ├── components/       # 再利用可能コンポーネント（sento-card, review-form 等）
│   │   ├── services/         # API クライアント（sento, review, auth）
│   │   └── models/           # TypeScript インターフェース
│   └── package.json
├── back/                     # FastAPI アプリ
│   ├── app/
│   │   ├── main.py           # エントリポイント・CORS 設定
│   │   ├── routers/          # エンドポイント（sento, review, auth）
│   │   ├── models/           # SQLAlchemy モデル（Sento, Review, User）
│   │   ├── schemas/          # Pydantic スキーマ
│   │   └── crud/             # DB 操作
│   ├── alembic/              # DB マイグレーション
│   ├── tests/                # pytest テスト
│   └── pyproject.toml
└── batch/                    # スクレイピングバッチ
    ├── scraper.py             # 1010.or.jp スクレイパー
    └── pyproject.toml
```

## コーディング規約

**バックエンド (Python)**
- 型ヒント必須（mypy 準拠）
- FastAPI のルートは `routers/` に分割、`main.py` に直接書かない
- DB アクセスは `crud/` に集約し、ルータから直接 ORM を触らない
- パスワードは bcrypt でハッシュ化、平文保存禁止
- 環境変数は `.env` で管理し、`pydantic-settings` で読み込む
- CORS は `back/app/main.py` で Angular の origin のみ許可

**フロントエンド (Angular)**
- コンポーネントは `pages/`（ルーティング単位）と `components/`（再利用）に分離
- API 呼び出しは必ず `services/` 経由、コンポーネントから直接 fetch しない
- 型定義は `models/` に集約し、`any` 型の使用禁止
- ファイル名: ケバブケース（`sento-card.component.ts`）
- 地図: `@angular/google-maps` ラッパーを使用（`google-maps` npm パッケージ）
- Google Maps API キーは環境変数 `GOOGLE_MAPS_API_KEY` で管理し、`environment.ts` 経由で参照

**バッチ (Python)**
- スクレイピング間隔は最低 1 秒以上設けること
- 失敗時はリトライせず、エラーログを出力して次の処理に進む
- 既存データとの差分のみ UPDATE する設計にすること

## テスト要件

### カバレッジ目標
- バックエンド: 80% 以上（pytest-cov で計測）
- フロントエンド: 80% 以上（Karma カバレッジレポート）
- CI でカバレッジが 80% を下回る場合はマージブロック

### バックエンド（pytest）

**ユニットテスト（`back/tests/unit/`）**
- `schemas/` のバリデーション: 正常値・異常値・境界値
- `crud/` の関数: モック DB を使い、SQL の正確性を検証
- 対象: 全 crud 関数、全 Pydantic スキーマ

**API 統合テスト（`back/tests/integration/`）**
- FastAPI `TestClient` を使用
- ルーター（`sento`, `review`, `auth`）ごとにファイルを分割
- テスト DB（テスト用 PostgreSQL スキーマ or SQLite）を使用
- 検証項目: ステータスコード、レスポンス JSON 構造、エラーレスポンス
- 認証が必要なエンドポイントは未認証アクセスが 401 を返すことも確認

**テスト用 fixtures（`back/tests/conftest.py`）**
- `test_db` セッションの提供
- テスト用ユーザー・銭湯データのシードデータ

### フロントエンド（Jasmine/Karma + Playwright）

**サービス層ユニットテスト（`front/src/app/services/*.spec.ts`）**
- `HttpClientTestingModule` を使用
- 各サービスメソッドが正しいエンドポイントに正しいペイロードで呼び出すことを検証
- エラーレスポンス時の挙動も検証

**コンポーネントユニットテスト（`front/src/app/**/*.spec.ts`）**
- `TestBed` で各コンポーネントを独立してレンダリング
- サービスはモック（`jasmine.createSpyObj`）を使用
- 検証項目: DOM の表示内容、ユーザー操作（クリック・フォーム入力）への反応

**E2E テスト（`front/e2e/`、Playwright）**
- 主要シナリオのみ実装（保守コストが高いため最小限に）
  1. 地図上に銭湯ピンが表示されること
  2. 銭湯詳細ページが開けること
  3. ユーザー登録 → ログイン → 口コミ投稿の一連フロー

### CI（GitHub Actions）

- `ci-back.yml`: PR 時に pytest 実行 → カバレッジ 80% 未満でマージブロック
- `ci-front.yml`: PR 時に `npm test -- --coverage` 実行 → カバレッジ 80% 未満でマージブロック
- `ci-e2e.yml`: main マージ時のみ Playwright E2E 実行（PR 毎には不要）
- バッチ（scraper）のテストは対象外（スクレイピング先の変更で壊れるリスクが高いため）

## 注意事項

- 1010.or.jp の robots.txt・利用規約を確認してからスクレイピング実装すること
- スクレイピング時はリクエスト間隔を設けてサーバに負荷をかけないこと
- モバイルファーストで実装すること（銭湯検索はスマホ利用が主）
- JWT シークレットキーは必ず環境変数で管理すること
- Google Maps API キーはブラウザから見えるため、GCP コンソールでリファラー制限を必ず設定すること

## 禁止事項

- `rm -rf` の実行
- `git push --force` の実行
- `git reset --hard` の実行
- `sudo` を使ったコマンド実行
- API キー・秘密情報のコードへの直書き
- テストなしでの機能実装完了の宣言
