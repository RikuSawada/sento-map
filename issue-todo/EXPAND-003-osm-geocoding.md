# EXPAND-003: OSM Overpass API による座標補完

## なぜ必要か

各都道府県の組合サイトの一部は緯度経度を持たない（住所のみ）。現在のバッチは緯度経度がないとデータを保存できない（lat/lng は `NOT NULL`）。OSM Overpass API は完全無料・商用利用可能（ODbL ライセンス）で、日本全国の `amenity=public_bath` データを約5,624件保有しており、名前・住所によるマッチングで座標を補完できる。

## 選択理由

| 座標補完手段 | コスト | 精度 | 注意点 |
|---|---|---|---|
| **OSM Overpass API** | 無料（ODbL） | ○（ボランティア入力） | 帰属表示必須 |
| Google Geocoding API | 有料（$5/1,000件） | ◎ | 二次配布禁止 |
| 国土地理院 ジオコーダ | 無料 | △（住所精度） | POI なし、住所→座標のみ |

Google Geocoding API は**取得した座標の DB 保存が利用規約上グレー**（Google Maps サービス上での表示のみ許可）なため除外。OSM は座標データ自体の DB 保存・再配布が明示的に許可されている。

## OSM データ概要

```
日本国内 amenity=public_bath: 約5,624件
  - bath:type=sento: 銭湯
  - bath:type=super_sento: スーパー銭湯
  - bath:type=onsen: 温泉施設
```

Overpass API エンドポイント: `https://overpass-api.de/api/interpreter`

```python
# 都道府県単位でのクエリ例
query = """
[out:json][timeout:60];
area["name"="大阪府"]["admin_level"="4"]->.pref;
nwr(area.pref)[amenity=public_bath];
out body center;
"""
```

## やること

### 1. OSM マッチングスクリプト

`batch/osm_geocoder.py` を新規作成：

- 指定都道府県の OSM データを一括取得（1クエリで全件）
- 既存 DB の `lat IS NULL` の銭湯に対して名前・住所でファジーマッチング
- マッチしたら `lat`/`lng`/`source_geocoder='osm'` で UPDATE

マッチングロジック：
1. **名前完全一致** → 信頼度 高
2. **名前部分一致 + 住所の市区町村一致** → 信頼度 中（確認してから反映）
3. **住所のみ一致** → 信頼度 低（スキップ or ログ出力）

### 2. DB スキーマ追加（EXPAND-002 と同時対応可能）

```sql
ALTER TABLE sentos
  ADD COLUMN geocoded_by VARCHAR(20);  -- 'batch', 'osm', 'manual' 等
```

### 3. 実行オプション

```bash
# ドライラン（マッチング結果を表示するが DB 更新しない）
uv run python osm_geocoder.py --prefecture 大阪府 --dry-run

# 実際に更新
uv run python osm_geocoder.py --prefecture 大阪府
uv run python osm_geocoder.py --all  # 全都道府県
```

### 4. 帰属表示対応

フロントの地図表示画面に `© OpenStreetMap contributors` の帰属表示を追加（ODbL 要件）。Google Maps の attribution と並べて表示。

## 完了条件

- [ ] `osm_geocoder.py --dry-run` でマッチング結果を確認できる
- [ ] マッチング精度が目視確認で80%以上
- [ ] `geocoded_by` カラムで後から精度追跡できる
- [ ] フロントに OSM 帰属表示を追加

## 制約

- Overpass API 公開サーバーへの過度なリクエスト禁止（1クエリで都道府県単位の全件取得にし、ポーリングしない）
- ODbL ライセンスによりデータを改変して配布する場合はシェアアライク適用

## 依存

- EXPAND-002（`lat IS NULL` の銭湯データが存在するため、全国スクレイピング後に実施）
