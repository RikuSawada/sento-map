# EXPAND-008: 神奈川・兵庫パーサー実装

## 概要
神奈川県（k-o-i.jp）と兵庫県（hyogo1010.com）の公式組合サイトパーサーを実装する。

## 変更内容

### `batch/parsers/kanagawa.py`（新規）
- 一覧: `/search_area/yokohama/`, `/search_area/kawasaki/`, `/search_area/shonan/`
- 個別: `/koten/{slug}/`
- 緯度経度: 個別ページで調査

### `batch/parsers/hyogo.py`（新規）
- 一覧: `https://hyogo1010.com/sento_list/` の `.data-sento` div に JSON埋め込み（全74件一括）
- **注意**: JSON内の `"lat"` キー = 実際の経度, `"lng"` キー = 実際の緯度（スワップ）
  ```python
  actual_lat = float(data["lng"])
  actual_lng = float(data["lat"])
  ```

### `batch/parsers/__init__.py`
- PARSERS に `"神奈川県": KanagawaParser, "兵庫県": HyogoParser` 追加

## ブランチ
`feature/expand-008-kanagawa-hyogo`

## ステータス
- [ ] 実装
- [ ] テスト
- [ ] PR
