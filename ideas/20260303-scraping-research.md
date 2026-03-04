# スクレイピング調査結果 (1010.or.jp)
調査日: 2026-03-03

## robots.txt 確認結果

URL: https://www.1010.or.jp/robots.txt

```
User-agent: *
Disallow: /wp/wp-admin/
Allow: /wp/wp-admin/admin-ajax.php

Sitemap: https://www.1010.or.jp/wp-sitemap.xml
```

**判定:** `/map/` および `/map/item/item-cnt-*` へのアクセスは一切禁止されていない。
クローラー制限は WordPress 管理画面のみ。スクレイピング対象パスは全て許可範囲内。

---

## 利用規約確認結果

専用の利用規約ページ（/kiyaku/、/privacy/）は 404 で存在しない。

トップページフッターに以下の記載のみ確認:

> 「ホームページ内の写真、記事の流用を禁止します」
> Copyright © Tokyo Sento Association All Rights Reserved. 2015

**解釈:**
- 禁止されているのは「写真」と「記事」の流用（二次転載・再配布）
- 銭湯の名称・住所・電話番号・営業時間等のファクト情報は著作権保護の対象外（著作権法上、事実の列挙に著作物性なし）
- スクレイピング自体を禁止する記述は存在しない
- 自動収集禁止の ToS 記載なし

---

## 地図ページ HTML 構造

URL: https://www.1010.or.jp/map/

**サイト構成:** WordPress ベース（Gutenberg ブロックエディタ使用）

**銭湯一覧:**
- 総件数: 410 件（ページ内に「410件ヒットしました」と表示）
- 各銭湯エントリの URL パターン: `https://www.1010.or.jp/map/item/item-cnt-{数字}`
- ID 範囲: 非連番。確認済み最大値は item-cnt-704 だが、実在するのは 410 件

**一覧ページの HTML 構造:**
```html
<a href="https://www.1010.or.jp/map/item/item-cnt-XXX">
  <img src="..." class="thumb">
  [銭湯名]
</a>
<a href="https://www.1010.or.jp/map/archives/area/[ward]">[区名]</a>
```

**個別銭湯ページの構造（item-cnt-151: さくら湯、item-cnt-412: 水神湯 で確認）:**

```html
<!-- 住所: 郵便番号と番地が段落テキストとして存在（特定 class なし） -->
〒130-0002
墨田区業平４−６−５

<!-- 電話番号: tel: リンク -->
<a href="tel:03-3623-6917">03-3623-6917</a>

<!-- 営業時間・定休日: strong タグ見出し + テキスト -->
<strong>休日</strong>
月曜（祝日の場合は翌日休）

<strong>営業時間</strong>
１５：００−２４：００

<!-- Google Maps ナビリンク（緯度経度が埋め込まれている） -->
<a href="https://www.google.com/maps/dir/?api=1&destination=35.7074107,139.814937399999">
  Googleマップで見る
</a>
```

**使用 JavaScript:** jQuery、FancyBox（画像ライトボックス）、Google Tag Manager、Google Analytics

---

## 取得可能データ項目

| データ項目 | 取得可否 | 取得元 |
|-----------|---------|-------|
| 銭湯名 | ○ | 個別ページ h1 タイトル |
| 読み仮名 | ○ | 個別ページ本文（銭湯名直下テキスト） |
| 住所（郵便番号） | ○ | 個別ページ本文テキスト（正規表現で抽出） |
| 住所（番地） | ○ | 個別ページ本文テキスト |
| 区名 | ○ | 一覧ページのエリアリンクテキスト |
| 電話番号 | ○ | `<a href="tel:...">` の href 属性 |
| 営業時間 | ○ | `<strong>営業時間</strong>` 以降のテキスト |
| 定休日 | ○ | `<strong>休日</strong>` 以降のテキスト |
| 緯度 | ○ | Google Maps リンクの destination パラメータ |
| 経度 | ○ | Google Maps リンクの destination パラメータ |
| 公式 URL | △ | 個別ページ内の外部リンク（存在する場合） |
| 写真 | ✕ | 著作権禁止のため取得しない |

---

## 緯度経度の取得方法

各個別ページにある Google Maps ナビリンクの URL パラメータから正規表現で抽出する。
HTML スクレイピングのみで取得可能。ジオコーディング API は不要。

**対象 URL 形式:**
```
https://www.google.com/maps/dir/?api=1&destination={latitude},{longitude}
```

**実測値:**
```
さくら湯（item-cnt-151）: destination=35.7074107,139.814937399999
水神湯（item-cnt-412）:   destination=35.591961858107005,139.7341013511001
```

**Python 抽出コード:**
```python
import re
from bs4 import BeautifulSoup

def extract_coordinates(soup: BeautifulSoup) -> tuple[float, float] | None:
    maps_link = soup.find("a", href=re.compile(r"maps\.google\.com/maps/dir/\?api=1&destination="))
    if not maps_link:
        return None
    match = re.search(r"destination=([-\d.]+),([-\d.]+)", maps_link["href"])
    if match:
        return float(match.group(1)), float(match.group(2))
    return None
```

---

## WordPress REST API の調査結果

`https://www.1010.or.jp/wp-json/wp/v2/` は公開されているが、銭湯データは標準 posts として格納されており、
住所・座標・営業時間はカスタムフィールド（meta）として REST API に公開されていない（`"meta": []`）。
カスタム投稿タイプも存在しない（標準 post/page/attachment 等のみ）。

**結論:** REST API 経由での構造化データ取得は不可。HTML スクレイピングが唯一の手段。

---

## 判断: GO

**理由:**
1. robots.txt で `/map/` パスの収集は禁止されていない
2. 利用規約にスクレイピング・自動収集禁止の記載なし
3. 住所・電話番号・営業時間等のファクト情報は著作権保護の対象外
4. 全データを HTML から静的に取得可能（JavaScript 実行不要）
5. 緯度経度は Google Maps ナビリンクから直接取得可能（ジオコーディング API 不要）

**遵守事項:**
- リクエスト間隔: 最低 2 秒（CLAUDE.md 規約の 1 秒より安全側に設定）
- 写真・記事コンテンツは取得しない（利用規約の禁止事項）
- User-Agent を明示的に設定し、bot であることを隠さない
- スクレイピング先の負荷を最小化する設計

---

## BATCH-002 実装方針

### スクレイピング戦略

**2 段階取得:**
1. 一覧ページ（`/map/`）から全 `item-cnt-XXX` の URL リストを取得（410 件）
2. 各個別ページから詳細情報を取得（リクエスト間隔 2 秒以上）

### パーシング仕様

| データ | 取得方法 |
|-------|---------|
| 銭湯名 | ページタイトル or h1 タグ |
| 読み仮名 | 銭湯名直下のテキスト（ひらがな） |
| 郵便番号 | 正規表現 `〒(\d{3}-\d{4})` |
| 住所 | 郵便番号直後のテキストブロック |
| 区名 | 一覧ページの area リンクテキスト |
| 電話番号 | `a[href^="tel:"]` の href 属性値 |
| 営業時間 | `<strong>営業時間</strong>` の next sibling テキスト |
| 定休日 | `<strong>休日</strong>` の next sibling テキスト |
| 緯度経度 | `a[href*="maps.google.com/maps/dir"]` の destination パラメータ |
| 公式 URL | 個別ページ内の 1010.or.jp 以外の外部リンク |

### DB への書き込み方針

- `sento_id`（= item-cnt の数字部分）を自然キーとして使用
- 既存レコードとの差分比較で変更があった場合のみ UPDATE
- 新規の場合は INSERT
- 廃業（ページが 404）の場合は `is_active = False` に更新（物理削除しない）

### エラーハンドリング

```
HTTP 404   → 廃業扱いで is_active = False に更新、次の処理へ
HTTP 429/503 → エラーログ出力して次の処理へ（リトライなし）
パーシング失敗 → エラーログ出力して次の処理へ（部分データでも INSERT しない）
接続タイムアウト → エラーログ出力して次の処理へ
```

### 使用ライブラリ

```toml
# batch/pyproject.toml に追加
httpx = ">=0.27"          # HTTP クライアント（同期モードで使用）
beautifulsoup4 = ">=4.12" # HTML パーシング
lxml = ">=5.0"            # BS4 パーサー（高速）
sqlalchemy = ">=2.0"      # DB 接続（back と共通スキーマ使用）
psycopg2-binary = ">=2.9" # PostgreSQL ドライバ
```

### ファイル構成

```
batch/
├── scraper.py      # メインエントリポイント（一覧取得 → 個別取得のオーケストレーション）
├── fetcher.py      # HTTP 取得（httpx、リクエスト間隔制御）
├── parser.py       # HTML パーシング（BeautifulSoup、各フィールド抽出）
├── db.py           # DB 接続・upsert 処理
└── pyproject.toml
```

### スケジューリング

- 週 1 回（毎週月曜 3:00 JST）を想定
- 実行コマンド: `docker compose --profile batch run --rm batch uv run python scraper.py`
- GitHub Actions のスケジュールトリガーで実行予定
