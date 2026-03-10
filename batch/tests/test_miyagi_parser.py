"""MiyagiParser のユニットテスト。"""
import pytest

from parsers import PARSERS
from parsers.miyagi import MiyagiParser


@pytest.fixture
def parser() -> MiyagiParser:
    return MiyagiParser()


MIYAGI_TOP_HTML = """
<html>
<body>
  <a href="https://miyagi1010.com/category/sento/">銭湯一覧</a>
  <a href="/category/news/">お知らせ</a>
  <a href="https://example.com/category/sento/">外部</a>
</body>
</html>
"""


MIYAGI_LIST_HTML = """
<html>
<body>
  <article><h2><a href="https://miyagi1010.com/2025/01/10/aoba-yu/">青葉湯</a></h2></article>
  <article><h2><a href="/2025/02/01/sendai-yu/">仙台湯</a></h2></article>
  <a href="https://miyagi1010.com/category/sento/">一覧（除外）</a>
  <a href="https://miyagi1010.com/wp-admin/">管理（除外）</a>
</body>
</html>
"""


MIYAGI_DETAIL_HTML_HAPPY = """
<html>
<body>
  <h1 class="entry-title">青葉湯</h1>
  <dl>
    <dt>住所</dt><dd>宮城県仙台市青葉区1-2-3</dd>
    <dt>TEL</dt><dd>022-123-4567</dd>
    <dt>営業時間</dt><dd>15:00〜23:00</dd>
    <dt>定休日</dt><dd>月曜日</dd>
  </dl>
  <a href="https://www.google.com/maps?q=38.2682,140.8694">地図</a>
</body>
</html>
"""


MIYAGI_DETAIL_HTML_NO_COORD = """
<html>
<body>
  <h1>榴岡湯</h1>
  <table>
    <tr><th>住所</th><td>宮城県仙台市宮城野区2-3-4</td></tr>
    <tr><th>電話</th><td>022-987-6543</td></tr>
  </table>
</body>
</html>
"""


MIYAGI_DETAIL_HTML_NO_NAME = """
<html>
<body>
  <dl><dt>住所</dt><dd>宮城県仙台市若林区3-4-5</dd></dl>
</body>
</html>
"""


def test_parse_sento_happy_path(parser: MiyagiParser) -> None:
    result = parser.parse_sento(MIYAGI_DETAIL_HTML_HAPPY, "https://miyagi1010.com/2025/01/10/aoba-yu/")

    assert result is not None
    assert result["name"] == "青葉湯"
    assert result["address"] == "宮城県仙台市青葉区1-2-3"
    assert result["phone"] == "022-123-4567"
    assert result["open_hours"] == "15:00〜23:00"
    assert result["holiday"] == "月曜日"
    assert result["lat"] == pytest.approx(38.2682)
    assert result["lng"] == pytest.approx(140.8694)
    assert result["prefecture"] == "宮城県"
    assert result["region"] == "東北"
    assert result["facility_type"] == "sento"


def test_parse_sento_returns_none_when_name_missing(parser: MiyagiParser) -> None:
    result = parser.parse_sento(MIYAGI_DETAIL_HTML_NO_NAME, "https://miyagi1010.com/2025/01/10/unknown/")
    assert result is None


def test_parse_sento_without_coordinates(parser: MiyagiParser) -> None:
    result = parser.parse_sento(MIYAGI_DETAIL_HTML_NO_COORD, "https://miyagi1010.com/2025/02/11/tsutsujigaoka-yu/")
    assert result is not None
    assert result["lat"] is None
    assert result["lng"] is None
    assert result["address"] == "宮城県仙台市宮城野区2-3-4"


def test_get_all_list_urls_collects_list_pages(parser: MiyagiParser) -> None:
    urls = parser.get_all_list_urls(MIYAGI_TOP_HTML)
    assert "https://miyagi1010.com/" in urls
    assert "https://miyagi1010.com/category/sento" in urls
    assert "https://miyagi1010.com/category/news" in urls
    assert all("example.com" not in url for url in urls)


def test_get_item_urls_extracts_detail_urls(parser: MiyagiParser) -> None:
    urls = parser.get_item_urls(MIYAGI_LIST_HTML, "https://miyagi1010.com/category/sento/")
    assert "https://miyagi1010.com/2025/01/10/aoba-yu" in urls
    assert "https://miyagi1010.com/2025/02/01/sendai-yu" in urls
    assert all("/category/" not in url for url in urls)
    assert all("/wp-admin" not in url for url in urls)


def test_parsers_contains_miyagi() -> None:
    assert "宮城県" in PARSERS
    assert PARSERS["宮城県"] is MiyagiParser
