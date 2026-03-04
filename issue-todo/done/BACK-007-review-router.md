# BACK-007: 口コミルーター実装

## 概要
`back/app/routers/review.py` に口コミの取得・投稿エンドポイントを実装する。
投稿は JWT 認証必須。

## エンドポイント
| Method | Path | 説明 |
|--------|------|------|
| GET | /sentos/{sento_id}/reviews | 指定銭湯の口コミ一覧 |
| POST | /sentos/{sento_id}/reviews | 口コミ投稿（要認証） |

## やること
- [ ] `back/app/routers/review.py` 作成
- [ ] `GET /sentos/{sento_id}/reviews` — 認証不要、ページネーション対応
- [ ] `POST /sentos/{sento_id}/reviews` — `get_current_user` Depends で認証チェック
  - sento_id が存在しない場合は 404
  - レスポンスは `ReviewResponse` (投稿者の username を含む)
- [ ] `back/app/main.py` にルーター登録

## 完了条件
- 未認証で POST すると 401
- 認証済みで POST すると 201 + ReviewResponse が返る
- GET で投稿済み口コミが取得できる

## 依存
- BACK-003 (スキーマ)
- BACK-004 (crud.review)
- BACK-005 (認証 Depends)
