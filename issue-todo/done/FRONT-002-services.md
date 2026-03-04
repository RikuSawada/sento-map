# FRONT-002: API サービス実装

## 概要
`front/src/app/services/` にバックエンド API を呼び出すサービスを実装する。
コンポーネントから直接 fetch/http を叩くことを禁止し、テスタビリティを確保する。

## やること
- [ ] `front/src/app/services/sento.service.ts`
  - `getSentos(params?: {lat_min, lat_max, lng_min, lng_max, page, per_page})` → `Observable<SentoListResponse>`
  - `getSento(id: number)` → `Observable<Sento>`
- [ ] `front/src/app/services/review.service.ts`
  - `getReviews(sentoId: number, page?: number)` → `Observable<Review[]>`
  - `createReview(sentoId: number, data: ReviewCreate)` → `Observable<Review>`
- [ ] `front/src/app/services/auth.service.ts`
  - `register(data: RegisterRequest)` → `Observable<User>`
  - `login(data: LoginRequest)` → `Observable<TokenResponse>`
  - `logout()` — localStorage からトークン削除
  - `getMe()` → `Observable<User>`
  - `isLoggedIn()` → `boolean`
  - `getToken()` → `string | null`
- [ ] `front/src/app/interceptors/auth.interceptor.ts` — Authorization ヘッダー自動付与
- [ ] `environment.ts` / `environment.prod.ts` に `apiUrl` と `googleMapsApiKey` 追加
- [ ] `app.config.ts` に `provideHttpClient(withInterceptors([authInterceptor]))` 追加

## 完了条件
- 各サービスのユニットテスト (`*.spec.ts`) が通る
- `HttpClientTestingModule` を使い、エンドポイント・ペイロードを検証

## 依存
- FRONT-001 (モデル定義)
