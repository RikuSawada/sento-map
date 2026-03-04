# BATCH-002: スクレイパー実装

## 概要
`batch/scraper.py` に 1010.or.jp から銭湯データを収集し、PostgreSQL に差分 UPSERT するスクレイパーを実装する。
BATCH-001 の調査結果に基づいて実装方針を決定すること。

## やること
- [ ] `batch/pyproject.toml` に依存追加 (`httpx` or `requests`, `beautifulsoup4`, `psycopg2-binary` or `asyncpg`, `sqlalchemy`)
- [ ] `batch/scraper.py` 実装
  - リクエスト間隔: 最低 1 秒以上 (`time.sleep(1)`)
  - User-Agent を適切に設定（ボットと分かる形で）
  - エラー時はリトライせず、ログ出力して次の処理に進む
  - 既存データとの差分のみ UPDATE（`url` or `name+address` でユニーク判定）
  - 取得できなかったフィールドは NULL で保存（欠損を許容）
- [ ] 住所から緯度経度を取得できない場合、ジオコーディング処理を追加
- [ ] `batch/scraper.py` に `--dry-run` オプション追加（DB に書き込まずログのみ）
- [ ] 実行ログを標準出力に出力（処理件数・成功/失敗件数）

## 実行方法（確認）
```bash
# 通常実行
docker compose --profile batch run --rm batch uv run python scraper.py

# ドライラン
docker compose --profile batch run --rm batch uv run python scraper.py --dry-run
```

## 完了条件
- `--dry-run` で銭湯データが標準出力に表示される
- 通常実行後、DB に銭湯データが投入されている
- 2回実行しても重複データが発生しない（UPSERT が機能している）

## 依存
- BATCH-001 (調査完了後)
- BACK-002 (DB スキーマ確定後)
