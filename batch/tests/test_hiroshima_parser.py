"""HiroshimaParser のユニットテスト。"""
import pytest

from parsers import PARSERS
from parsers.hiroshima import HiroshimaParser


@pytest.fixture
def parser() -> HiroshimaParser:
    return HiroshimaParser()


HIROSHIMA_TOP_HTML = """
<html>
<body>
  <a href="https://hiroshima1010.com/category/sento/">銭湯一覧</a>
  <a href="/category/news/">お知らせ</a>
  <a href="https://example.com/category/sento/">外部</a>
</body>
</html>
"""


HIROSHIMA_LIST_HTML = """
<html>
<body>
  <article><h2><a href="https://hiroshima1010.com/2025/01/10/hiroshima-yu/">広島湯</a></h2></article>
  <article><h2><a href="/2025/02/01/fukuyama-yu/">福山湯</a></h2></article>
  <a href="https://hiroshima1010.com/category/sento/">一覧（除外）</a>
  <a href="https://hiroshima1010.com/wp-admin/">管理（除外）</a>
</body>
</html>
"""


HIROSHIMA_DETAIL_HTML_HAPPY = """
<html>
<body>
  <h1 class="entry-title">広島湯</h1>
  <dl>
    <dt>住所</dt><dd>広島県広島市中区1-2-3</dd>
    <dt>TEL</dt><dd>082-123-4567</dd>
    <dt>営業時間</dt><dd>15:00〜23:00</dd>
    <dt>定休日</dt><dd>火曜日</dd>
  </dl>
  <a href="https://www.google.com/maps?q=34.3853,132.4553">地図</a>
</body>
</html>
"""


HIROSHIMA_DETAIL_HTML_IFRAME = """
<html>
<body>
  <h1>福山湯</h1>
  <dl><dt>住所</dt><dd>広島県福山市2-3-4</dd></dl>
  <iframe src="https://www.google.com/maps/embed?pb=!1m18!2d133.3623!3d34.4859"></iframe>
</body>
</html>
"""


HIROSHIMA_DETAIL_HTML_NO_ADDRESS = """
<html>
<body>
  <h1>住所なし湯</h1>
</body>
</html>
"""


HIROSHIMA_DETAIL_HTML_NO_NAME = """
<html>
<body>
  <dl><dt>住所</dt><dd>広島県呉市3-4-5</dd></dl>
</body>
</html>
"""


def test_parse_sento_happy_path(parser: HiroshimaParser) -> None:
    result = parser.parse_sento(HIROSHIMA_DETAIL_HTML_HAPPY, "https://hiroshima1010.com/2025/01/10/hiroshima-yu/")

    assert result is not None
    assert result["name"] == "広島湯"
    assert result["address"] == "広島県広島市中区1-2-3"
    assert result["phone"] == "082-123-4567"
    assert result["open_hours"] == "15:00〜23:00"
    assert result["holiday"] == "火曜日"
    assert result["lat"] == pytest.approx(34.3853)
    assert result["lng"] == pytest.approx(132.4553)
    assert result["prefecture"] == "広島県"
    assert result["region"] == "中国"
    assert result["facility_type"] == "sento"


def test_parse_sento_extracts_coordinates_from_iframe(parser: HiroshimaParser) -> None:
    result = parser.parse_sento(HIROSHIMA_DETAIL_HTML_IFRAME, "https://hiroshima1010.com/2025/02/01/fukuyama-yu/")
    assert result is not None
    assert result["lat"] == pytest.approx(34.4859)
    assert result["lng"] == pytest.approx(133.3623)


def test_parse_sento_returns_none_when_address_missing(parser: HiroshimaParser) -> None:
    result = parser.parse_sento(HIROSHIMA_DETAIL_HTML_NO_ADDRESS, "https://hiroshima1010.com/2025/03/01/no-address/")
    assert result is None


def test_parse_sento_returns_none_when_name_missing(parser: HiroshimaParser) -> None:
    result = parser.parse_sento(HIROSHIMA_DETAIL_HTML_NO_NAME, "https://hiroshima1010.com/2025/03/01/no-name/")
    assert result is None


def test_get_all_list_urls_collects_list_pages(parser: HiroshimaParser) -> None:
    urls = parser.get_all_list_urls(HIROSHIMA_TOP_HTML)
    assert "https://hiroshima1010.com/" in urls
    assert "https://hiroshima1010.com/category/sento" in urls
    assert "https://hiroshima1010.com/category/news" in urls
    assert all("example.com" not in url for url in urls)


def test_get_item_urls_extracts_detail_urls(parser: HiroshimaParser) -> None:
    urls = parser.get_item_urls(HIROSHIMA_LIST_HTML, "https://hiroshima1010.com/category/sento/")
    assert "https://hiroshima1010.com/2025/01/10/hiroshima-yu" in urls
    assert "https://hiroshima1010.com/2025/02/01/fukuyama-yu" in urls
    assert all("/category/" not in url for url in urls)
    assert all("/wp-admin" not in url for url in urls)


def test_parsers_contains_hiroshima() -> None:
    assert "広島県" in PARSERS
    assert PARSERS["広島県"] is HiroshimaParser
