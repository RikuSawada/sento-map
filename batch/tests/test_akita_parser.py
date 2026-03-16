"""AkitaParser のユニットテスト。"""
import pytest

from parsers import PARSERS
from parsers.akita import AkitaParser


@pytest.fixture
def parser() -> AkitaParser:
    return AkitaParser()


AKITA_DETAIL_HTML_HAPPY = """
<html>
<body>
  <h1 class="entry-title">秋田温泉</h1>
  <dl>
    <dt>住所</dt><dd>秋田県秋田市1-2-3</dd>
    <dt>TEL</dt><dd>018-123-4567</dd>
    <dt>営業時間</dt><dd>15:00〜22:30</dd>
    <dt>定休日</dt><dd>月曜日</dd>
  </dl>
  <a href="https://www.google.com/maps?q=39.7199,140.1025">地図</a>
</body>
</html>
"""


def test_parse_sento_happy_path(parser: AkitaParser) -> None:
    result = parser.parse_sento(AKITA_DETAIL_HTML_HAPPY, "https://akita-sento.com/sento/akita-onsen/")
    assert result is not None
    assert result["name"] == "秋田温泉"
    assert result["address"] == "秋田県秋田市1-2-3"
    assert result["phone"] == "018-123-4567"
    assert result["open_hours"] == "15:00〜22:30"
    assert result["holiday"] == "月曜日"
    assert result["lat"] == pytest.approx(39.7199)
    assert result["lng"] == pytest.approx(140.1025)
    assert result["prefecture"] == "秋田県"
    assert result["region"] == "東北"
    assert result["facility_type"] == "sento"


AKITA_DETAIL_HTML_TABLE_AND_AT = """
<html>
<body>
  <h1>港の湯</h1>
  <table>
    <tr><th>住所</th><td>秋田県秋田市港2-3-4</td></tr>
    <tr><th>電話</th><td>018-222-3333</td></tr>
    <tr><th>休業日</th><td>第2火曜日</td></tr>
  </table>
  <a href="https://www.google.com/maps/place/%E6%B8%AF/@39.7000,140.1200,17z">地図</a>
</body>
</html>
"""


def test_parse_sento_extracts_table_and_at_coords(parser: AkitaParser) -> None:
    result = parser.parse_sento(AKITA_DETAIL_HTML_TABLE_AND_AT, "https://akita-sento.com/sento/minato/")
    assert result is not None
    assert result["address"] == "秋田県秋田市港2-3-4"
    assert result["phone"] == "018-222-3333"
    assert result["holiday"] == "第2火曜日"
    assert result["lat"] == pytest.approx(39.7000)
    assert result["lng"] == pytest.approx(140.1200)


AKITA_DETAIL_HTML_IFRAME = """
<html>
<body>
  <h2>旭湯</h2>
  <dl>
    <dt>住所</dt><dd>秋田県横手市5-6-7</dd>
  </dl>
  <iframe src="https://www.google.com/maps/embed?pb=!1m18!...!3d39.3100!...!4d140.5600!..."></iframe>
</body>
</html>
"""


def test_parse_sento_extracts_coords_from_iframe(parser: AkitaParser) -> None:
    result = parser.parse_sento(AKITA_DETAIL_HTML_IFRAME, "https://akita-sento.com/sento/asahi/")
    assert result is not None
    assert result["lat"] == pytest.approx(39.3100)
    assert result["lng"] == pytest.approx(140.5600)


AKITA_DETAIL_HTML_NO_COORDS = """
<html>
<body>
  <h1>白神の湯</h1>
  <dl>
    <dt>住所</dt><dd>秋田県能代市8-9-10</dd>
  </dl>
</body>
</html>
"""


def test_parse_sento_lat_lng_none_when_no_maps_link(parser: AkitaParser) -> None:
    result = parser.parse_sento(AKITA_DETAIL_HTML_NO_COORDS, "https://akita-sento.com/sento/shirakami/")
    assert result is not None
    assert result["lat"] is None
    assert result["lng"] is None


AKITA_DETAIL_HTML_NO_NAME = """
<html><body><p>銭湯情報なし</p></body></html>
"""


def test_parse_sento_returns_none_when_name_missing(parser: AkitaParser) -> None:
    result = parser.parse_sento(AKITA_DETAIL_HTML_NO_NAME, "https://akita-sento.com/sento/unknown/")
    assert result is None


AKITA_DETAIL_HTML_NO_ADDRESS = """
<html>
<body>
  <h1>秋田温泉</h1>
  <p>住所情報なし</p>
</body>
</html>
"""


def test_parse_sento_returns_none_when_address_missing(parser: AkitaParser) -> None:
    result = parser.parse_sento(AKITA_DETAIL_HTML_NO_ADDRESS, "https://akita-sento.com/sento/no-address/")
    assert result is None


AKITA_DETAIL_HTML_ADDRESS_TAG = """
<html>
<body>
  <h1>川反の湯</h1>
  <address>秋田県秋田市川反町 1-2-3</address>
</body>
</html>
"""


def test_parse_sento_falls_back_to_address_tag(parser: AkitaParser) -> None:
    result = parser.parse_sento(AKITA_DETAIL_HTML_ADDRESS_TAG, "https://akita-sento.com/sento/kawabata/")
    assert result is not None
    assert result["address"] == "秋田県秋田市川反町 1-2-3"


AKITA_DETAIL_HTML_IFRAME_Q = """
<html>
<body>
  <h1>土崎の湯</h1>
  <dl><dt>住所</dt><dd>秋田県秋田市土崎港1-2-3</dd></dl>
  <iframe src="https://www.google.com/maps?q=39.7501,140.0701"></iframe>
</body>
</html>
"""


def test_parse_sento_extracts_coords_from_iframe_q(parser: AkitaParser) -> None:
    result = parser.parse_sento(AKITA_DETAIL_HTML_IFRAME_Q, "https://akita-sento.com/sento/tsuchizaki/")
    assert result is not None
    assert result["lat"] == pytest.approx(39.7501)
    assert result["lng"] == pytest.approx(140.0701)


AKITA_LIST_HTML = """
<html>
<body>
  <a href="/sento/akita-onsen/">秋田温泉</a>
  <a href="/sento/akita-onsen/">秋田温泉（重複）</a>
  <a href="https://akita-sento.com/bath/minato/">港の湯</a>
  <a href="https://akita-sento.com/facility/asahi/">旭湯</a>
  <a href="/category/news/">お知らせ</a>
  <a href="https://example.com/sento/outside/">外部</a>
</body>
</html>
"""


def test_get_item_urls_extracts_detail_urls_only(parser: AkitaParser) -> None:
    urls = parser.get_item_urls(AKITA_LIST_HTML, "https://akita-sento.com/")
    assert urls == [
        "https://akita-sento.com/sento/akita-onsen/",
        "https://akita-sento.com/bath/minato/",
        "https://akita-sento.com/facility/asahi/",
    ]


def test_get_list_urls(parser: AkitaParser) -> None:
    assert parser.get_list_urls() == [
        "https://akita-sento.com/",
        "https://akita-sento.com/sento/",
    ]


def test_parsers_registry_contains_akita() -> None:
    assert PARSERS["秋田県"] is AkitaParser
