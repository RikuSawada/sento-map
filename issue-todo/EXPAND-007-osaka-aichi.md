# EXPAND-007: 大阪・愛知パーサー実装

## 概要
大阪府（osaka268.com）と愛知県（aichi1010.jp）の公式組合サイトパーサーを実装する。

## 変更内容

### `batch/parsers/osaka.py`（新規）
- 一覧: `https://osaka268.com/search/` の JS `childaMarkers` 配列から lat/lng + URL 抽出
- 個別ページで name/address/phone/hours/holiday 取得
- facility_type = 'sento'

### `batch/parsers/aichi.py`（新規）
- 一覧: `https://aichi1010.jp/page/list/l/{page}` ページネーション
- 個別: `https://aichi1010.jp/page/detail/l/{ID}`
- Google Maps リンク `maps?q=lat,lng` から座標抽出
- 名前: `[区名]` 部分を除去
- facility_type = 'sento'

### `batch/parsers/__init__.py`
- PARSERS に `"大阪府": OsakaParser, "愛知県": AichiParser` 追加

## ブランチ
`feature/expand-007-osaka-aichi`

## ステータス
- [ ] 実装
- [ ] テスト
- [ ] PR
