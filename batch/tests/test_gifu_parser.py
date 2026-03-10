"""GifuParser のユニットテスト。"""
import pytest

from parsers import PARSERS
from parsers.gifu import GifuParser


@pytest.fixture
def parser() -> GifuParser:
    return GifuParser()


def test_parser_registered() -> None:
    assert "岐阜県" in PARSERS
    assert PARSERS["岐阜県"] is GifuParser


def test_get_list_urls(parser: GifuParser) -> None:
    assert parser.get_list_urls() == ["https://gifu1010.com/"]


GIFU_LIST_HTML = """
<html>
<body>
  <a href="/sento/いずみ湯">いずみ湯</a>
  <a href="/sento/かぎや温泉">かぎや温泉</a>
  <a href="/sento/いずみ湯">重複</a>
  <a href="/info/">お知らせ</a>
</body>
</html>
"""


def test_get_item_urls_extracts_and_deduplicates(parser: GifuParser) -> None:
    urls = parser.get_item_urls(GIFU_LIST_HTML, "https://gifu1010.com/")
    assert urls == [
        "https://gifu1010.com/sento/いずみ湯",
        "https://gifu1010.com/sento/かぎや温泉",
    ]


GIFU_DETAIL_HTML_HAPPY = """
<html>
<body>
  <h1>いずみ湯</h1>
  <table>
    <tr><th>住所</th><td>岐阜県岐阜市泉町1-2-3</td></tr>
    <tr><th>TEL</th><td>058-111-2222</td></tr>
    <tr><th>営業時間</th><td>15:00〜23:30</td></tr>
    <tr><th>定休日</th><td>火曜日</td></tr>
  </table>
  <a href="https://www.google.com/maps?q=35.4233,136.7606">地図</a>
</body>
</html>
"""


def test_parse_sento_happy_path(parser: GifuParser) -> None:
    url = "https://gifu1010.com/sento/いずみ湯"
    result = parser.parse_sento(GIFU_DETAIL_HTML_HAPPY, url)

    assert result is not None
    assert result["name"] == "いずみ湯"
    assert result["address"] == "岐阜県岐阜市泉町1-2-3"
    assert result["phone"] == "058-111-2222"
    assert result["open_hours"] == "15:00〜23:30"
    assert result["holiday"] == "火曜日"
    assert result["lat"] == pytest.approx(35.4233)
    assert result["lng"] == pytest.approx(136.7606)
    assert result["prefecture"] == "岐阜県"
    assert result["region"] == "中部"
    assert result["facility_type"] == "sento"
    assert result["source_url"] == url


GIFU_DETAIL_HTML_MAPS_DEST = """
<html>
<body>
  <h1>かぎや温泉</h1>
  <dl>
    <dt>住所</dt><dd>岐阜県岐阜市鍵屋町9-9</dd>
    <dt>営業時間</dt><dd>14:00〜22:00</dd>
  </dl>
  <a href="https://www.google.com/maps?destination=35.4001,136.7620">地図</a>
</body>
</html>
"""


def test_parse_sento_extracts_coords_from_destination(parser: GifuParser) -> None:
    result = parser.parse_sento(GIFU_DETAIL_HTML_MAPS_DEST, "https://gifu1010.com/sento/かぎや温泉")
    assert result is not None
    assert result["lat"] == pytest.approx(35.4001)
    assert result["lng"] == pytest.approx(136.7620)


GIFU_DETAIL_HTML_TEL_ONLY = """
<html>
<body>
  <h1>音羽湯</h1>
  <dl>
    <dt>住所</dt><dd>岐阜県大垣市音羽町3-4</dd>
    <dt>営業時間</dt><dd>16:00〜23:00</dd>
  </dl>
  <a href="tel:0584-11-1111">電話</a>
</body>
</html>
"""


def test_parse_sento_extracts_phone_from_tel_link(parser: GifuParser) -> None:
    result = parser.parse_sento(GIFU_DETAIL_HTML_TEL_ONLY, "https://gifu1010.com/sento/音羽湯")
    assert result is not None
    assert result["phone"] == "0584-11-1111"


def test_parse_sento_lat_lng_none_when_no_maps_link(parser: GifuParser) -> None:
    result = parser.parse_sento(GIFU_DETAIL_HTML_TEL_ONLY, "https://gifu1010.com/sento/音羽湯")
    assert result is not None
    assert result["lat"] is None
    assert result["lng"] is None


def test_parse_sento_returns_none_when_name_missing(parser: GifuParser) -> None:
    html = """
    <html><body>
      <dl><dt>住所</dt><dd>岐阜県岐阜市1-2-3</dd></dl>
    </body></html>
    """
    assert parser.parse_sento(html, "https://gifu1010.com/sento/unknown") is None


def test_parse_sento_returns_none_when_address_missing(parser: GifuParser) -> None:
    html = """
    <html><body>
      <h1>平和湯</h1>
      <p>住所情報なし</p>
    </body></html>
    """
    assert parser.parse_sento(html, "https://gifu1010.com/sento/heiwa") is None
