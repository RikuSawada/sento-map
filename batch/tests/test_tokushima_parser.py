"""TokushimaParser のユニットテスト。"""
import pytest

from parsers import PARSERS
from parsers.tokushima import TokushimaParser


@pytest.fixture
def parser() -> TokushimaParser:
    return TokushimaParser()


TOKUSHIMA_TOP_HTML = """
<html>
<body>
  <a href="https://tokushima1010.com/category/sento/">銭湯一覧</a>
  <a href="/category/news/">お知らせ</a>
  <a href="https://example.com/category/sento/">外部</a>
</body>
</html>
"""


TOKUSHIMA_LIST_HTML = """
<html>
<body>
  <article><h2><a href="https://tokushima1010.com/2025/01/10/tokushima-yu/">徳島湯</a></h2></article>
  <article><h2><a href="/2025/02/01/naruto-yu/">鳴門湯</a></h2></article>
  <a href="https://tokushima1010.com/category/sento/">一覧（除外）</a>
  <a href="https://tokushima1010.com/wp-admin/">管理（除外）</a>
</body>
</html>
"""


TOKUSHIMA_DETAIL_HTML_HAPPY = """
<html>
<body>
  <h1 class="entry-title">徳島湯</h1>
  <dl>
    <dt>住所</dt><dd>徳島県徳島市1-2-3</dd>
    <dt>TEL</dt><dd>088-123-4567</dd>
    <dt>営業時間</dt><dd>15:00〜23:00</dd>
    <dt>定休日</dt><dd>火曜日</dd>
  </dl>
  <a href="https://www.google.com/maps?q=34.0658,134.5593">地図</a>
</body>
</html>
"""


TOKUSHIMA_DETAIL_HTML_IFRAME = """
<html>
<body>
  <h1>鳴門湯</h1>
  <dl><dt>住所</dt><dd>徳島県鳴門市2-3-4</dd></dl>
  <iframe src="https://www.google.com/maps/embed?pb=!1m18!2d134.6076!3d34.1777"></iframe>
</body>
</html>
"""


TOKUSHIMA_DETAIL_HTML_NO_ADDRESS = """
<html>
<body>
  <h1>住所なし湯</h1>
</body>
</html>
"""


TOKUSHIMA_DETAIL_HTML_NO_NAME = """
<html>
<body>
  <dl><dt>住所</dt><dd>徳島県阿南市3-4-5</dd></dl>
</body>
</html>
"""


def test_parse_sento_happy_path(parser: TokushimaParser) -> None:
    result = parser.parse_sento(TOKUSHIMA_DETAIL_HTML_HAPPY, "https://tokushima1010.com/2025/01/10/tokushima-yu/")

    assert result is not None
    assert result["name"] == "徳島湯"
    assert result["address"] == "徳島県徳島市1-2-3"
    assert result["phone"] == "088-123-4567"
    assert result["open_hours"] == "15:00〜23:00"
    assert result["holiday"] == "火曜日"
    assert result["lat"] == pytest.approx(34.0658)
    assert result["lng"] == pytest.approx(134.5593)
    assert result["prefecture"] == "徳島県"
    assert result["region"] == "四国"
    assert result["facility_type"] == "sento"


def test_parse_sento_extracts_coordinates_from_iframe(parser: TokushimaParser) -> None:
    result = parser.parse_sento(TOKUSHIMA_DETAIL_HTML_IFRAME, "https://tokushima1010.com/2025/02/01/naruto-yu/")
    assert result is not None
    assert result["lat"] == pytest.approx(34.1777)
    assert result["lng"] == pytest.approx(134.6076)


def test_parse_sento_returns_none_when_address_missing(parser: TokushimaParser) -> None:
    result = parser.parse_sento(TOKUSHIMA_DETAIL_HTML_NO_ADDRESS, "https://tokushima1010.com/2025/03/01/no-address/")
    assert result is None


def test_parse_sento_returns_none_when_name_missing(parser: TokushimaParser) -> None:
    result = parser.parse_sento(TOKUSHIMA_DETAIL_HTML_NO_NAME, "https://tokushima1010.com/2025/03/01/no-name/")
    assert result is None


def test_get_all_list_urls_collects_list_pages(parser: TokushimaParser) -> None:
    urls = parser.get_all_list_urls(TOKUSHIMA_TOP_HTML)
    assert "https://tokushima1010.com/" in urls
    assert "https://tokushima1010.com/category/sento" in urls
    assert "https://tokushima1010.com/category/news" in urls
    assert all("example.com" not in url for url in urls)


def test_get_item_urls_extracts_detail_urls(parser: TokushimaParser) -> None:
    urls = parser.get_item_urls(TOKUSHIMA_LIST_HTML, "https://tokushima1010.com/category/sento/")
    assert "https://tokushima1010.com/2025/01/10/tokushima-yu" in urls
    assert "https://tokushima1010.com/2025/02/01/naruto-yu" in urls
    assert all("/category/" not in url for url in urls)
    assert all("/wp-admin" not in url for url in urls)


def test_parsers_contains_tokushima() -> None:
    assert "徳島県" in PARSERS
    assert PARSERS["徳島県"] is TokushimaParser
