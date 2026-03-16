"""FukushimaParser のユニットテスト。"""
import pytest

from parsers import PARSERS
from parsers.fukushima import FukushimaParser


@pytest.fixture
def parser() -> FukushimaParser:
    return FukushimaParser()


def test_get_list_urls(parser: FukushimaParser) -> None:
    urls = parser.get_list_urls()
    assert urls == ["https://fukushima1010.com/"]


FUKUSHIMA_LIST_HTML = """
<html>
<body>
  <a class="entry-card" href="https://fukushima1010.com/sento/azuma-yu/">あづま湯</a>
  <a href="/shop/koriyama-no-yu/">郡山の湯</a>
  <a href="/sento/azuma-yu/#access">同一リンク（重複）</a>
  <a href="https://fukushima1010.com/category/news/">お知らせ（除外）</a>
  <a href="https://example.com/sento/x/">外部サイト（除外）</a>
</body>
</html>
"""


def test_get_item_urls_collects_detail_links(parser: FukushimaParser) -> None:
    urls = parser.get_item_urls(FUKUSHIMA_LIST_HTML, "https://fukushima1010.com/")

    assert "https://fukushima1010.com/sento/azuma-yu/" in urls
    assert "https://fukushima1010.com/shop/koriyama-no-yu/" in urls
    assert "https://fukushima1010.com/category/news/" not in urls
    assert all("example.com" not in u for u in urls)
    assert urls.count("https://fukushima1010.com/sento/azuma-yu/") == 1


FUKUSHIMA_DETAIL_HTML_HAPPY = """
<html>
<body>
  <h1 class="entry-title">吾妻湯</h1>
  <dl>
    <dt>住所</dt><dd>福島県福島市本町1-2-3</dd>
    <dt>TEL</dt><dd>024-111-2222</dd>
    <dt>営業時間</dt><dd>14:00〜22:30</dd>
    <dt>定休日</dt><dd>木曜日</dd>
  </dl>
  <a href="https://www.google.com/maps?q=37.7608,140.4747">地図</a>
</body>
</html>
"""


def test_parse_sento_happy_path(parser: FukushimaParser) -> None:
    url = "https://fukushima1010.com/sento/azuma-yu/"
    result = parser.parse_sento(FUKUSHIMA_DETAIL_HTML_HAPPY, url)

    assert result is not None
    assert result["name"] == "吾妻湯"
    assert result["address"] == "福島県福島市本町1-2-3"
    assert result["phone"] == "024-111-2222"
    assert result["open_hours"] == "14:00〜22:30"
    assert result["holiday"] == "木曜日"
    assert result["lat"] == pytest.approx(37.7608)
    assert result["lng"] == pytest.approx(140.4747)
    assert result["prefecture"] == "福島県"
    assert result["region"] == "東北"
    assert result["facility_type"] == "sento"
    assert result["source_url"] == url


FUKUSHIMA_DETAIL_HTML_DESTINATION = """
<html>
<body>
  <h1>郡山の湯</h1>
  <dl>
    <dt>住所</dt><dd>福島県郡山市駅前2-3-4</dd>
  </dl>
  <a href="https://www.google.com/maps?destination=37.4000,140.3900">Google Map</a>
</body>
</html>
"""


def test_parse_sento_extracts_destination_coords(parser: FukushimaParser) -> None:
    result = parser.parse_sento(
        FUKUSHIMA_DETAIL_HTML_DESTINATION,
        "https://fukushima1010.com/shop/koriyama-no-yu/",
    )

    assert result is not None
    assert result["lat"] == pytest.approx(37.4000)
    assert result["lng"] == pytest.approx(140.3900)


FUKUSHIMA_DETAIL_HTML_TABLE_AND_TEL = """
<html>
<body>
  <h2>会津さくら湯</h2>
  <table>
    <tr><th>住所</th><td>福島県会津若松市1-1</td></tr>
    <tr><th>営業時間</th><td>15:00〜23:00</td></tr>
    <tr><th>休日</th><td>毎週火曜日</td></tr>
  </table>
  <a href="tel:0242-12-3456">電話</a>
</body>
</html>
"""


def test_parse_sento_supports_table_and_tel(parser: FukushimaParser) -> None:
    result = parser.parse_sento(
        FUKUSHIMA_DETAIL_HTML_TABLE_AND_TEL,
        "https://fukushima1010.com/sento/aizu-sakura-yu/",
    )

    assert result is not None
    assert result["address"] == "福島県会津若松市1-1"
    assert result["phone"] == "0242-12-3456"
    assert result["open_hours"] == "15:00〜23:00"
    assert result["holiday"] == "毎週火曜日"


FUKUSHIMA_DETAIL_HTML_NO_MAPS = """
<html>
<body>
  <h1>いわき湯</h1>
  <dl>
    <dt>住所</dt><dd>福島県いわき市平3-4-5</dd>
  </dl>
</body>
</html>
"""


def test_parse_sento_lat_lng_none_when_no_google_maps(parser: FukushimaParser) -> None:
    result = parser.parse_sento(
        FUKUSHIMA_DETAIL_HTML_NO_MAPS,
        "https://fukushima1010.com/sento/iwaki-yu/",
    )

    assert result is not None
    assert result["lat"] is None
    assert result["lng"] is None


FUKUSHIMA_DETAIL_HTML_NO_NAME = """
<html><body><p>施設情報</p></body></html>
"""


def test_parse_sento_returns_none_when_name_missing(parser: FukushimaParser) -> None:
    result = parser.parse_sento(
        FUKUSHIMA_DETAIL_HTML_NO_NAME,
        "https://fukushima1010.com/sento/unknown/",
    )
    assert result is None


FUKUSHIMA_DETAIL_HTML_NO_ADDRESS = """
<html><body><h1>住所なし湯</h1></body></html>
"""


def test_parse_sento_returns_none_when_address_missing(parser: FukushimaParser) -> None:
    result = parser.parse_sento(
        FUKUSHIMA_DETAIL_HTML_NO_ADDRESS,
        "https://fukushima1010.com/sento/no-address-yu/",
    )
    assert result is None


FUKUSHIMA_DETAIL_HTML_IFRAME = """
<html>
<body>
  <h1>磐梯湯</h1>
  <dl><dt>住所</dt><dd>福島県郡山市1-2-3</dd></dl>
  <iframe src="https://www.google.com/maps?q=37.4001,140.3801"></iframe>
</body>
</html>
"""


def test_parse_sento_extracts_iframe_coords(parser: FukushimaParser) -> None:
    result = parser.parse_sento(
        FUKUSHIMA_DETAIL_HTML_IFRAME,
        "https://fukushima1010.com/sento/bandai-yu/",
    )

    assert result is not None
    assert result["lat"] == pytest.approx(37.4001)
    assert result["lng"] == pytest.approx(140.3801)


FUKUSHIMA_DETAIL_HTML_AT_COORDS = """
<html>
<body>
  <h1>会津湯</h1>
  <dl><dt>住所</dt><dd>福島県会津若松市4-5-6</dd></dl>
  <a href="https://www.google.com/maps/place/%E4%BC%9A%E6%B4%A5/@37.4947,139.9299,16z">地図</a>
</body>
</html>
"""


def test_parse_sento_extracts_at_coords(parser: FukushimaParser) -> None:
    result = parser.parse_sento(
        FUKUSHIMA_DETAIL_HTML_AT_COORDS,
        "https://fukushima1010.com/sento/aizu-yu/",
    )

    assert result is not None
    assert result["lat"] == pytest.approx(37.4947)
    assert result["lng"] == pytest.approx(139.9299)


def test_parser_registration_for_fukushima() -> None:
    assert PARSERS["福島県"] is FukushimaParser
