"""YamaguchiParser のユニットテスト。"""
import pytest

from parsers import PARSERS
from parsers.yamaguchi import YamaguchiParser


@pytest.fixture
def parser() -> YamaguchiParser:
    return YamaguchiParser()


YAMAGUCHI_TOP_HTML = """
<html>
<body>
  <a href="https://yamaguchi1010.com/category/sento/">銭湯一覧</a>
  <a href="/category/news/">お知らせ</a>
  <a href="https://example.com/category/sento/">外部</a>
</body>
</html>
"""


YAMAGUCHI_LIST_HTML = """
<html>
<body>
  <article><h2><a href="https://yamaguchi1010.com/2025/01/10/yamaguchi-yu/">山口湯</a></h2></article>
  <article><h2><a href="/2025/02/01/shimonoseki-yu/">下関湯</a></h2></article>
  <a href="https://yamaguchi1010.com/category/sento/">一覧（除外）</a>
  <a href="https://yamaguchi1010.com/wp-admin/">管理（除外）</a>
</body>
</html>
"""


YAMAGUCHI_DETAIL_HTML_HAPPY = """
<html>
<body>
  <h1 class="entry-title">山口湯</h1>
  <dl>
    <dt>住所</dt><dd>山口県山口市1-2-3</dd>
    <dt>TEL</dt><dd>083-123-4567</dd>
    <dt>営業時間</dt><dd>15:00〜23:00</dd>
    <dt>定休日</dt><dd>水曜日</dd>
  </dl>
  <a href="https://www.google.com/maps?q=34.1785,131.4737">地図</a>
</body>
</html>
"""


YAMAGUCHI_DETAIL_HTML_IFRAME = """
<html>
<body>
  <h1>下関湯</h1>
  <dl><dt>住所</dt><dd>山口県下関市2-3-4</dd></dl>
  <iframe src="https://www.google.com/maps/embed?pb=!1m18!2d130.9500!3d33.9578"></iframe>
</body>
</html>
"""


YAMAGUCHI_DETAIL_HTML_NO_ADDRESS = """
<html>
<body>
  <h1>住所なし湯</h1>
</body>
</html>
"""


YAMAGUCHI_DETAIL_HTML_NO_NAME = """
<html>
<body>
  <dl><dt>住所</dt><dd>山口県宇部市3-4-5</dd></dl>
</body>
</html>
"""


def test_parse_sento_happy_path(parser: YamaguchiParser) -> None:
    result = parser.parse_sento(YAMAGUCHI_DETAIL_HTML_HAPPY, "https://yamaguchi1010.com/2025/01/10/yamaguchi-yu/")

    assert result is not None
    assert result["name"] == "山口湯"
    assert result["address"] == "山口県山口市1-2-3"
    assert result["phone"] == "083-123-4567"
    assert result["open_hours"] == "15:00〜23:00"
    assert result["holiday"] == "水曜日"
    assert result["lat"] == pytest.approx(34.1785)
    assert result["lng"] == pytest.approx(131.4737)
    assert result["prefecture"] == "山口県"
    assert result["region"] == "中国"
    assert result["facility_type"] == "sento"


def test_parse_sento_extracts_coordinates_from_iframe(parser: YamaguchiParser) -> None:
    result = parser.parse_sento(YAMAGUCHI_DETAIL_HTML_IFRAME, "https://yamaguchi1010.com/2025/02/01/shimonoseki-yu/")
    assert result is not None
    assert result["lat"] == pytest.approx(33.9578)
    assert result["lng"] == pytest.approx(130.9500)


def test_parse_sento_returns_none_when_address_missing(parser: YamaguchiParser) -> None:
    result = parser.parse_sento(YAMAGUCHI_DETAIL_HTML_NO_ADDRESS, "https://yamaguchi1010.com/2025/03/01/no-address/")
    assert result is None


def test_parse_sento_returns_none_when_name_missing(parser: YamaguchiParser) -> None:
    result = parser.parse_sento(YAMAGUCHI_DETAIL_HTML_NO_NAME, "https://yamaguchi1010.com/2025/03/01/no-name/")
    assert result is None


def test_get_all_list_urls_collects_list_pages(parser: YamaguchiParser) -> None:
    urls = parser.get_all_list_urls(YAMAGUCHI_TOP_HTML)
    assert "https://yamaguchi1010.com/" in urls
    assert "https://yamaguchi1010.com/category/sento" in urls
    assert "https://yamaguchi1010.com/category/news" in urls
    assert all("example.com" not in url for url in urls)


def test_get_item_urls_extracts_detail_urls(parser: YamaguchiParser) -> None:
    urls = parser.get_item_urls(YAMAGUCHI_LIST_HTML, "https://yamaguchi1010.com/category/sento/")
    assert "https://yamaguchi1010.com/2025/01/10/yamaguchi-yu" in urls
    assert "https://yamaguchi1010.com/2025/02/01/shimonoseki-yu" in urls
    assert all("/category/" not in url for url in urls)
    assert all("/wp-admin" not in url for url in urls)


def test_parsers_contains_yamaguchi() -> None:
    assert "山口県" in PARSERS
    assert PARSERS["山口県"] is YamaguchiParser
