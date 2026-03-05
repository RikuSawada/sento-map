# EXPAND-004: Yahoo! ローカルサーチAPI による情報補完

## なぜ必要か

各都道府県組合サイトには**写真・評価点・詳細な営業時間（曜日ごとの時間）**が含まれていないことが多い。Yahoo! ローカルサーチAPI は無料枠50,000リクエスト/日と大きく、業種コード `gc=0418`（浴場）で銭湯を検索できる。組合サイトのデータと照合して、不足フィールドを補完する用途に使う。

## 選択理由

| API | 無料枠 | 写真 | 営業時間詳細 | ライセンス |
|---|---|---|---|---|
| **Yahoo! ローカルサーチ** | 50,000req/日 | ○ | ○（曜日別） | 商用可 |
| Google Places API | 5,000req/月（Nearby Pro） | ○ | ○ | 二次配布禁止 |
| OSM | 無制限 | × | △ | ODbL |

Google Places はデータの二次保存が利用規約上制限されるため、**表示用途**に限定するか使用しない。Yahoo! は商用利用可能で二次保存の制約が緩い。

## API 概要

```
エンドポイント: https://map.yahooapis.jp/LocalSearchService/V1/localSearch
パラメータ:
  - appid: Yahoo! デベロッパーネットワークで取得
  - query: 銭湯名
  - gc: 0418（浴場系業種コード）
  - lat/lon: 周辺検索の中心座標
  - dist: 検索半径（km）
  - output: json
  - results: 1-100
```

## やること

### 1. Yahoo! デベロッパーネットワーク登録・API キー取得

- `https://developer.yahoo.co.jp/` でアプリケーション登録
- `.env` に `YAHOO_LOCAL_SEARCH_API_KEY` を追加
- `CLAUDE.md` の環境変数リストを更新

### 2. enricher スクリプト作成

`batch/yahoo_enricher.py` を新規作成：

```python
# 対象: DB にある銭湯（名前 + lat/lng を使って周辺検索）
# 処理: Yahoo API でマッチした施設の以下フィールドを補完
#   - yahoo_rating: float | None  (Yahoo! の評価点)
#   - yahoo_review_count: int | None
#   - yahoo_category: str | None  (詳細業種名)
#   - photo_url: str | None       (サムネイル画像URL)
```

マッチング: 名前類似度 + 半径100m以内で一意に特定できる場合のみ更新

### 3. DB スキーマ追加

```sql
ALTER TABLE sentos
  ADD COLUMN yahoo_rating NUMERIC(3, 1),
  ADD COLUMN yahoo_review_count INTEGER,
  ADD COLUMN photo_url TEXT;
```

### 4. フロント反映

- カードに評価点バッジ（★ 4.2 など）を表示
- 詳細ページに写真サムネイルを表示

## 実行

```bash
uv run python yahoo_enricher.py --prefecture 東京都 --dry-run
uv run python yahoo_enricher.py --all
```

## 完了条件

- [ ] Yahoo! API キーの取得手順が `.env.example` にコメントで記載されている
- [ ] ドライランで既存 380 件に対するマッチング結果を確認できる
- [ ] マッチした銭湯に `yahoo_rating` が保存される
- [ ] フロントのカードに評価点が表示される

## 注意

- Yahoo! API の利用規約で「提供データの二次配布・販売禁止」の制限がある。**評価点・画像を別サービスに転売しないこと**
- レート制限: 50,000req/日の範囲内で1リクエスト/秒以上にしない
- `photo_url` は Yahoo! のサーバーを直接参照（ダウンロードして再配布しない）

## 優先度

**EXPAND-001〜003 完了後に着手**。写真・評価点はコア機能ではなく付加価値。

## 依存

- EXPAND-002（DB スキーマ）完了後
- EXPAND-001（全国データ）完了後が望ましいが、東京分だけで先行検証可能
