# FRONT-005: 銭湯詳細ページ実装

## 概要
`front/src/app/pages/sento-detail/` に銭湯詳細ページを実装する。
銭湯情報 + 口コミ一覧 + 口コミ投稿フォームを表示する。

## やること
- [ ] `front/src/app/pages/sento-detail/sento-detail.component.ts` + `.html` + `.css`
  - ルートパラメータ `:id` から銭湯情報取得 (`SentoService.getSento(id)`)
  - 表示項目: 名前・住所・電話番号・URL・営業時間・定休日
  - 口コミ一覧表示（`ReviewService.getReviews(id)`）
  - 口コミ投稿フォーム（ログイン済みのみ表示）
  - ログアウト状態では「口コミを投稿するにはログインしてください」リンク
- [ ] `front/src/app/components/sento-card/sento-card.component.ts` — 地図ページ用の銭湯情報カード（マーカークリック時に表示）
- [ ] `front/src/app/components/review-form/review-form.component.ts` — 星評価 + テキストエリア
- [ ] `front/src/app/components/review-list/review-list.component.ts` — 口コミ一覧表示
- [ ] `app.routes.ts` に `/sentos/:id` ルート追加
- [ ] 銭湯が存在しない場合は 404 ページへリダイレクト

## 完了条件
- `/sentos/1` で銭湯情報が表示される
- 未ログイン時は口コミフォームが非表示
- 口コミ投稿後に一覧が更新される

## 依存
- FRONT-002 (SentoService, ReviewService)
- BACK-006, BACK-007 (API)
