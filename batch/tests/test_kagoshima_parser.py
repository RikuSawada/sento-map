"""KagoshimaParser のユニットテスト。"""
import pytest

from parsers import PARSERS
from parsers.kagoshima import KagoshimaParser


@pytest.fixture
def parser() -> KagoshimaParser:
    return KagoshimaParser()


KAGOSHIMA_TOP_HTML = """
<html>
<body>
  <a href="https://kagoshima1010.com/category/sento/">銭湯一覧</a>
  <a href="/category/news/">お知らせ</a>
  <a href="https://example.com/category/sento/">外部</a>
</body>
</html>
"""


KAGOSHIMA_LIST_HTML = """
<html>
<body>
  <article><h2><a href="https://kagoshima1010.com/2025/01/10/kagoshima-yu/">鹿児島湯</a></h2></article>
  <article><h2><a href="/2025/02/01/kirishima-yu/">霧島湯</a></h2></article>
  <a href="https://kagoshima1010.com/category/sento/">一覧（除外）</a>
  <a href="https://kagoshima1010.com/wp-admin/">管理（除外）</a>
</body>
</html>
"""


KAGOSHIMA_DETAIL_HTML_HAPPY = """
<html>
<body>
  <h1 class="entry-title">鹿児島湯</h1>
  <dl>
    <dt>住所</dt><dd>鹿児島県鹿児島市1-2-3</dd>
    <dt>TEL</dt><dd>099-123-4567</dd>
    <dt>営業時間</dt><dd>15:00〜23:00</dd>
    <dt>定休日</dt><dd>水曜日</dd>
  </dl>
  <a href="https://www.google.com/maps?q=31.5966,130.5571">地図</a>
</body>
</html>
"""


KAGOSHIMA_DETAIL_HTML_IFRAME = """
<html>
<body>
  <h1>霧島湯</h1>
  <dl><dt>住所</dt><dd>鹿児島県霧島市2-3-4</dd></dl>
  <iframe src="https://www.google.com/maps/embed?pb=!1m18!2d130.7632!3d31.7411"></iframe>
</body>
</html>
"""


KAGOSHIMA_DETAIL_HTML_NO_ADDRESS = """
<html>
<body>
  <h1>住所なし湯</h1>
</body>
</html>
"""


KAGOSHIMA_DETAIL_HTML_NO_NAME = """
<html>
<body>
  <dl><dt>住所</dt><dd>鹿児島県指宿市3-4-5</dd></dl>
</body>
</html>
"""


def test_parse_sento_happy_path(parser: KagoshimaParser) -> None:
    result = parser.parse_sento(KAGOSHIMA_DETAIL_HTML_HAPPY, "https://kagoshima1010.com/2025/01/10/kagoshima-yu/")

    assert result is not None
    assert result["name"] == "鹿児島湯"
    assert result["address"] == "鹿児島県鹿児島市1-2-3"
    assert result["phone"] == "099-123-4567"
    assert result["open_hours"] == "15:00〜23:00"
    assert result["holiday"] == "水曜日"
    assert result["lat"] == pytest.approx(31.5966)
    assert result["lng"] == pytest.approx(130.5571)
    assert result["prefecture"] == "鹿児島県"
    assert result["region"] == "九州"
    assert result["facility_type"] == "sento"


def test_parse_sento_extracts_coordinates_from_iframe(parser: KagoshimaParser) -> None:
    result = parser.parse_sento(KAGOSHIMA_DETAIL_HTML_IFRAME, "https://kagoshima1010.com/2025/02/01/kirishima-yu/")
    assert result is not None
    assert result["lat"] == pytest.approx(31.7411)
    assert result["lng"] == pytest.approx(130.7632)


def test_parse_sento_returns_none_when_address_missing(parser: KagoshimaParser) -> None:
    result = parser.parse_sento(KAGOSHIMA_DETAIL_HTML_NO_ADDRESS, "https://kagoshima1010.com/2025/03/01/no-address/")
    assert result is None


def test_parse_sento_returns_none_when_name_missing(parser: KagoshimaParser) -> None:
    result = parser.parse_sento(KAGOSHIMA_DETAIL_HTML_NO_NAME, "https://kagoshima1010.com/2025/03/01/no-name/")
    assert result is None


def test_get_all_list_urls_collects_list_pages(parser: KagoshimaParser) -> None:
    urls = parser.get_all_list_urls(KAGOSHIMA_TOP_HTML)
    assert "https://kagoshima1010.com/" in urls
    assert "https://kagoshima1010.com/category/sento" in urls
    assert "https://kagoshima1010.com/category/news" in urls
    assert all("example.com" not in url for url in urls)


def test_get_item_urls_extracts_detail_urls(parser: KagoshimaParser) -> None:
    urls = parser.get_item_urls(KAGOSHIMA_LIST_HTML, "https://kagoshima1010.com/category/sento/")
    assert "https://kagoshima1010.com/2025/01/10/kagoshima-yu" in urls
    assert "https://kagoshima1010.com/2025/02/01/kirishima-yu" in urls
    assert all("/category/" not in url for url in urls)
    assert all("/wp-admin" not in url for url in urls)


def test_parsers_contains_kagoshima() -> None:
    assert "鹿児島県" in PARSERS
    assert PARSERS["鹿児島県"] is KagoshimaParser
