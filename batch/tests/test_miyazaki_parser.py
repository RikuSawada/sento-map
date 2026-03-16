"""MiyazakiParser のユニットテスト。"""
import pytest

from parsers import PARSERS
from parsers.miyazaki import MiyazakiParser


@pytest.fixture
def parser() -> MiyazakiParser:
    return MiyazakiParser()


MIYAZAKI_TOP_HTML = """
<html>
<body>
  <a href="https://miyazaki1010.com/category/sento/">銭湯一覧</a>
  <a href="/category/news/">お知らせ</a>
  <a href="https://example.com/category/sento/">外部</a>
</body>
</html>
"""


MIYAZAKI_LIST_HTML = """
<html>
<body>
  <article><h2><a href="https://miyazaki1010.com/2025/01/10/miyazaki-yu/">宮崎湯</a></h2></article>
  <article><h2><a href="/2025/02/01/nobeoka-yu/">延岡湯</a></h2></article>
  <a href="https://miyazaki1010.com/category/sento/">一覧（除外）</a>
  <a href="https://miyazaki1010.com/wp-admin/">管理（除外）</a>
</body>
</html>
"""


MIYAZAKI_DETAIL_HTML_HAPPY = """
<html>
<body>
  <h1 class="entry-title">宮崎湯</h1>
  <dl>
    <dt>住所</dt><dd>宮崎県宮崎市1-2-3</dd>
    <dt>TEL</dt><dd>0985-12-3456</dd>
    <dt>営業時間</dt><dd>15:00〜23:00</dd>
    <dt>定休日</dt><dd>木曜日</dd>
  </dl>
  <a href="https://www.google.com/maps?q=31.9111,131.4239">地図</a>
</body>
</html>
"""


MIYAZAKI_DETAIL_HTML_IFRAME = """
<html>
<body>
  <h1>延岡湯</h1>
  <dl><dt>住所</dt><dd>宮崎県延岡市2-3-4</dd></dl>
  <iframe src="https://www.google.com/maps/embed?pb=!1m18!2d131.6649!3d32.5834"></iframe>
</body>
</html>
"""


MIYAZAKI_DETAIL_HTML_NO_ADDRESS = """
<html>
<body>
  <h1>住所なし湯</h1>
</body>
</html>
"""


MIYAZAKI_DETAIL_HTML_NO_NAME = """
<html>
<body>
  <dl><dt>住所</dt><dd>宮崎県日南市3-4-5</dd></dl>
</body>
</html>
"""


def test_parse_sento_happy_path(parser: MiyazakiParser) -> None:
    result = parser.parse_sento(MIYAZAKI_DETAIL_HTML_HAPPY, "https://miyazaki1010.com/2025/01/10/miyazaki-yu/")

    assert result is not None
    assert result["name"] == "宮崎湯"
    assert result["address"] == "宮崎県宮崎市1-2-3"
    assert result["phone"] == "0985-12-3456"
    assert result["open_hours"] == "15:00〜23:00"
    assert result["holiday"] == "木曜日"
    assert result["lat"] == pytest.approx(31.9111)
    assert result["lng"] == pytest.approx(131.4239)
    assert result["prefecture"] == "宮崎県"
    assert result["region"] == "九州"
    assert result["facility_type"] == "sento"


def test_parse_sento_extracts_coordinates_from_iframe(parser: MiyazakiParser) -> None:
    result = parser.parse_sento(MIYAZAKI_DETAIL_HTML_IFRAME, "https://miyazaki1010.com/2025/02/01/nobeoka-yu/")
    assert result is not None
    assert result["lat"] == pytest.approx(32.5834)
    assert result["lng"] == pytest.approx(131.6649)


def test_parse_sento_returns_none_when_address_missing(parser: MiyazakiParser) -> None:
    result = parser.parse_sento(MIYAZAKI_DETAIL_HTML_NO_ADDRESS, "https://miyazaki1010.com/2025/03/01/no-address/")
    assert result is None


def test_parse_sento_returns_none_when_name_missing(parser: MiyazakiParser) -> None:
    result = parser.parse_sento(MIYAZAKI_DETAIL_HTML_NO_NAME, "https://miyazaki1010.com/2025/03/01/no-name/")
    assert result is None


def test_get_all_list_urls_collects_list_pages(parser: MiyazakiParser) -> None:
    urls = parser.get_all_list_urls(MIYAZAKI_TOP_HTML)
    assert "https://miyazaki1010.com/" in urls
    assert "https://miyazaki1010.com/category/sento" in urls
    assert "https://miyazaki1010.com/category/news" in urls
    assert all("example.com" not in url for url in urls)


def test_get_item_urls_extracts_detail_urls(parser: MiyazakiParser) -> None:
    urls = parser.get_item_urls(MIYAZAKI_LIST_HTML, "https://miyazaki1010.com/category/sento/")
    assert "https://miyazaki1010.com/2025/01/10/miyazaki-yu" in urls
    assert "https://miyazaki1010.com/2025/02/01/nobeoka-yu" in urls
    assert all("/category/" not in url for url in urls)
    assert all("/wp-admin" not in url for url in urls)


def test_parsers_contains_miyazaki() -> None:
    assert "宮崎県" in PARSERS
    assert PARSERS["宮崎県"] is MiyazakiParser
