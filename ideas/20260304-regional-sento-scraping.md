# 地方銭湯組合サイト スクレイピング調査

調査日: 2026-03-04

---

## 1. 大阪: osaka268.com

### 概要

- 運営: 大阪府公衆浴場組合（大阪府公衆浴場業生活衛生同業組合）
- CMS: WordPress（`/wp/wp-content/uploads/` パスが確認済み）
- 総銭湯数: 71軒（2024/11/29時点）

### 銭湯一覧ページ

- URL: `https://osaka268.com/search/`
- 取得方法: 検索フォームから地域・区で絞り込み可能（フォームベース）
- ページネーション: 不明（71軒程度なので単一ページの可能性が高い）

### 個別ページURL

- パターン不明（WordPress の slug ベースと推測される）
- 参考PDF: `https://osaka268.com/wp/wp-content/uploads/2024/11/72c049141463986fe7cfc80ab7482739-2.pdf`
  - PDF には「支部名・浴場名・所在地・電話」が記載されており、スクレイピングの代替手段として使用可能

### 取得可能フィールド

| フィールド | 取得可否 | 備考 |
|-----------|---------|------|
| 名前 | ○ | |
| 住所 | ○ | |
| 電話番号 | ○ | |
| 営業時間 | 不明 | サイト上での確認未完 |
| 定休日 | 不明 | サイト上での確認未完 |
| 緯度経度 | 不明 | Google Maps iframe の有無不明 |

### HTML構造（推定）

- WordPress 標準テーマまたはカスタムテーマ
- `/wp/` サブディレクトリ構成
- 地図機能の実装方式不明（Google Maps API 埋め込みか iframe か）

### robots.txt

- WebFetch が拒否されたため直接確認不可
- `/wp/` ディレクトリが公開されており、`/search/` も検索エンジンにインデックスされているため、Disallow の可能性は低い

### 代替アプローチ

PDF (`/wp/wp-content/uploads/` 以下) に銭湯リスト（名前・住所・電話）が公開されている。
スクレイピングより PDF パースの方が安定する可能性が高い。

```python
# PDF から情報を抽出する場合
import pdfplumber
# URL: https://osaka268.com/wp/wp-content/uploads/2024/11/72c049141463986fe7cfc80ab7482739-2.pdf
```

---

## 2. 京都: 1010.kyoto

### 概要

- 運営: 京都府浴場組合
- CMS: WordPress（カスタム投稿タイプ `spot` を使用）
- 総銭湯数: 100軒以上（公称）、一覧ページに84件確認

### 銭湯一覧ページ

- URL: `https://1010.kyoto/spot/`
- カテゴリ別: `https://1010.kyoto/spot-cat/kyoto/`（京都市）
- タグ別: `https://1010.kyoto/spot-tag/morning_open/`（午前営業など）
- ページネーション: あり（`/page/2/`、`/page/8/` まで確認）

```
# ページネーション URL パターン
https://1010.kyoto/spot/page/2/
https://1010.kyoto/spot-cat/kyoto/page/2/
https://1010.kyoto/spot-cat/kyoto/page/8/
```

### 個別ページURL

- パターン: `https://1010.kyoto/spot/[slug]/`
- 例:
  - `https://1010.kyoto/spot/aketayu/` （明田湯）
  - `https://1010.kyoto/spot/taishouyu2/` （大正湯）
  - `https://1010.kyoto/spot/funaokaonsen/` （船岡温泉）
  - `https://1010.kyoto/spot/daikokuyu/` （大黒湯）

### 取得可能フィールド

| フィールド | 取得可否 | 備考 |
|-----------|---------|------|
| 名前 | ○ | ページタイトル |
| 住所 | ○ | 例: 京都府京都市南区東九条明田町10 |
| 電話番号 | ○ | 例: 075-691-6298 |
| 営業時間 | ○ | 例: 15:00〜24:00 |
| 定休日 | ○ | 例: 金曜日 |
| 設備 | ○ | 主浴槽・ジェット・電気・水風呂・薬湯・サウナ等 |
| 駐車場 | ○ | |
| 緯度経度 | 要確認 | Google Maps リンクの有無は未確認 |

### HTML構造（推定）

WordPress カスタム投稿タイプ `spot` ベース。
各詳細ページは構造化されたカスタムフィールドで情報を管理していると推定。

```python
# BeautifulSoup での抽出例（推定）
# 一覧ページのリンク取得
links = soup.select('article.spot a[href*="/spot/"]')

# 詳細ページの情報抽出
name = soup.select_one('h1.entry-title').text.strip()
# 各フィールドはラベル付きのdl/dt/dd か table で構成されると推定
```

### スクレイピング手順

1. `https://1010.kyoto/spot/` からページ数を取得
2. 各ページを巡回して個別ページの URL を収集
3. 各個別ページを fetch して情報を抽出

### robots.txt

- 直接確認不可（WebFetch 拒否）
- サイト全体が検索エンジンにインデックスされており、スクレイピングの障壁は低いと推定

---

## 3. 愛知: aichi1010.jp

### 概要

- 運営: 愛知県公衆浴場業生活衛生同業組合
- CMS: 独自システム（WordPress ではない可能性が高い）
- 銭湯数: 不明（IDが76以上確認）

### 銭湯一覧ページ

- URL: `https://aichi1010.jp/page/list/`
- 別 URL: `https://aichi1010.jp/page/list/l`
- 地図と一覧を組み合わせた表示（Google Maps API 使用で1日あたり表示回数制限あり）
- ページネーション: 一覧に存在するか不明（地図ベースの可能性）

### 個別ページURL

- パターン: `https://aichi1010.jp/page/detail/[地区コード]/[ID]`
- 地区コード:
  - `l` = 名古屋市内（確認済み）
  - `1` = 他地区（例: 小田井温泉は `detail/1/17`）
- 例:
  - `https://aichi1010.jp/page/detail/l/1` （娯楽湯）
  - `https://aichi1010.jp/page/detail/l/8` （大幸温泉）
  - `https://aichi1010.jp/page/detail/l/22` （大黒湯）
  - `https://aichi1010.jp/page/detail/l/34` （永楽湯）
  - `https://aichi1010.jp/page/detail/l/44` （玉の湯）
  - `https://aichi1010.jp/page/detail/l/63` （鳴海温泉）
  - `https://aichi1010.jp/page/detail/l/76` （龍美湯）
  - `https://aichi1010.jp/page/detail/1/17` （小田井温泉）

### 取得可能フィールド

| フィールド | 取得可否 | 備考 |
|-----------|---------|------|
| 名前 | ○ | |
| 区 | ○ | 例: 千種区 |
| 住所 | ○ | 例: 〒464-0848 愛知県名古屋市千種区春岡2-24-20 |
| 電話番号 | ○ | 例: 052-762-7051 |
| 営業時間 | ○ | 例: 16:00〜24:00 |
| 定休日 | ○ | 例: 木曜日 |
| 入浴料金 | ○ | |
| 駐車場 | ○ | 台数まで記載あり |
| アクセス | ○ | 電車・バス・車 |
| 緯度経度 | 要確認 | Google Maps リンクの有無は未確認 |

### HTML構造（推定）

独自CMSベースの構造。ID ベースの URL パターンから、データベース直結の動的ページと推定。

```python
# ID を連番でブルートフォース的にアクセスする戦略
# ただし欠番があるため、404 を graceful に処理する必要あり
for sento_id in range(1, 200):  # 最大IDは調査必要
    url = f"https://aichi1010.jp/page/detail/l/{sento_id}"
    # 404 なら skip

# 地区コードも 'l' 以外に '1', '2' 等が存在する可能性あり
# page/list ページから全リンクを収集する方が安全
```

### スクレイピング手順

1. `https://aichi1010.jp/page/list/` から全銭湯の個別ページURLを収集
2. 各 URL を fetch して情報を抽出
3. 地図データ（JSON）がページ内に埋め込まれている場合は緯度経度を直接取得可能

### robots.txt

- 直接確認不可
- `page/list` や `page/detail` がインデックスされているため Disallow は限定的と推定

---

## 4. 福岡: fukuoka1010.com

### 概要

- 運営: 福岡県公衆浴場生活衛生同業組合
- サイト名: 福岡よか風呂ガイド
- CMS: WordPress（推定）
- 対象地域: 福岡市・北九州市・筑後地区等

### 銭湯一覧ページ

地域別に分かれた複数の一覧ページが存在：

| 地域 | URL |
|------|-----|
| 福岡市内 | `https://fukuoka1010.com/list-fukuoka/` |
| 北九州 | `https://fukuoka1010.com/list-kitakyu/` |
| （筑後？） | 不明（`/chikugo/` 配下に個別ページあり） |

- 取得方法: 区別のリスト形式（ページネーションなしの静的一覧と推定）
- 福岡市内の区: 東区・博多区・中央区・城南区・早良区・西区
- 北九州の区: 若松区・戸畑区・八幡東区・小倉北区・小倉南区・門司区

### 個別ページURL

- パターン: `https://fukuoka1010.com/[地域コード]/[slug]/`
- 地域コード:
  - `fukuoka` = 福岡市内
  - `kitakyu` = 北九州市
  - `chikugo` = 筑後地区
- 例:
  - `https://fukuoka1010.com/fukuoka/daitokuyu/` （大徳湯【博多区】）
  - `https://fukuoka1010.com/fukuoka/honjyouyu/` （本庄湯【中央区】）
  - `https://fukuoka1010.com/fukuoka/asoyu/` （阿蘇の湯【東区】）
  - `https://fukuoka1010.com/kitakyu/daikokuyu-kokurakita/` （大黒湯【小倉北区】）
  - `https://fukuoka1010.com/kitakyu/tsurunoyu-wakamatsu/` （鶴の湯【若松区】）
  - `https://fukuoka1010.com/chikugo/daichanyu/` （だぃちゃん湯【大牟田】）

### 取得可能フィールド

| フィールド | 取得可否 | 備考 |
|-----------|---------|------|
| 名前 | ○ | ページタイトルに「【区名】」付き |
| 区 | ○ | タイトルから抽出可能 |
| 住所 | ○ | |
| 電話番号 | 要確認 | |
| 営業時間 | ○ | |
| 定休日 | 要確認 | |
| 緯度経度 | 要確認 | Google Maps リンクの有無は未確認 |

### HTML構造（推定）

WordPress ベースで、個別ページは投稿またはカスタム投稿タイプ。

```python
# BeautifulSoup での抽出例（推定）
# タイトルから区名を抽出
import re
title = soup.select_one('h1').text  # 例: "大徳湯【博多区】"
name = re.sub(r'【.*?】', '', title).strip()  # 大徳湯
ward = re.search(r'【(.+?)】', title).group(1)  # 博多区
```

### スクレイピング手順

1. 一覧ページ（`/list-fukuoka/`, `/list-kitakyu/` 等）から全個別URLを収集
2. 各 URL を fetch して情報を抽出

### robots.txt

- 直接確認不可
- WordPress ベースの公開サイトで全ページがインデックスされており、制限は少ないと推定

---

## まとめ比較表

| 項目 | 大阪 | 京都 | 愛知 | 福岡 |
|------|------|------|------|------|
| 銭湯数 | 71軒 | 100軒以上 | 不明（76以上） | 不明 |
| CMS | WordPress | WordPress | 独自システム | WordPress（推定） |
| 一覧URL | `/search/` | `/spot/` | `/page/list/` | `/list-fukuoka/` 等 |
| ページネーション | 不明 | あり（`/page/N/`） | 不明 | なし（推定） |
| 個別URL | 不明 | `/spot/[slug]/` | `/page/detail/[code]/[id]` | `/[region]/[slug]/` |
| 名前 | ○ | ○ | ○ | ○ |
| 住所 | ○ | ○ | ○ | ○ |
| 電話番号 | ○ | ○ | ○ | 要確認 |
| 営業時間 | 不明 | ○ | ○ | ○ |
| 定休日 | 不明 | ○ | ○ | 要確認 |
| 緯度経度 | 不明 | 要確認 | 要確認 | 要確認 |
| 難易度 | 高（要JS確認） | 低（WordPress標準） | 中（ID連番） | 低（WordPress標準） |

---

## 実装優先度・推奨アプローチ

### 推奨順位

1. **京都** (1010.kyoto) - WordPress 標準構成、slug ベースURL、ページネーション明確
2. **福岡** (fukuoka1010.com) - WordPress 推定、地域別一覧ページが明確
3. **愛知** (aichi1010.jp) - 独自システムだが ID パターンが判明
4. **大阪** (osaka268.com) - PDF 活用が有力、HTML 一覧の構造が不明

### 大阪の代替案

銭湯リストの PDF (`/wp/wp-content/uploads/` 配下) を定期ダウンロードして `pdfplumber` でパースする。
HTML スクレイピングより安定性が高い。

### 緯度経度の取得戦略

全サイト共通で Google Maps リンク (`maps.google.com/maps?daddr=` や `maps.app.goo.gl/`) の
destination パラメータから抽出できる可能性がある。
確認できない場合は Google Geocoding API で住所から変換する（コスト発生）。

```python
import re

# Google Maps ナビリンクから緯度経度を抽出（東京1010と同様のパターン）
GMAPS_PATTERN = re.compile(
    r'(?:daddr|destination|ll|@)=(-?\d+\.\d+)[,+](-?\d+\.\d+)'
)

def extract_latlng(url: str) -> tuple[float, float] | None:
    m = GMAPS_PATTERN.search(url)
    if m:
        return float(m.group(1)), float(m.group(2))
    return None
```

---

## 次のアクション

1. 各サイトの `robots.txt` を実際に fetch して確認（WebFetch 権限が必要）
2. 各サイトの実際の HTML を取得して CSS セレクタを確定
3. 京都・福岡から実装開始（構造が明確なため）
4. 大阪は PDF パースの実現性を検証
5. 愛知は `page/list/` から全URLを収集する方法を検証
