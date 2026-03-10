"""NiigataParser のユニットテスト。"""
import pytest

from parsers import PARSERS
from parsers.niigata import NiigataParser


@pytest.fixture
def parser() -> NiigataParser:
    return NiigataParser()


def test_get_list_urls(parser: NiigataParser) -> None:
    urls = parser.get_list_urls()
    assert urls == ["https://niigata1010.com/sento-list/"]


NIIGATA_LIST_HTML = """
<html>
<body>
  <a href="/sento/matsu-yu/">松の湯</a>
  <a href="https://niigata1010.com/sento_list/ume-yu/">梅の湯</a>
  <a href="https://www.niigata1010.com/bath/take-yu/">竹の湯</a>
  <a href="/sento-list/">一覧（除外）</a>
  <a href="/category/news/">カテゴリ（除外）</a>
  <a href="https://example.com/sento/outside/">外部（除外）</a>
  <a href="/sento/matsu-yu/">重複</a>
</body>
</html>
"""


def test_get_item_urls_extracts_and_deduplicates(parser: NiigataParser) -> None:
    urls = parser.get_item_urls(NIIGATA_LIST_HTML, "https://niigata1010.com/sento-list/")
    assert urls == [
        "https://niigata1010.com/sento/matsu-yu/",
        "https://niigata1010.com/sento_list/ume-yu/",
        "https://www.niigata1010.com/bath/take-yu/",
    ]


NIIGATA_DETAIL_HTML_HAPPY = """
<html>
<body>
  <h1>松の湯</h1>
  <dl>
    <dt>住所</dt><dd>新潟県新潟市中央区1-2-3</dd>
    <dt>TEL</dt><dd>025-111-2222</dd>
    <dt>営業時間</dt><dd>15:00〜23:00</dd>
    <dt>定休日</dt><dd>火曜日</dd>
  </dl>
  <a href="https://www.google.com/maps?q=37.9026,139.0232">地図</a>
</body>
</html>
"""


def test_parse_sento_happy_path(parser: NiigataParser) -> None:
    result = parser.parse_sento(NIIGATA_DETAIL_HTML_HAPPY, "https://niigata1010.com/sento/matsu-yu/")

    assert result is not None
    assert result["name"] == "松の湯"
    assert result["address"] == "新潟県新潟市中央区1-2-3"
    assert result["phone"] == "025-111-2222"
    assert result["open_hours"] == "15:00〜23:00"
    assert result["holiday"] == "火曜日"
    assert result["lat"] == pytest.approx(37.9026)
    assert result["lng"] == pytest.approx(139.0232)
    assert result["prefecture"] == "新潟県"
    assert result["region"] == "中部"
    assert result["facility_type"] == "sento"
    assert result["source_url"] == "https://niigata1010.com/sento/matsu-yu/"


NIIGATA_DETAIL_HTML_DESTINATION = """
<html>
<body>
  <h1>梅の湯</h1>
  <dl>
    <dt>住所</dt><dd>新潟県長岡市4-5-6</dd>
  </dl>
  <a href="https://www.google.com/maps/dir/?api=1&destination=37.4462,138.8512">地図</a>
</body>
</html>
"""


def test_parse_sento_coords_from_destination(parser: NiigataParser) -> None:
    result = parser.parse_sento(NIIGATA_DETAIL_HTML_DESTINATION, "https://niigata1010.com/sento/ume-yu/")
    assert result is not None
    assert result["lat"] == pytest.approx(37.4462)
    assert result["lng"] == pytest.approx(138.8512)


NIIGATA_DETAIL_HTML_NO_COORDS = """
<html>
<body>
  <h1>竹の湯</h1>
  <dl>
    <dt>住所</dt><dd>新潟県上越市7-8-9</dd>
    <dt>営業時間</dt><dd>14:00〜22:00</dd>
  </dl>
</body>
</html>
"""


def test_parse_sento_returns_none_coords_when_map_missing(parser: NiigataParser) -> None:
    result = parser.parse_sento(NIIGATA_DETAIL_HTML_NO_COORDS, "https://niigata1010.com/sento/take-yu/")
    assert result is not None
    assert result["lat"] is None
    assert result["lng"] is None


NIIGATA_DETAIL_HTML_TEL_LINK = """
<html>
<body>
  <h1>桜湯</h1>
  <table>
    <tr><th>住所</th><td>新潟県三条市1-1-1</td></tr>
    <tr><th>休業日</th><td>月曜日</td></tr>
  </table>
  <a href="tel:0256-22-3344">電話</a>
</body>
</html>
"""


def test_parse_sento_phone_from_tel_and_table_fields(parser: NiigataParser) -> None:
    result = parser.parse_sento(NIIGATA_DETAIL_HTML_TEL_LINK, "https://niigata1010.com/sento/sakura-yu/")
    assert result is not None
    assert result["address"] == "新潟県三条市1-1-1"
    assert result["phone"] == "0256-22-3344"
    assert result["holiday"] == "月曜日"


def test_parse_sento_returns_none_when_name_missing(parser: NiigataParser) -> None:
    html = """
    <html><body>
      <dl><dt>住所</dt><dd>新潟県</dd></dl>
    </body></html>
    """
    assert parser.parse_sento(html, "https://niigata1010.com/sento/unknown/") is None


def test_parser_registered_in_parsers_dict() -> None:
    assert "新潟県" in PARSERS
    assert PARSERS["新潟県"] is NiigataParser
