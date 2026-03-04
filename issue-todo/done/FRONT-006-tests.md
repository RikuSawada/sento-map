# FRONT-006: フロントエンドテスト実装

## 概要
カバレッジ 80% 以上を達成する Jasmine/Karma テストと Playwright E2E テストを実装する。

## やること

### サービス層ユニットテスト
- [ ] `sento.service.spec.ts` — `HttpClientTestingModule` で GET /sentos, GET /sentos/:id を検証
- [ ] `review.service.spec.ts` — GET/POST エンドポイントとペイロードを検証
- [ ] `auth.service.spec.ts` — login 後の localStorage 保存、isLoggedIn の挙動を検証

### コンポーネントユニットテスト
- [ ] `login.component.spec.ts` — フォームバリデーション、送信時の AuthService 呼び出し
- [ ] `register.component.spec.ts` — password 不一致バリデーション
- [ ] `sento-detail.component.spec.ts` — ルートパラメータから API 呼び出しを検証
- [ ] `review-form.component.spec.ts` — 送信イベント発火の検証
- [ ] `map.component.spec.ts` — SentoService.getSentos が呼ばれることを検証

### E2E テスト (Playwright)
- [ ] `front/e2e/` ディレクトリ作成、Playwright インストール
- [ ] `e2e/map.spec.ts` — 地図上に銭湯ピンが表示されること
- [ ] `e2e/sento-detail.spec.ts` — 銭湯詳細ページが開けること
- [ ] `e2e/auth-review.spec.ts` — ユーザー登録 → ログイン → 口コミ投稿の一連フロー

### カバレッジ
- [ ] `npm test -- --coverage` で 80% 以上達成

## 完了条件
- `npm test` が全てパスする
- カバレッジ 80% 以上
- Playwright E2E 3シナリオが通る

## 依存
- FRONT-003, FRONT-004, FRONT-005 (実装完了後)
