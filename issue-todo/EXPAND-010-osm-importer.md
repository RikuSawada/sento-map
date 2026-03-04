# EXPAND-010: OSMインポーター拡張（新規レコード生成）

## 概要
`batch/osm_geocoder.py` に `--import-new` フラグを追加し、
残り37都道府県分の銭湯データを OSM から一括インポートできるようにする。

## 背景
公式サイトパーサーが未実装な都道府県向けにOSMデータを新規INSERTする手段が必要。
現在の osm_geocoder.py は既存レコードの座標補完のみ対応。

## 変更内容

### `batch/osm_geocoder.py`
- `--import-new` フラグ追加（既存の座標補完モードと排他）
- `amenity=public_bath` + `amenity=spa` を対象とする Overpass クエリ拡張
- `source_url = "osm:{element_id}"` で重複チェック・SKIP
- `facility_type` マッピング:
  - `amenity=public_bath` + `bath:type=onsen` → `'onsen'`
  - `amenity=public_bath`（その他）→ `'sento'`
  - `amenity=spa` → `'super_sento'`
- `geocoded_by = 'osm'`

### `batch/db.py`
- `upsert_sento` に `facility_type` パラメータサポート追加

## 利用例
```bash
uv run python osm_geocoder.py --import-new --prefecture 大分県 --dry-run
uv run python osm_geocoder.py --import-new --all
```

## ブランチ
`feature/expand-010-osm-importer`

## ステータス
- [ ] 実装
- [ ] テスト
- [ ] PR
