"""KagawaParser のユニットテスト。"""
import pytest

from parsers import PARSERS
from parsers.kagawa import KagawaParser


@pytest.fixture
def parser() -> KagawaParser:
    return KagawaParser()


KAGAWA_TOP_HTML = """
<html>
<body>
  <a href="https://kagawa1010.com/category/sento/">銭湯一覧</a>
  <a href="/category/news/">お知らせ</a>
  <a href="https://example.com/category/sento/">外部</a>
</body>
</html>
"""


KAGAWA_LIST_HTML = """
<html>
<body>
  <article><h2><a href="https://kagawa1010.com/2025/01/10/takamatsu-yu/">高松湯</a></h2></article>
  <article><h2><a href="/2025/02/01/marugame-yu/">丸亀湯</a></h2></article>
  <a href="https://kagawa1010.com/category/sento/">一覧（除外）</a>
  <a href="https://kagawa1010.com/wp-admin/">管理（除外）</a>
</body>
</html>
"""


KAGAWA_DETAIL_HTML_HAPPY = """
<html>
<body>
  <h1 class="entry-title">高松湯</h1>
  <dl>
    <dt>住所</dt><dd>香川県高松市1-2-3</dd>
    <dt>TEL</dt><dd>087-123-4567</dd>
    <dt>営業時間</dt><dd>15:00〜23:00</dd>
    <dt>定休日</dt><dd>月曜日</dd>
  </dl>
  <a href="https://www.google.com/maps?q=34.3428,134.0466">地図</a>
</body>
</html>
"""


KAGAWA_DETAIL_HTML_IFRAME = """
<html>
<body>
  <h1>丸亀湯</h1>
  <dl><dt>住所</dt><dd>香川県丸亀市2-3-4</dd></dl>
  <iframe src="https://www.google.com/maps/embed?pb=!1m18!2d133.7971!3d34.2912"></iframe>
</body>
</html>
"""


KAGAWA_DETAIL_HTML_NO_ADDRESS = """
<html>
<body>
  <h1>住所なし湯</h1>
</body>
</html>
"""


KAGAWA_DETAIL_HTML_NO_NAME = """
<html>
<body>
  <dl><dt>住所</dt><dd>香川県坂出市3-4-5</dd></dl>
</body>
</html>
"""


def test_parse_sento_happy_path(parser: KagawaParser) -> None:
    result = parser.parse_sento(KAGAWA_DETAIL_HTML_HAPPY, "https://kagawa1010.com/2025/01/10/takamatsu-yu/")

    assert result is not None
    assert result["name"] == "高松湯"
    assert result["address"] == "香川県高松市1-2-3"
    assert result["phone"] == "087-123-4567"
    assert result["open_hours"] == "15:00〜23:00"
    assert result["holiday"] == "月曜日"
    assert result["lat"] == pytest.approx(34.3428)
    assert result["lng"] == pytest.approx(134.0466)
    assert result["prefecture"] == "香川県"
    assert result["region"] == "四国"
    assert result["facility_type"] == "sento"


def test_parse_sento_extracts_coordinates_from_iframe(parser: KagawaParser) -> None:
    result = parser.parse_sento(KAGAWA_DETAIL_HTML_IFRAME, "https://kagawa1010.com/2025/02/01/marugame-yu/")
    assert result is not None
    assert result["lat"] == pytest.approx(34.2912)
    assert result["lng"] == pytest.approx(133.7971)


def test_parse_sento_returns_none_when_address_missing(parser: KagawaParser) -> None:
    result = parser.parse_sento(KAGAWA_DETAIL_HTML_NO_ADDRESS, "https://kagawa1010.com/2025/03/01/no-address/")
    assert result is None


def test_parse_sento_returns_none_when_name_missing(parser: KagawaParser) -> None:
    result = parser.parse_sento(KAGAWA_DETAIL_HTML_NO_NAME, "https://kagawa1010.com/2025/03/01/no-name/")
    assert result is None


def test_get_all_list_urls_collects_list_pages(parser: KagawaParser) -> None:
    urls = parser.get_all_list_urls(KAGAWA_TOP_HTML)
    assert "https://kagawa1010.com/" in urls
    assert "https://kagawa1010.com/category/sento" in urls
    assert "https://kagawa1010.com/category/news" in urls
    assert all("example.com" not in url for url in urls)


def test_get_item_urls_extracts_wordpress_post_urls(parser: KagawaParser) -> None:
    urls = parser.get_item_urls(KAGAWA_LIST_HTML, "https://kagawa1010.com/category/sento/")
    assert "https://kagawa1010.com/2025/01/10/takamatsu-yu" in urls
    assert "https://kagawa1010.com/2025/02/01/marugame-yu" in urls
    assert all("/category/" not in url for url in urls)
    assert all("/wp-admin" not in url for url in urls)


def test_parsers_contains_kagawa() -> None:
    assert "香川県" in PARSERS
    assert PARSERS["香川県"] is KagawaParser
