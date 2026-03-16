"""KochiParser のユニットテスト。"""
import pytest

from parsers import PARSERS
from parsers.kochi import KochiParser


@pytest.fixture
def parser() -> KochiParser:
    return KochiParser()


KOCHI_TOP_HTML = """
<html>
<body>
  <a href="https://kochi1010.com/category/sento/">銭湯一覧</a>
  <a href="/category/news/">お知らせ</a>
  <a href="https://example.com/category/sento/">外部</a>
</body>
</html>
"""


KOCHI_LIST_HTML = """
<html>
<body>
  <article><h2><a href="https://kochi1010.com/2025/01/10/kochi-yu/">高知湯</a></h2></article>
  <article><h2><a href="/2025/02/01/nankoku-yu/">南国湯</a></h2></article>
  <a href="https://kochi1010.com/category/sento/">一覧（除外）</a>
  <a href="https://kochi1010.com/wp-admin/">管理（除外）</a>
</body>
</html>
"""


KOCHI_DETAIL_HTML_HAPPY = """
<html>
<body>
  <h1 class="entry-title">高知湯</h1>
  <dl>
    <dt>住所</dt><dd>高知県高知市1-2-3</dd>
    <dt>TEL</dt><dd>088-812-3456</dd>
    <dt>営業時間</dt><dd>15:00〜23:00</dd>
    <dt>定休日</dt><dd>水曜日</dd>
  </dl>
  <a href="https://www.google.com/maps?q=33.5597,133.5311">地図</a>
</body>
</html>
"""


KOCHI_DETAIL_HTML_IFRAME = """
<html>
<body>
  <h1>南国湯</h1>
  <dl><dt>住所</dt><dd>高知県南国市2-3-4</dd></dl>
  <iframe src="https://www.google.com/maps/embed?pb=!1m18!2d133.6410!3d33.5757"></iframe>
</body>
</html>
"""


KOCHI_DETAIL_HTML_NO_ADDRESS = """
<html>
<body>
  <h1>住所なし湯</h1>
</body>
</html>
"""


KOCHI_DETAIL_HTML_NO_NAME = """
<html>
<body>
  <dl><dt>住所</dt><dd>高知県四万十市3-4-5</dd></dl>
</body>
</html>
"""


def test_parse_sento_happy_path(parser: KochiParser) -> None:
    result = parser.parse_sento(KOCHI_DETAIL_HTML_HAPPY, "https://kochi1010.com/2025/01/10/kochi-yu/")

    assert result is not None
    assert result["name"] == "高知湯"
    assert result["address"] == "高知県高知市1-2-3"
    assert result["phone"] == "088-812-3456"
    assert result["open_hours"] == "15:00〜23:00"
    assert result["holiday"] == "水曜日"
    assert result["lat"] == pytest.approx(33.5597)
    assert result["lng"] == pytest.approx(133.5311)
    assert result["prefecture"] == "高知県"
    assert result["region"] == "四国"
    assert result["facility_type"] == "sento"


def test_parse_sento_extracts_coordinates_from_iframe(parser: KochiParser) -> None:
    result = parser.parse_sento(KOCHI_DETAIL_HTML_IFRAME, "https://kochi1010.com/2025/02/01/nankoku-yu/")
    assert result is not None
    assert result["lat"] == pytest.approx(33.5757)
    assert result["lng"] == pytest.approx(133.6410)


def test_parse_sento_returns_none_when_address_missing(parser: KochiParser) -> None:
    result = parser.parse_sento(KOCHI_DETAIL_HTML_NO_ADDRESS, "https://kochi1010.com/2025/03/01/no-address/")
    assert result is None


def test_parse_sento_returns_none_when_name_missing(parser: KochiParser) -> None:
    result = parser.parse_sento(KOCHI_DETAIL_HTML_NO_NAME, "https://kochi1010.com/2025/03/01/no-name/")
    assert result is None


def test_get_all_list_urls_collects_list_pages(parser: KochiParser) -> None:
    urls = parser.get_all_list_urls(KOCHI_TOP_HTML)
    assert "https://kochi1010.com/" in urls
    assert "https://kochi1010.com/category/sento" in urls
    assert "https://kochi1010.com/category/news" in urls
    assert all("example.com" not in url for url in urls)


def test_get_item_urls_extracts_detail_urls(parser: KochiParser) -> None:
    urls = parser.get_item_urls(KOCHI_LIST_HTML, "https://kochi1010.com/category/sento/")
    assert "https://kochi1010.com/2025/01/10/kochi-yu" in urls
    assert "https://kochi1010.com/2025/02/01/nankoku-yu" in urls
    assert all("/category/" not in url for url in urls)
    assert all("/wp-admin" not in url for url in urls)


def test_parsers_contains_kochi() -> None:
    assert "高知県" in PARSERS
    assert PARSERS["高知県"] is KochiParser
