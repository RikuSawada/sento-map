# BACK-006: 銭湯ルーター実装

## 概要
`back/app/routers/sento.py` に銭湯データの取得エンドポイントを実装する。
フロントエンドの地図表示・詳細ページから呼び出される READ 系 API。

## エンドポイント
| Method | Path | 説明 |
|--------|------|------|
| GET | /sentos | 一覧取得（ページネーション、緯度経度範囲フィルタ） |
| GET | /sentos/{sento_id} | 1件取得 |

## やること
- [ ] `back/app/routers/sento.py` 作成
- [ ] `GET /sentos` — クエリパラメータ: `page`, `per_page`, `lat_min`, `lat_max`, `lng_min`, `lng_max`
  - 地図の表示範囲でフィルタリングできること（地図スクロール時の動的ロード用）
- [ ] `GET /sentos/{sento_id}` — 存在しない場合は 404
- [ ] レスポンスは `SentoResponse` スキーマに合わせる
- [ ] `back/app/main.py` にルーター登録 (`prefix="/sentos"`)

## 完了条件
- `GET /sentos` が JSON 配列を返す
- `GET /sentos/9999` が 404 を返す
- 地図範囲フィルタが機能する

## 依存
- BACK-003 (スキーマ)
- BACK-004 (crud.sento)
