"""ShizuokaParser のユニットテスト。"""
import pytest

from parsers import PARSERS
from parsers.shizuoka import ShizuokaParser


@pytest.fixture
def parser() -> ShizuokaParser:
    return ShizuokaParser()


def test_parser_registered_in_parsers_dict() -> None:
    assert "静岡県" in PARSERS
    assert PARSERS["静岡県"] is ShizuokaParser


def test_get_list_urls(parser: ShizuokaParser) -> None:
    assert parser.get_list_urls() == ["https://shizuoka1010.com/"]


SHIZUOKA_LIST_HTML = """
<html>
<body>
  <a href="/shop/atami-yu/">熱海湯</a>
  <a href="https://shizuoka1010.com/sento/shimizu-yu/">清水湯</a>
  <a href="/shop/atami-yu/">熱海湯（重複）</a>
  <a href="/news/2026/notice">お知らせ</a>
  <a href="/contact/">お問い合わせ</a>
  <a href="https://example.com/shop/outside/">外部</a>
  <a href="/assets/map.pdf">PDF</a>
</body>
</html>
"""


def test_get_item_urls_extracts_internal_detail_links(parser: ShizuokaParser) -> None:
    urls = parser.get_item_urls(SHIZUOKA_LIST_HTML, "https://shizuoka1010.com/")
    assert "https://shizuoka1010.com/shop/atami-yu" in urls
    assert "https://shizuoka1010.com/sento/shimizu-yu" in urls
    assert "https://example.com/shop/outside" not in urls
    assert all("/news/" not in u for u in urls)
    assert all("/contact/" not in u for u in urls)
    assert all(not u.endswith(".pdf") for u in urls)


def test_get_item_urls_deduplicates(parser: ShizuokaParser) -> None:
    html = """
    <html><body>
      <a href="/shop/kakegawa-yu/">掛川湯</a>
      <a href="https://shizuoka1010.com/shop/kakegawa-yu/">掛川湯（重複）</a>
    </body></html>
    """
    urls = parser.get_item_urls(html, "https://shizuoka1010.com/")
    assert urls == ["https://shizuoka1010.com/shop/kakegawa-yu"]


SHIZUOKA_DETAIL_HTML_HAPPY = """
<html>
<body>
  <h1>熱海湯</h1>
  <dl>
    <dt>住所</dt><dd>静岡県熱海市銀座町1-2-3</dd>
    <dt>TEL</dt><dd>0557-11-2233</dd>
    <dt>営業時間</dt><dd>14:00〜23:00</dd>
    <dt>定休日</dt><dd>火曜日</dd>
  </dl>
  <a href="https://www.google.com/maps?q=35.0952,139.0710">地図</a>
</body>
</html>
"""


def test_parse_sento_happy_path(parser: ShizuokaParser) -> None:
    url = "https://shizuoka1010.com/shop/atami-yu/"
    result = parser.parse_sento(SHIZUOKA_DETAIL_HTML_HAPPY, url)
    assert result is not None
    assert result["name"] == "熱海湯"
    assert result["address"] == "静岡県熱海市銀座町1-2-3"
    assert result["phone"] == "0557-11-2233"
    assert result["open_hours"] == "14:00〜23:00"
    assert result["holiday"] == "火曜日"
    assert result["lat"] == pytest.approx(35.0952)
    assert result["lng"] == pytest.approx(139.0710)
    assert result["prefecture"] == "静岡県"
    assert result["region"] == "中部"
    assert result["facility_type"] == "sento"
    assert result["source_url"] == url


SHIZUOKA_DETAIL_HTML_IFRAME = """
<html>
<body>
  <h1>清水湯</h1>
  <table>
    <tr><th>住所</th><td>静岡県静岡市清水区4-5-6</td></tr>
  </table>
  <iframe src="https://www.google.com/maps/embed?pb=!1m18!...!3d34.9850!...!4d138.4890!..."></iframe>
</body>
</html>
"""


def test_parse_sento_extracts_coords_from_iframe(parser: ShizuokaParser) -> None:
    result = parser.parse_sento(SHIZUOKA_DETAIL_HTML_IFRAME, "https://shizuoka1010.com/shop/shimizu-yu/")
    assert result is not None
    assert result["lat"] == pytest.approx(34.9850)
    assert result["lng"] == pytest.approx(138.4890)


SHIZUOKA_DETAIL_HTML_NO_COORDS = """
<html>
<body>
  <h1>富士見湯</h1>
  <dl>
    <dt>住所</dt><dd>静岡県富士市7-8-9</dd>
    <dt>電話</dt><dd>0545-12-3456</dd>
  </dl>
  <a href="https://maps.app.goo.gl/abcdef123456">地図</a>
</body>
</html>
"""


def test_parse_sento_returns_none_coords_when_not_in_map_url(parser: ShizuokaParser) -> None:
    result = parser.parse_sento(SHIZUOKA_DETAIL_HTML_NO_COORDS, "https://shizuoka1010.com/shop/fujimi-yu/")
    assert result is not None
    assert result["lat"] is None
    assert result["lng"] is None


def test_parse_sento_returns_none_when_name_missing(parser: ShizuokaParser) -> None:
    html = """
    <html><body><dl><dt>住所</dt><dd>静岡県浜松市1-1-1</dd></dl></body></html>
    """
    assert parser.parse_sento(html, "https://shizuoka1010.com/shop/unknown/") is None


def test_parse_sento_returns_none_when_address_missing(parser: ShizuokaParser) -> None:
    html = """
    <html><body><h1>名無し湯</h1><p>住所情報なし</p></body></html>
    """
    assert parser.parse_sento(html, "https://shizuoka1010.com/shop/no-address/") is None
