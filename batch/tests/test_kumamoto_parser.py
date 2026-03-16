"""KumamotoParser のユニットテスト。"""
import pytest

from parsers import PARSERS
from parsers.kumamoto import KumamotoParser


@pytest.fixture
def parser() -> KumamotoParser:
    return KumamotoParser()


KUMAMOTO_TOP_HTML = """
<html>
<body>
  <a href="https://kumamoto1010.com/category/sento/">銭湯一覧</a>
  <a href="/category/news/">お知らせ</a>
  <a href="https://example.com/category/sento/">外部</a>
</body>
</html>
"""


KUMAMOTO_LIST_HTML = """
<html>
<body>
  <article><h2><a href="https://kumamoto1010.com/2025/01/10/kumamoto-yu/">熊本湯</a></h2></article>
  <article><h2><a href="/2025/02/01/yatsushiro-yu/">八代湯</a></h2></article>
  <a href="https://kumamoto1010.com/category/sento/">一覧（除外）</a>
  <a href="https://kumamoto1010.com/wp-admin/">管理（除外）</a>
</body>
</html>
"""


KUMAMOTO_DETAIL_HTML_HAPPY = """
<html>
<body>
  <h1 class="entry-title">熊本湯</h1>
  <dl>
    <dt>住所</dt><dd>熊本県熊本市1-2-3</dd>
    <dt>TEL</dt><dd>096-123-4567</dd>
    <dt>営業時間</dt><dd>15:00〜23:00</dd>
    <dt>定休日</dt><dd>月曜日</dd>
  </dl>
  <a href="https://www.google.com/maps?q=32.8031,130.7079">地図</a>
</body>
</html>
"""


KUMAMOTO_DETAIL_HTML_IFRAME = """
<html>
<body>
  <h1>八代湯</h1>
  <dl><dt>住所</dt><dd>熊本県八代市2-3-4</dd></dl>
  <iframe src="https://www.google.com/maps/embed?pb=!1m18!2d130.6025!3d32.5099"></iframe>
</body>
</html>
"""


KUMAMOTO_DETAIL_HTML_NO_ADDRESS = """
<html>
<body>
  <h1>住所なし湯</h1>
</body>
</html>
"""


KUMAMOTO_DETAIL_HTML_NO_NAME = """
<html>
<body>
  <dl><dt>住所</dt><dd>熊本県天草市3-4-5</dd></dl>
</body>
</html>
"""


def test_parse_sento_happy_path(parser: KumamotoParser) -> None:
    result = parser.parse_sento(KUMAMOTO_DETAIL_HTML_HAPPY, "https://kumamoto1010.com/2025/01/10/kumamoto-yu/")

    assert result is not None
    assert result["name"] == "熊本湯"
    assert result["address"] == "熊本県熊本市1-2-3"
    assert result["phone"] == "096-123-4567"
    assert result["open_hours"] == "15:00〜23:00"
    assert result["holiday"] == "月曜日"
    assert result["lat"] == pytest.approx(32.8031)
    assert result["lng"] == pytest.approx(130.7079)
    assert result["prefecture"] == "熊本県"
    assert result["region"] == "九州"
    assert result["facility_type"] == "sento"


def test_parse_sento_extracts_coordinates_from_iframe(parser: KumamotoParser) -> None:
    result = parser.parse_sento(KUMAMOTO_DETAIL_HTML_IFRAME, "https://kumamoto1010.com/2025/02/01/yatsushiro-yu/")
    assert result is not None
    assert result["lat"] == pytest.approx(32.5099)
    assert result["lng"] == pytest.approx(130.6025)


def test_parse_sento_returns_none_when_address_missing(parser: KumamotoParser) -> None:
    result = parser.parse_sento(KUMAMOTO_DETAIL_HTML_NO_ADDRESS, "https://kumamoto1010.com/2025/03/01/no-address/")
    assert result is None


def test_parse_sento_returns_none_when_name_missing(parser: KumamotoParser) -> None:
    result = parser.parse_sento(KUMAMOTO_DETAIL_HTML_NO_NAME, "https://kumamoto1010.com/2025/03/01/no-name/")
    assert result is None


def test_get_all_list_urls_collects_list_pages(parser: KumamotoParser) -> None:
    urls = parser.get_all_list_urls(KUMAMOTO_TOP_HTML)
    assert "https://kumamoto1010.com/" in urls
    assert "https://kumamoto1010.com/category/sento" in urls
    assert "https://kumamoto1010.com/category/news" in urls
    assert all("example.com" not in url for url in urls)


def test_get_item_urls_extracts_wordpress_post_urls(parser: KumamotoParser) -> None:
    urls = parser.get_item_urls(KUMAMOTO_LIST_HTML, "https://kumamoto1010.com/category/sento/")
    assert "https://kumamoto1010.com/2025/01/10/kumamoto-yu" in urls
    assert "https://kumamoto1010.com/2025/02/01/yatsushiro-yu" in urls
    assert all("/category/" not in url for url in urls)
    assert all("/wp-admin" not in url for url in urls)


def test_parsers_contains_kumamoto() -> None:
    assert "熊本県" in PARSERS
    assert PARSERS["熊本県"] is KumamotoParser
