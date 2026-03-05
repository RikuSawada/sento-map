"""OsakaParser のユニットテスト。"""
import json
import textwrap

import pytest

from parsers.osaka import OsakaParser
from parsers.base import BaseParser
from bs4 import BeautifulSoup


@pytest.fixture
def parser() -> OsakaParser:
    return OsakaParser()


# ---------------------------------------------------------------------------
# parse_sento: ハッピーパス
# ---------------------------------------------------------------------------

OSAKA_DETAIL_HTML_HAPPY = """
<html>
<head><title>松の湯 | 大阪268銭湯</title></head>
<body>
  <h1 class="sento-name">松の湯</h1>
  <div class="sento-address">大阪府大阪市中央区1-2-3</div>
  <a href="tel:06-1234-5678">06-1234-5678</a>
  <dl>
    <dt>営業時間</dt><dd>15:00〜23:00</dd>
    <dt>定休日</dt><dd>月曜日</dd>
  </dl>
  <a href="https://www.google.com/maps?destination=34.6937,135.5023">地図</a>
</body>
</html>
"""


def test_parse_sento_happy_path(parser: OsakaParser) -> None:
    result = parser.parse_sento(OSAKA_DETAIL_HTML_HAPPY, "https://osaka268.com/sento/matsu/")

    assert result is not None
    assert result["name"] == "松の湯"
    assert result["address"] == "大阪府大阪市中央区1-2-3"
    assert result["phone"] == "06-1234-5678"
    assert result["open_hours"] == "15:00〜23:00"
    assert result["holiday"] == "月曜日"
    assert result["lat"] == pytest.approx(34.6937)
    assert result["lng"] == pytest.approx(135.5023)
    assert result["prefecture"] == "大阪府"
    assert result["region"] == "関西"
    assert result["facility_type"] == "sento"
    assert result["source_url"] == "https://osaka268.com/sento/matsu/"


# ---------------------------------------------------------------------------
# parse_sento: name が取得できない場合 None を返す
# ---------------------------------------------------------------------------

OSAKA_DETAIL_HTML_NO_NAME = """
<html>
<body>
  <p>銭湯情報が見つかりません</p>
</body>
</html>
"""


def test_parse_sento_returns_none_when_name_missing(parser: OsakaParser) -> None:
    result = parser.parse_sento(OSAKA_DETAIL_HTML_NO_NAME, "https://osaka268.com/sento/unknown/")
    assert result is None


# ---------------------------------------------------------------------------
# parse_sento: キャッシュから座標を取得する
# ---------------------------------------------------------------------------

OSAKA_DETAIL_HTML_NO_MAPS = """
<html>
<body>
  <h1 class="sento-name">竹の湯</h1>
  <address>大阪府堺市1-1-1</address>
</body>
</html>
"""


def test_parse_sento_uses_coord_cache(parser: OsakaParser) -> None:
    url = "https://osaka268.com/sento/take/"
    parser._coord_cache[url] = (34.5700, 135.4800)

    result = parser.parse_sento(OSAKA_DETAIL_HTML_NO_MAPS, url)

    assert result is not None
    assert result["lat"] == pytest.approx(34.5700)
    assert result["lng"] == pytest.approx(135.4800)


# ---------------------------------------------------------------------------
# get_item_urls: childaMarkers JSON から URL を抽出しキャッシュを構築する
# ---------------------------------------------------------------------------

def _make_search_html(markers: list[dict]) -> str:
    markers_json = json.dumps(markers)
    return f"""
<html>
<body>
<script>
var childaMarkers = {markers_json};
</script>
</body>
</html>
"""


def test_get_item_urls_extracts_from_child_markers(parser: OsakaParser) -> None:
    markers = [
        {"url": "/sento/a/", "lat": 34.69, "lng": 135.50},
        {"url": "/sento/b/", "lat": 34.70, "lng": 135.51},
    ]
    html = _make_search_html(markers)
    urls = parser.get_item_urls(html, "https://osaka268.com/search/")

    assert urls == [
        "https://osaka268.com/sento/a/",
        "https://osaka268.com/sento/b/",
    ]
    assert parser._coord_cache["https://osaka268.com/sento/a/"] == pytest.approx((34.69, 135.50))
    assert parser._coord_cache["https://osaka268.com/sento/b/"] == pytest.approx((34.70, 135.51))


def test_get_item_urls_deduplicates(parser: OsakaParser) -> None:
    markers = [
        {"url": "/sento/a/", "lat": 34.69, "lng": 135.50},
        {"url": "/sento/a/", "lat": 34.69, "lng": 135.50},  # 重複
    ]
    html = _make_search_html(markers)
    urls = parser.get_item_urls(html, "https://osaka268.com/search/")
    assert len(urls) == 1


# ---------------------------------------------------------------------------
# _extract_label_value ヘルパー
# ---------------------------------------------------------------------------

def test_extract_label_value_dt_dd() -> None:
    soup = BeautifulSoup("<dl><dt>住所</dt><dd>大阪市</dd></dl>", "lxml")
    assert BaseParser.extract_label_value(soup, "住所") == "大阪市"


def test_extract_label_value_returns_none_when_missing() -> None:
    soup = BeautifulSoup("<dl><dt>電話</dt><dd>06-0000</dd></dl>", "lxml")
    assert BaseParser.extract_label_value(soup, "住所") is None
