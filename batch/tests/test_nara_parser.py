"""NaraParser のユニットテスト。"""
import pytest

from parsers import PARSERS
from parsers.nara import NaraParser


@pytest.fixture
def parser() -> NaraParser:
    return NaraParser()


def test_registered_in_parsers() -> None:
    assert PARSERS["奈良県"] is NaraParser


def test_get_list_urls(parser: NaraParser) -> None:
    assert parser.get_list_urls() == ["https://nara1010.com/"]


NARA_LIST_HTML = """
<html>
<body>
  <a href="/sento/matsu-yu/">松の湯</a>
  <a href="https://nara1010.com/shop/ume-yu/">梅の湯</a>
  <a href="/?p=123">竹の湯</a>
  <a href="https://example.com/sento/outside/">外部</a>
  <a href="/privacy/">プライバシー</a>
  <a href="/">トップ</a>
  <a href="/sento/matsu-yu/">重複</a>
</body>
</html>
"""


def test_get_item_urls_extracts_internal_detail_urls(parser: NaraParser) -> None:
    urls = parser.get_item_urls(NARA_LIST_HTML, "https://nara1010.com/")

    assert "https://nara1010.com/sento/matsu-yu/" in urls
    assert "https://nara1010.com/shop/ume-yu/" in urls
    assert "https://nara1010.com/?p=123" in urls
    assert all("example.com" not in u for u in urls)
    assert all("privacy" not in u for u in urls)


def test_get_item_urls_deduplicates(parser: NaraParser) -> None:
    urls = parser.get_item_urls(NARA_LIST_HTML, "https://nara1010.com/")
    assert urls.count("https://nara1010.com/sento/matsu-yu/") == 1


NARA_DETAIL_HTML_HAPPY = """
<html>
<head><title>松の湯 | 奈良県浴場組合</title></head>
<body>
  <h1>松の湯</h1>
  <dl>
    <dt>住所</dt><dd>奈良県奈良市三条町1-2-3</dd>
    <dt>TEL</dt><dd>0742-11-2233</dd>
    <dt>営業時間</dt><dd>14:00-24:00</dd>
    <dt>定休日</dt><dd>月曜日</dd>
  </dl>
  <a href="https://www.google.com/maps?q=34.6851,135.8048">地図</a>
</body>
</html>
"""


def test_parse_sento_happy_path(parser: NaraParser) -> None:
    result = parser.parse_sento(NARA_DETAIL_HTML_HAPPY, "https://nara1010.com/sento/matsu-yu/")

    assert result is not None
    assert result["name"] == "松の湯"
    assert result["address"] == "奈良県奈良市三条町1-2-3"
    assert result["phone"] == "0742-11-2233"
    assert result["open_hours"] == "14:00-24:00"
    assert result["holiday"] == "月曜日"
    assert result["lat"] == pytest.approx(34.6851)
    assert result["lng"] == pytest.approx(135.8048)
    assert result["prefecture"] == "奈良県"
    assert result["region"] == "近畿"
    assert result["facility_type"] == "sento"


NARA_DETAIL_HTML_TABLE_TEL = """
<html>
<body>
  <h1>梅の湯</h1>
  <table>
    <tr><th>住所</th><td>奈良県大和郡山市2-3-4</td></tr>
    <tr><th>営業時間</th><td>15:00-22:30</td></tr>
    <tr><th>定休日</th><td>木曜日</td></tr>
  </table>
  <a href="tel:0743-55-6677">電話</a>
  <a href="https://www.google.com/maps/dir/?api=1&destination=34.6490,135.7820">地図</a>
</body>
</html>
"""


def test_parse_sento_extracts_tel_and_destination_coords(parser: NaraParser) -> None:
    result = parser.parse_sento(NARA_DETAIL_HTML_TABLE_TEL, "https://nara1010.com/shop/ume-yu/")

    assert result is not None
    assert result["phone"] == "0743-55-6677"
    assert result["lat"] == pytest.approx(34.6490)
    assert result["lng"] == pytest.approx(135.7820)


NARA_DETAIL_HTML_NO_COORDS = """
<html>
<body>
  <h1>竹の湯</h1>
  <p>住所: 奈良県橿原市5-6-7</p>
</body>
</html>
"""


def test_parse_sento_sets_coords_none_when_no_maps_link(parser: NaraParser) -> None:
    result = parser.parse_sento(NARA_DETAIL_HTML_NO_COORDS, "https://nara1010.com/sento/take-yu/")
    assert result is not None
    assert result["lat"] is None
    assert result["lng"] is None


NARA_DETAIL_HTML_NO_NAME = """
<html>
<body>
  <p>住所: 奈良県奈良市1-1-1</p>
</body>
</html>
"""


def test_parse_sento_returns_none_when_name_missing(parser: NaraParser) -> None:
    result = parser.parse_sento(NARA_DETAIL_HTML_NO_NAME, "https://nara1010.com/sento/unknown/")
    assert result is None


NARA_DETAIL_HTML_NO_ADDRESS = """
<html>
<body>
  <h1>名無し湯</h1>
</body>
</html>
"""


def test_parse_sento_returns_none_when_address_missing(parser: NaraParser) -> None:
    result = parser.parse_sento(NARA_DETAIL_HTML_NO_ADDRESS, "https://nara1010.com/sento/no-address/")
    assert result is None
