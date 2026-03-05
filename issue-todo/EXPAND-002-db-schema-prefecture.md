# EXPAND-002: DB スキーマ拡張（都道府県・地域フィールド）

## なぜ必要か

全国展開に伴い、銭湯データに「どの都道府県か」を持たせる必要がある。現在の `sentos` テーブルには都道府県フィールドがなく、住所から都度パースしなければならない。また全国検索・地域絞り込みのクエリ効率化のためにインデックスが必要。

## 選択理由

- `prefecture`（都道府県）カラムを追加することで、API の `?prefecture=大阪府` フィルタや、フロントのエリアセレクトを高速化できる
- `source_url` カラムを追加することで、各組合サイトの元 URL を保持し、データ更新時の差分判定に使用できる（現在は `url` が店舗 Web サイトを指しており混在を防ぐ）
- `region` カラム（関東・関西・九州等）はフロントのUI最適化に使用

## やること

### 1. Alembic マイグレーション作成

```sql
ALTER TABLE sentos
  ADD COLUMN prefecture VARCHAR(10),      -- 例: '東京都', '大阪府'
  ADD COLUMN region VARCHAR(20),           -- 例: '関東', '関西', '九州'
  ADD COLUMN source_url TEXT;              -- 組合サイトの元ページURL

CREATE INDEX ix_sentos_prefecture ON sentos(prefecture);
```

- `prefecture` は既存データに対して住所から自動補完するデータマイグレーションも同時に実施
  - `東京都` で始まる住所 → `prefecture = '東京都'`

### 2. SQLAlchemy モデル更新

`back/app/models/sento.py` に3カラム追加。

### 3. Pydantic スキーマ更新

`SentoResponse` に `prefecture: str | None` を追加。

### 4. CRUD 更新

`get_sentos()` に `prefecture` フィルタ引数を追加。

### 5. API エンドポイント更新

`GET /sentos?prefecture=東京都` クエリパラメータを追加。

### 6. バッチ db.py 更新

UPSERT 時に `prefecture`・`source_url` を書き込む。

## 完了条件

- [ ] マイグレーションが `alembic upgrade head` で適用できる
- [ ] 既存 380 件に `prefecture = '東京都'` が設定されている
- [ ] `GET /sentos?prefecture=東京都` が動作する
- [ ] バックエンドのテストが通る（新カラムのスキーマテスト追加）

## 破壊的変更への注意

**既存テーブルへの `ADD COLUMN`** のみ。`DROP` や `NOT NULL` 制約追加はしない。マイグレーション実行前に DB バックアップが望ましいが必須ではない（追加のみ）。

## 依存

- なし（最初に着手可能）
