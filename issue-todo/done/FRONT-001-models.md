# FRONT-001: TypeScript モデル定義

## 概要
`front/src/app/models/` にバックエンド API レスポンスに対応する TypeScript インターフェースを定義する。
`any` 型の使用を禁止し、型安全なフロントエンド開発の基盤を作る。

## やること
- [ ] `front/src/app/models/sento.ts` — `Sento`, `SentoListResponse`
- [ ] `front/src/app/models/review.ts` — `Review`, `ReviewCreate`
- [ ] `front/src/app/models/user.ts` — `User`, `LoginRequest`, `RegisterRequest`, `TokenResponse`
- [ ] `front/src/app/models/index.ts` — 全モデルの re-export

## インターフェース仕様例
```typescript
export interface Sento {
  id: number;
  name: string;
  address: string;
  lat: number;
  lng: number;
  phone: string | null;
  url: string | null;
  openHours: string | null;
  holiday: string | null;
}
```

## 完了条件
- `models/` から全インターフェースが import できる
- バックエンドの Pydantic スキーマと対応している

## 依存
- BACK-003 (スキーマ定義参照)
