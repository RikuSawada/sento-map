"""ShimaneParser のユニットテスト。"""
import pytest

from parsers import PARSERS
from parsers.shimane import ShimaneParser


@pytest.fixture
def parser() -> ShimaneParser:
    return ShimaneParser()


SHIMANE_TOP_HTML = """
<html>
<body>
  <a href="https://shimane1010.com/category/sento/">銭湯一覧</a>
  <a href="/category/news/">お知らせ</a>
  <a href="https://example.com/category/sento/">外部</a>
</body>
</html>
"""


SHIMANE_LIST_HTML = """
<html>
<body>
  <article><h2><a href="https://shimane1010.com/2025/01/10/shimane-yu/">島根湯</a></h2></article>
  <article><h2><a href="/2025/02/01/matsue-yu/">松江湯</a></h2></article>
  <a href="https://shimane1010.com/category/sento/">一覧（除外）</a>
  <a href="https://shimane1010.com/wp-admin/">管理（除外）</a>
</body>
</html>
"""


SHIMANE_DETAIL_HTML_HAPPY = """
<html>
<body>
  <h1 class="entry-title">島根湯</h1>
  <dl>
    <dt>住所</dt><dd>島根県松江市1-2-3</dd>
    <dt>TEL</dt><dd>0852-12-3456</dd>
    <dt>営業時間</dt><dd>15:00〜23:00</dd>
    <dt>定休日</dt><dd>金曜日</dd>
  </dl>
  <a href="https://www.google.com/maps?q=35.4723,133.0505">地図</a>
</body>
</html>
"""


SHIMANE_DETAIL_HTML_IFRAME = """
<html>
<body>
  <h1>松江湯</h1>
  <dl><dt>住所</dt><dd>島根県松江市2-3-4</dd></dl>
  <iframe src="https://www.google.com/maps/embed?pb=!1m18!2d133.2239!3d35.3678"></iframe>
</body>
</html>
"""


SHIMANE_DETAIL_HTML_NO_ADDRESS = """
<html>
<body>
  <h1>住所なし湯</h1>
</body>
</html>
"""


SHIMANE_DETAIL_HTML_NO_NAME = """
<html>
<body>
  <dl><dt>住所</dt><dd>島根県出雲市3-4-5</dd></dl>
</body>
</html>
"""


def test_parse_sento_happy_path(parser: ShimaneParser) -> None:
    result = parser.parse_sento(SHIMANE_DETAIL_HTML_HAPPY, "https://shimane1010.com/2025/01/10/shimane-yu/")

    assert result is not None
    assert result["name"] == "島根湯"
    assert result["address"] == "島根県松江市1-2-3"
    assert result["phone"] == "0852-12-3456"
    assert result["open_hours"] == "15:00〜23:00"
    assert result["holiday"] == "金曜日"
    assert result["lat"] == pytest.approx(35.4723)
    assert result["lng"] == pytest.approx(133.0505)
    assert result["prefecture"] == "島根県"
    assert result["region"] == "中国"
    assert result["facility_type"] == "sento"


def test_parse_sento_extracts_coordinates_from_iframe(parser: ShimaneParser) -> None:
    result = parser.parse_sento(SHIMANE_DETAIL_HTML_IFRAME, "https://shimane1010.com/2025/02/01/matsue-yu/")
    assert result is not None
    assert result["lat"] == pytest.approx(35.3678)
    assert result["lng"] == pytest.approx(133.2239)


def test_parse_sento_returns_none_when_address_missing(parser: ShimaneParser) -> None:
    result = parser.parse_sento(SHIMANE_DETAIL_HTML_NO_ADDRESS, "https://shimane1010.com/2025/03/01/no-address/")
    assert result is None


def test_parse_sento_returns_none_when_name_missing(parser: ShimaneParser) -> None:
    result = parser.parse_sento(SHIMANE_DETAIL_HTML_NO_NAME, "https://shimane1010.com/2025/03/01/no-name/")
    assert result is None


def test_get_all_list_urls_collects_list_pages(parser: ShimaneParser) -> None:
    urls = parser.get_all_list_urls(SHIMANE_TOP_HTML)
    assert "https://shimane1010.com/" in urls
    assert "https://shimane1010.com/category/sento" in urls
    assert "https://shimane1010.com/category/news" in urls
    assert all("example.com" not in url for url in urls)


def test_get_item_urls_extracts_detail_urls(parser: ShimaneParser) -> None:
    urls = parser.get_item_urls(SHIMANE_LIST_HTML, "https://shimane1010.com/category/sento/")
    assert "https://shimane1010.com/2025/01/10/shimane-yu" in urls
    assert "https://shimane1010.com/2025/02/01/matsue-yu" in urls
    assert all("/category/" not in url for url in urls)
    assert all("/wp-admin" not in url for url in urls)


def test_parsers_contains_shimane() -> None:
    assert "島根県" in PARSERS
    assert PARSERS["島根県"] is ShimaneParser
