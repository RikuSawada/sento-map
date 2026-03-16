"""EhimeParser のユニットテスト。"""
import pytest

from parsers import PARSERS
from parsers.ehime import EhimeParser


@pytest.fixture
def parser() -> EhimeParser:
    return EhimeParser()


EHIME_TOP_HTML = """
<html>
<body>
  <a href="https://ehime1010.com/category/sento/">銭湯一覧</a>
  <a href="/category/news/">お知らせ</a>
  <a href="https://example.com/category/sento/">外部</a>
</body>
</html>
"""


EHIME_LIST_HTML = """
<html>
<body>
  <article><h2><a href="https://ehime1010.com/2025/01/10/matsuyama-yu/">松山湯</a></h2></article>
  <article><h2><a href="/2025/02/01/imabari-yu/">今治湯</a></h2></article>
  <a href="https://ehime1010.com/category/sento/">一覧（除外）</a>
  <a href="https://ehime1010.com/wp-admin/">管理（除外）</a>
</body>
</html>
"""


EHIME_DETAIL_HTML_HAPPY = """
<html>
<body>
  <h1 class="entry-title">松山湯</h1>
  <dl>
    <dt>住所</dt><dd>愛媛県松山市1-2-3</dd>
    <dt>TEL</dt><dd>089-123-4567</dd>
    <dt>営業時間</dt><dd>15:00〜23:00</dd>
    <dt>定休日</dt><dd>木曜日</dd>
  </dl>
  <a href="https://www.google.com/maps?q=33.8392,132.7657">地図</a>
</body>
</html>
"""


EHIME_DETAIL_HTML_IFRAME = """
<html>
<body>
  <h1>今治湯</h1>
  <dl><dt>住所</dt><dd>愛媛県今治市2-3-4</dd></dl>
  <iframe src="https://www.google.com/maps/embed?pb=!1m18!2d132.9978!3d34.0661"></iframe>
</body>
</html>
"""


EHIME_DETAIL_HTML_NO_ADDRESS = """
<html>
<body>
  <h1>住所なし湯</h1>
</body>
</html>
"""


EHIME_DETAIL_HTML_NO_NAME = """
<html>
<body>
  <dl><dt>住所</dt><dd>愛媛県宇和島市3-4-5</dd></dl>
</body>
</html>
"""


def test_parse_sento_happy_path(parser: EhimeParser) -> None:
    result = parser.parse_sento(EHIME_DETAIL_HTML_HAPPY, "https://ehime1010.com/2025/01/10/matsuyama-yu/")

    assert result is not None
    assert result["name"] == "松山湯"
    assert result["address"] == "愛媛県松山市1-2-3"
    assert result["phone"] == "089-123-4567"
    assert result["open_hours"] == "15:00〜23:00"
    assert result["holiday"] == "木曜日"
    assert result["lat"] == pytest.approx(33.8392)
    assert result["lng"] == pytest.approx(132.7657)
    assert result["prefecture"] == "愛媛県"
    assert result["region"] == "四国"
    assert result["facility_type"] == "sento"


def test_parse_sento_extracts_coordinates_from_iframe(parser: EhimeParser) -> None:
    result = parser.parse_sento(EHIME_DETAIL_HTML_IFRAME, "https://ehime1010.com/2025/02/01/imabari-yu/")
    assert result is not None
    assert result["lat"] == pytest.approx(34.0661)
    assert result["lng"] == pytest.approx(132.9978)


def test_parse_sento_returns_none_when_address_missing(parser: EhimeParser) -> None:
    result = parser.parse_sento(EHIME_DETAIL_HTML_NO_ADDRESS, "https://ehime1010.com/2025/03/01/no-address/")
    assert result is None


def test_parse_sento_returns_none_when_name_missing(parser: EhimeParser) -> None:
    result = parser.parse_sento(EHIME_DETAIL_HTML_NO_NAME, "https://ehime1010.com/2025/03/01/no-name/")
    assert result is None


def test_get_all_list_urls_collects_list_pages(parser: EhimeParser) -> None:
    urls = parser.get_all_list_urls(EHIME_TOP_HTML)
    assert "https://ehime1010.com/" in urls
    assert "https://ehime1010.com/category/sento" in urls
    assert "https://ehime1010.com/category/news" in urls
    assert all("example.com" not in url for url in urls)


def test_get_item_urls_extracts_detail_urls(parser: EhimeParser) -> None:
    urls = parser.get_item_urls(EHIME_LIST_HTML, "https://ehime1010.com/category/sento/")
    assert "https://ehime1010.com/2025/01/10/matsuyama-yu" in urls
    assert "https://ehime1010.com/2025/02/01/imabari-yu" in urls
    assert all("/category/" not in url for url in urls)
    assert all("/wp-admin" not in url for url in urls)


def test_parsers_contains_ehime() -> None:
    assert "愛媛県" in PARSERS
    assert PARSERS["愛媛県"] is EhimeParser
