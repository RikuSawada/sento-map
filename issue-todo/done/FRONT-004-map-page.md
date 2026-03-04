# FRONT-004: 地図ページ実装 (Google Maps 統合)

## 概要
`front/src/app/pages/map/` にメイン地図ページを実装する。
Google Maps JavaScript API を `@angular/google-maps` 経由で使用し、銭湯ピンを表示する。

## やること
- [ ] `npm install @angular/google-maps` でパッケージインストール
- [ ] `front/src/app/pages/map/map.component.ts` + `.html` + `.css`
  - `<google-map>` コンポーネントで東京中心に表示（lat: 35.6762, lng: 139.6503, zoom: 12）
  - 地図の表示範囲変更時に `SentoService.getSentos(bounds)` を呼び出し
  - 取得した銭湯データを `<map-marker>` で表示
  - マーカークリックで銭湯詳細ページへ遷移
- [ ] `app.routes.ts` に `/map` ルート追加（デフォルトルート）
- [ ] Google Maps API キーを `environment.ts` 経由で読み込む
- [ ] `index.html` の `<script>` タグではなく、`bootstrapApplication` の `providers` でロード
- [ ] 地図ロード中・エラー時のフォールバック表示

## セキュリティ
- GCP コンソールで API キーのリファラー制限（`localhost:4200`, 本番ドメイン）を設定すること
- API キーをコードに直書きしないこと

## 完了条件
- 地図上に銭湯ピンが表示される
- ピンクリックで詳細ページに遷移できる

## 依存
- FRONT-002 (SentoService)
- BACK-006 (銭湯 API)
