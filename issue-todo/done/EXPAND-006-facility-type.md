# EXPAND-006: facility_type カラム追加

## 概要
温泉・スーパー銭湯を普通銭湯と区別するための `facility_type` カラムを追加する。

## 背景
全国展開にあたり、銭湯だけでなく温泉・スーパー銭湯も取得対象となる。
フロントエンドでフィルタリングや表示切り替えを行うためにカラムが必要。

## 変更内容

### バックエンド
- `back/app/models/sento.py`: `facility_type: Mapped[Optional[str]]` 追加
- `back/app/schemas/sento.py`: `facility_type: Optional[str] = None` 追加
- `back/alembic/versions/{hash}_add_facility_type.py`: マイグレーション作成

### フロントエンド
- `front/src/app/models/sento.ts`: `facilityType?: string` 追加

## facility_type の値
- `'sento'`: 普通公衆浴場（銭湯）
- `'onsen'`: 温泉銭湯
- `'super_sento'`: スーパー銭湯
- `NULL`: 不明（デフォルト、後方互換）

## ブランチ
`feature/expand-006-facility-type`

## ステータス
- [ ] 実装
- [ ] テスト
- [ ] PR
