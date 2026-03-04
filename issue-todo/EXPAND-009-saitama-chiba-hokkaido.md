# EXPAND-009: 埼玉・千葉・北海道パーサー実装

## 概要
埼玉県（saiyoku.jp）・千葉県（chiba1126sento.com）・北海道（kita-no-sento.com）の
公式組合サイトパーサーを実装する。

## 変更内容

### `batch/parsers/saitama.py`（新規）
- 個別 URL: `/id-1/{ID}/`
- ホームページが403の場合は User-Agent ヘッダー確認、解消しない場合 OSM インポートに切り替え

### `batch/parsers/chiba.py`（新規）
- WordPress ベース: `/?page_id={N}`
- エリア一覧ページ → 個別ページ ID を収集 → スクレイプ

### `batch/parsers/hokkaido.py`（新規）
- 一覧: `https://www.kita-no-sento.com/sentolist/` （100+件）
- 個別: `/sento/{ID}/`

### `batch/parsers/__init__.py`
- PARSERS に `"埼玉県": SaitamaParser, "千葉県": ChibaParser, "北海道": HokkaidoParser` 追加

## ブランチ
`feature/expand-009-saitama-chiba-hokkaido`

## ステータス
- [ ] 実装
- [ ] テスト
- [ ] PR
