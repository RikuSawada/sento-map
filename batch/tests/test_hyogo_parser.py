"""HyogoParser のユニットテスト。"""
import json

import pytest

from parsers.hyogo import HyogoParser


@pytest.fixture
def parser() -> HyogoParser:
    return HyogoParser()


# ---------------------------------------------------------------------------
# get_list_urls
# ---------------------------------------------------------------------------

def test_get_list_urls(parser: HyogoParser) -> None:
    urls = parser.get_list_urls()
    assert len(urls) == 1
    assert "hyogo1010.com/sento_list/" in urls[0]


# ---------------------------------------------------------------------------
# _cache_from_json: lat/lng スワップ補正
# ---------------------------------------------------------------------------

def test_cache_from_json_swaps_lat_lng(parser: HyogoParser) -> None:
    """JSON の "lat" が経度、"lng" が緯度なので、スワップして格納されること。"""
    url = "https://hyogo1010.com/sento_list/kobe-matsuno-yu/"
    # サイトの JSON: lat=経度(135.19), lng=緯度(34.69)
    data = {"lat": "135.19", "lng": "34.69", "name": "松の湯", "url": url}
    parser._cache_from_json(url, data)

    assert url in parser._coord_cache
    actual_lat, actual_lng = parser._coord_cache[url]
    assert actual_lat == pytest.approx(34.69)   # JSON の "lng" が実際の lat
    assert actual_lng == pytest.approx(135.19)  # JSON の "lat" が実際の lng


def test_cache_from_json_skips_when_lat_missing(parser: HyogoParser) -> None:
    """lat キーがない場合は座標キャッシュに追加しない。"""
    url = "https://hyogo1010.com/sento_list/kobe-test/"
    data = {"lng": "34.69", "name": "テスト湯"}
    parser._cache_from_json(url, data)
    assert url not in parser._coord_cache


def test_cache_from_json_skips_when_lng_missing(parser: HyogoParser) -> None:
    """lng キーがない場合は座標キャッシュに追加しない。"""
    url = "https://hyogo1010.com/sento_list/kobe-test2/"
    data = {"lat": "135.19", "name": "テスト湯2"}
    parser._cache_from_json(url, data)
    assert url not in parser._coord_cache


def test_cache_from_json_stores_data_cache(parser: HyogoParser) -> None:
    """データキャッシュには常に格納すること。"""
    url = "https://hyogo1010.com/sento_list/kobe-test3/"
    data = {"name": "テスト湯3", "address": "兵庫県神戸市1-1"}
    parser._cache_from_json(url, data)
    assert parser._data_cache[url] == data


# ---------------------------------------------------------------------------
# get_item_urls: data 属性から抽出
# ---------------------------------------------------------------------------

HYOGO_LIST_HTML_DATA_ATTR = """
<html>
<body>
  <div data-sento='{"lat": "135.19", "lng": "34.69", "name": "松の湯", "url": "/sento_list/kobe-matsu-yu/"}'></div>
  <div data-sento='{"lat": "135.20", "lng": "34.70", "name": "梅の湯", "url": "/sento_list/kobe-ume-yu/"}'></div>
</body>
</html>
"""


def test_get_item_urls_from_data_attrs(parser: HyogoParser) -> None:
    urls = parser.get_item_urls(HYOGO_LIST_HTML_DATA_ATTR, "https://hyogo1010.com/sento_list/")
    assert len(urls) == 2
    assert "https://hyogo1010.com/sento_list/kobe-matsu-yu/" in urls
    assert "https://hyogo1010.com/sento_list/kobe-ume-yu/" in urls
    # 座標もキャッシュされること（スワップ補正済み）
    lat, lng = parser._coord_cache["https://hyogo1010.com/sento_list/kobe-matsu-yu/"]
    assert lat == pytest.approx(34.69)
    assert lng == pytest.approx(135.19)


# ---------------------------------------------------------------------------
# get_item_urls: フォールバック（a タグ）
# ---------------------------------------------------------------------------

HYOGO_LIST_HTML_FALLBACK = """
<html>
<body>
  <a href="/sento_list/kobe-sakura-yu/">さくら湯</a>
  <a href="/sento_list/nishinomiya-take-yu/">竹の湯</a>
  <a href="/">トップ</a>
</body>
</html>
"""


def test_get_item_urls_fallback_from_a_tags(parser: HyogoParser) -> None:
    urls = parser.get_item_urls(HYOGO_LIST_HTML_FALLBACK, "https://hyogo1010.com/sento_list/")
    assert "https://hyogo1010.com/sento_list/kobe-sakura-yu/" in urls
    assert "https://hyogo1010.com/sento_list/nishinomiya-take-yu/" in urls


# ---------------------------------------------------------------------------
# parse_sento: ハッピーパス（座標はキャッシュから取得）
# ---------------------------------------------------------------------------

HYOGO_DETAIL_HTML_HAPPY = """
<html>
<body>
  <h1 class="sento-name">松の湯</h1>
  <dl>
    <dt>住所</dt><dd>兵庫県神戸市中央区1-2-3</dd>
    <dt>TEL</dt><dd>078-111-2222</dd>
    <dt>営業時間</dt><dd>15:00〜23:00</dd>
    <dt>定休日</dt><dd>月曜日</dd>
  </dl>
</body>
</html>
"""


def test_parse_sento_uses_coord_cache(parser: HyogoParser) -> None:
    url = "https://hyogo1010.com/sento_list/kobe-matsu-yu/"
    parser._coord_cache[url] = (34.69, 135.19)
    parser._data_cache[url] = {}

    result = parser.parse_sento(HYOGO_DETAIL_HTML_HAPPY, url)

    assert result is not None
    assert result["name"] == "松の湯"
    assert result["address"] == "兵庫県神戸市中央区1-2-3"
    assert result["phone"] == "078-111-2222"
    assert result["open_hours"] == "15:00〜23:00"
    assert result["holiday"] == "月曜日"
    assert result["lat"] == pytest.approx(34.69)
    assert result["lng"] == pytest.approx(135.19)
    assert result["prefecture"] == "兵庫県"
    assert result["region"] == "関西"
    assert result["facility_type"] == "sento"
    assert result["source_url"] == url


# ---------------------------------------------------------------------------
# parse_sento: name が取得できない場合 None を返す
# ---------------------------------------------------------------------------

HYOGO_DETAIL_HTML_NO_NAME = """
<html>
<body>
  <p>情報なし</p>
</body>
</html>
"""


def test_parse_sento_returns_none_when_name_missing(parser: HyogoParser) -> None:
    result = parser.parse_sento(HYOGO_DETAIL_HTML_NO_NAME, "https://hyogo1010.com/sento_list/unknown-yu/")
    assert result is None


# ---------------------------------------------------------------------------
# parse_sento: data_cache の name にフォールバックする
# ---------------------------------------------------------------------------

HYOGO_DETAIL_HTML_NO_H1 = """
<html>
<body>
  <dl>
    <dt>住所</dt><dd>兵庫県姫路市1-1-1</dd>
  </dl>
</body>
</html>
"""


def test_parse_sento_falls_back_to_cached_name(parser: HyogoParser) -> None:
    url = "https://hyogo1010.com/sento_list/himeji-take-yu/"
    parser._data_cache[url] = {"name": "竹の湯", "address": "兵庫県姫路市1-1-1"}

    result = parser.parse_sento(HYOGO_DETAIL_HTML_NO_H1, url)

    assert result is not None
    assert result["name"] == "竹の湯"


# ---------------------------------------------------------------------------
# parse_sento: 座標がキャッシュになければ Google Maps リンクから取得
# ---------------------------------------------------------------------------

HYOGO_DETAIL_HTML_GMAPS = """
<html>
<body>
  <h1>桜の湯</h1>
  <dl>
    <dt>住所</dt><dd>兵庫県西宮市2-3-4</dd>
  </dl>
  <a href="https://www.google.com/maps?q=34.7300,135.3400">地図</a>
</body>
</html>
"""


def test_parse_sento_extracts_coords_from_gmaps_link(parser: HyogoParser) -> None:
    url = "https://hyogo1010.com/sento_list/nishinomiya-sakura-yu/"
    result = parser.parse_sento(HYOGO_DETAIL_HTML_GMAPS, url)

    assert result is not None
    assert result["lat"] == pytest.approx(34.7300)
    assert result["lng"] == pytest.approx(135.3400)
