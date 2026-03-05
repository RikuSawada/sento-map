# EXPAND-005: フロントエンド 全国対応

## なぜ必要か

全国展開に伴い、現在の「東京の区フィルタ」だけでは検索 UX が破綻する。約2,000件以上のデータを扱うために、都道府県単位のフィルタリング・地図の広域表示・パフォーマンス改善が必要になる。

## 選択理由

- 都道府県セレクタを最上位フィルタにすることで、数千件のデータを効率よく絞り込める
- `per_page=500` での全件取得はデータが増えると破綻する。都道府県選択をトリガーにAPIを叩く設計に切り替えることで、初期ロードを軽量化できる
- 地図の初期表示を日本全体（center: lat 36.2, lng 138.3, zoom 5）に変更し、都道府県選択で zoom in する

## やること

### 1. API クライアント変更（`SentoService`）

`getSentos()` に `prefecture` パラメータを追加：

```typescript
export interface SentoQueryParams {
  prefecture?: string;  // 追加
  lat_min?: number;
  // ...
}
```

### 2. MapComponent の都道府県フィルタ追加

現在の区フィルタ（`selectedArea`）に加えて、都道府県フィルタ（`selectedPrefecture`）を上位に追加：

- 都道府県を選択すると API で `?prefecture=大阪府&per_page=500` を叩き直す
- 都道府県未選択時は **全国から最大500件**を取得（初期表示は近隣か位置情報ベースに）
- 区フィルタは都道府県選択後にクライアントサイドで絞り込む

```
[都道府県セレクト] [区/市セレクト] [銭湯名テキスト検索]
```

### 3. 地図の初期座標変更

```typescript
// 現在（東京固定）
readonly center = { lat: 35.6762, lng: 139.6503 };
readonly zoom = 12;

// 変更後（全国表示）
readonly center = { lat: 36.2048, lng: 138.2529 };  // 日本の中心
readonly zoom = 6;
```

都道府県を選択したときに地図をその都道府県の中心に fly（`google.maps.Map.panTo` / `fitBounds`）。

### 4. パフォーマンス対応

全国で2,000件以上になる場合、マーカーが重すぎる問題：

- **MarkerClusterer** (`@googlemaps/markerclusterer`) の導入検討
- zoom レベルに応じてクラスタリング

### 5. URL パラメータ対応

都道府県・区の選択状態を URL クエリパラメータで管理：

```
/map?prefecture=大阪府&area=北区
```

Angular Router の `queryParams` を使い、リロード・共有URLで状態を復元。

### 6. ナビゲーション改善

ヘッダーに「都道府県クイックリンク」または都道府県トップページを追加：

```
/map?prefecture=東京都
/map?prefecture=大阪府
...
```

## 完了条件

- [ ] 都道府県セレクタが表示され、選択すると API を叩き直す
- [ ] 地図が日本全体を初期表示する（zoom 6）
- [ ] 都道府県選択時に地図が対象地域にズームする
- [ ] URL パラメータで状態が保持される
- [ ] モバイルで都道府県セレクタが使いやすい（フルスクリーン表示等）

## 依存

- EXPAND-002（バックエンドの `prefecture` フィルタ API）完了後に着手
- EXPAND-001 と並行可能（東京のみのデータでも動作確認できる）
