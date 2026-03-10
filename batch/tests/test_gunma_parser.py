"""GunmaParser のユニットテスト。"""
import pytest

from parsers.gunma import GunmaParser


@pytest.fixture
def parser() -> GunmaParser:
    return GunmaParser()


GUNMA_DETAIL_HTML_HAPPY = """
<html>
<body>
  <h1 class="entry-title">前橋湯</h1>
  <dl>
    <dt>住所</dt><dd>群馬県前橋市本町1-2-3</dd>
    <dt>TEL</dt><dd>027-123-4567</dd>
    <dt>営業時間</dt><dd>15:00〜23:00</dd>
    <dt>定休日</dt><dd>月曜日</dd>
  </dl>
  <a href="https://www.google.com/maps?q=36.3911,139.0608">地図</a>
</body>
</html>
"""


def test_parse_sento_happy_path(parser: GunmaParser) -> None:
    result = parser.parse_sento(GUNMA_DETAIL_HTML_HAPPY, "https://gunma1010.com/2025/01/01/maebashi-yu/")

    assert result is not None
    assert result["name"] == "前橋湯"
    assert result["address"] == "群馬県前橋市本町1-2-3"
    assert result["phone"] == "027-123-4567"
    assert result["open_hours"] == "15:00〜23:00"
    assert result["holiday"] == "月曜日"
    assert result["lat"] == pytest.approx(36.3911)
    assert result["lng"] == pytest.approx(139.0608)
    assert result["prefecture"] == "群馬県"
    assert result["region"] == "関東"
    assert result["facility_type"] == "sento"


GUNMA_DETAIL_HTML_MAPS_AT = """
<html>
<body>
  <h1>高崎湯</h1>
  <dl><dt>住所</dt><dd>群馬県高崎市2-3-4</dd></dl>
  <a href="https://www.google.com/maps/place/abc/@36.3219,139.0033,17z">Google Map</a>
</body>
</html>
"""


def test_parse_sento_extracts_coords_from_maps_at_format(parser: GunmaParser) -> None:
    result = parser.parse_sento(GUNMA_DETAIL_HTML_MAPS_AT, "https://gunma1010.com/takasaki-yu/")
    assert result is not None
    assert result["lat"] == pytest.approx(36.3219)
    assert result["lng"] == pytest.approx(139.0033)


GUNMA_DETAIL_HTML_TABLE_TEL = """
<html>
<body>
  <h1>伊勢崎湯</h1>
  <table>
    <tr><td>住所</td><td>群馬県伊勢崎市3-4-5</td></tr>
    <tr><td>営業時間</td><td>14:00〜22:00</td></tr>
    <tr><td>休業日</td><td>木曜日</td></tr>
  </table>
  <a href="tel:0270-11-2233">電話</a>
</body>
</html>
"""


def test_parse_sento_extracts_table_and_tel_link(parser: GunmaParser) -> None:
    result = parser.parse_sento(GUNMA_DETAIL_HTML_TABLE_TEL, "https://gunma1010.com/isesaki-yu/")
    assert result is not None
    assert result["address"] == "群馬県伊勢崎市3-4-5"
    assert result["open_hours"] == "14:00〜22:00"
    assert result["holiday"] == "木曜日"
    assert result["phone"] == "0270-11-2233"


GUNMA_DETAIL_HTML_NO_COORDS = """
<html>
<body>
  <h1>桐生湯</h1>
  <dl><dt>住所</dt><dd>群馬県桐生市4-5-6</dd></dl>
</body>
</html>
"""


def test_parse_sento_without_google_maps_link_returns_none_coords(parser: GunmaParser) -> None:
    result = parser.parse_sento(GUNMA_DETAIL_HTML_NO_COORDS, "https://gunma1010.com/kiryu-yu/")
    assert result is not None
    assert result["lat"] is None
    assert result["lng"] is None


def test_parse_sento_returns_none_when_name_missing(parser: GunmaParser) -> None:
    html = "<html><body><p>銭湯情報</p></body></html>"
    result = parser.parse_sento(html, "https://gunma1010.com/unknown/")
    assert result is None


def test_parse_sento_returns_none_for_area_page(parser: GunmaParser) -> None:
    html = """
    <html><body>
      <h1>前橋エリア一覧</h1>
      <a href="https://gunma1010.com/2025/01/01/a/">A</a>
    </body></html>
    """
    result = parser.parse_sento(html, "https://gunma1010.com/?page_id=12")
    assert result is None


def test_get_all_list_urls_collects_top_and_area_links(parser: GunmaParser) -> None:
    html = """
    <html><body>
      <a href="/category/maebashi/">前橋エリア一覧</a>
      <a href="https://gunma1010.com/list/takasaki/">高崎地区一覧</a>
      <a href="https://gunma1010.com/?cat=3">桐生地域</a>
      <a href="https://gunma1010.com/category/maebashi/">前橋エリア一覧（重複）</a>
      <a href="https://example.com/category/outside/">外部</a>
    </body></html>
    """
    urls = parser.get_all_list_urls(html)

    assert "https://gunma1010.com/" in urls
    assert "https://gunma1010.com/category/maebashi/" in urls
    assert "https://gunma1010.com/list/takasaki/" in urls
    assert "https://gunma1010.com/?cat=3" in urls
    assert urls.count("https://gunma1010.com/category/maebashi/") == 1


def test_get_item_urls_extracts_detail_links_only(parser: GunmaParser) -> None:
    html = """
    <html><body>
      <a href="https://gunma1010.com/2025/01/01/maebashi-yu/">前橋湯</a>
      <a href="/takasaki-yu/">高崎湯</a>
      <a href="/?p=42">桐生湯</a>
      <a href="/category/maebashi/">カテゴリ</a>
      <a href="/page/2/">ページネーション</a>
      <a href="https://gunma1010.com/news/">お知らせ</a>
      <a href="https://example.com/2025/01/01/outside/">外部</a>
      <a href="/takasaki-yu/">高崎湯（重複）</a>
    </body></html>
    """
    urls = parser.get_item_urls(html, "https://gunma1010.com/category/maebashi/")

    assert "https://gunma1010.com/2025/01/01/maebashi-yu/" in urls
    assert "https://gunma1010.com/takasaki-yu/" in urls
    assert "https://gunma1010.com/?p=42" in urls
    assert "https://gunma1010.com/category/maebashi/" not in urls
    assert "https://gunma1010.com/news/" not in urls
    assert all("example.com" not in u for u in urls)
    assert urls.count("https://gunma1010.com/takasaki-yu/") == 1
