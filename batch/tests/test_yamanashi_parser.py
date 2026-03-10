"""YamanashiParser のユニットテスト。"""
import pytest

from parsers.yamanashi import YamanashiParser, LIST_URL


@pytest.fixture
def parser() -> YamanashiParser:
    return YamanashiParser()


def test_get_list_urls_returns_top(parser: YamanashiParser) -> None:
    assert parser.get_list_urls() == [LIST_URL]


YAMANASHI_LIST_HTML_PAGINATION = """
<html>
<body>
  <a href="/page/2/">2</a>
  <a href="https://sento-yamanashi.com/?paged=2">2(dup)</a>
  <a href="/about/">about</a>
</body>
</html>
"""


def test_get_all_list_urls_collects_pagination(parser: YamanashiParser) -> None:
    urls = parser.get_all_list_urls(YAMANASHI_LIST_HTML_PAGINATION)
    assert LIST_URL in urls
    assert "https://sento-yamanashi.com/page/2/" in urls
    assert "https://sento-yamanashi.com/?paged=2" in urls


YAMANASHI_LIST_HTML_ITEMS = """
<html>
<body>
  <a href="/sento/fuji-yu/">富士湯</a>
  <a href="/bath/kofu-onsen/">甲府温泉</a>
  <a href="/page/2/">一覧2</a>
  <a href="/category/news/">お知らせ</a>
  <a href="https://example.com/elsewhere">外部</a>
  <a href="/sento/fuji-yu/">富士湯(重複)</a>
</body>
</html>
"""


def test_get_item_urls_extracts_and_deduplicates(parser: YamanashiParser) -> None:
    urls = parser.get_item_urls(YAMANASHI_LIST_HTML_ITEMS, LIST_URL)
    assert len(urls) == 2
    assert "https://sento-yamanashi.com/sento/fuji-yu/" in urls
    assert "https://sento-yamanashi.com/bath/kofu-onsen/" in urls


YAMANASHI_DETAIL_HTML_HAPPY = """
<html>
<body>
  <h1 class="entry-title">富士湯</h1>
  <dl>
    <dt>住所</dt><dd>山梨県甲府市1-2-3</dd>
    <dt>TEL</dt><dd>055-111-2222</dd>
    <dt>営業時間</dt><dd>15:00〜23:00</dd>
    <dt>定休日</dt><dd>月曜日</dd>
  </dl>
  <a href="https://www.google.com/maps?q=35.6668,138.5684">地図</a>
</body>
</html>
"""


def test_parse_sento_happy_path(parser: YamanashiParser) -> None:
    url = "https://sento-yamanashi.com/sento/fuji-yu/"
    result = parser.parse_sento(YAMANASHI_DETAIL_HTML_HAPPY, url)

    assert result is not None
    assert result["name"] == "富士湯"
    assert result["address"] == "山梨県甲府市1-2-3"
    assert result["phone"] == "055-111-2222"
    assert result["open_hours"] == "15:00〜23:00"
    assert result["holiday"] == "月曜日"
    assert result["lat"] == pytest.approx(35.6668)
    assert result["lng"] == pytest.approx(138.5684)
    assert result["prefecture"] == "山梨県"
    assert result["region"] == "中部"
    assert result["facility_type"] == "sento"
    assert result["source_url"] == url


YAMANASHI_DETAIL_HTML_TEL_AND_DEST = """
<html>
<body>
  <h1>甲府温泉</h1>
  <table>
    <tr><th>住所</th><td>山梨県甲府市4-5-6</td></tr>
  </table>
  <a href="tel:055-999-0000">電話</a>
  <a href="https://www.google.com/maps?destination=35.6600,138.5600">地図</a>
</body>
</html>
"""


def test_parse_sento_tel_link_and_destination_coords(parser: YamanashiParser) -> None:
    result = parser.parse_sento(
        YAMANASHI_DETAIL_HTML_TEL_AND_DEST,
        "https://sento-yamanashi.com/bath/kofu-onsen/",
    )
    assert result is not None
    assert result["phone"] == "055-999-0000"
    assert result["lat"] == pytest.approx(35.6600)
    assert result["lng"] == pytest.approx(138.5600)


YAMANASHI_DETAIL_HTML_NO_MAPS = """
<html>
<body>
  <h1>石和の湯</h1>
  <dl>
    <dt>住所</dt><dd>山梨県笛吹市7-8-9</dd>
  </dl>
</body>
</html>
"""


def test_parse_sento_returns_none_coords_when_no_maps_link(parser: YamanashiParser) -> None:
    result = parser.parse_sento(
        YAMANASHI_DETAIL_HTML_NO_MAPS,
        "https://sento-yamanashi.com/sento/isawa-no-yu/",
    )
    assert result is not None
    assert result["lat"] is None
    assert result["lng"] is None


def test_parse_sento_returns_none_when_name_missing(parser: YamanashiParser) -> None:
    html = "<html><body><p>not found</p></body></html>"
    result = parser.parse_sento(html, "https://sento-yamanashi.com/sento/missing/")
    assert result is None
