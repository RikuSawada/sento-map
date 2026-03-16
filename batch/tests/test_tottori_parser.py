"""TottoriParser のユニットテスト。"""
import pytest

from parsers import PARSERS
from parsers.tottori import TottoriParser


@pytest.fixture
def parser() -> TottoriParser:
    return TottoriParser()


TOTTORI_TOP_HTML = """
<html>
<body>
  <a href="https://sento.tottori.jp/category/sento/">銭湯一覧</a>
  <a href="/category/news/">お知らせ</a>
  <a href="https://example.com/category/sento/">外部</a>
</body>
</html>
"""


TOTTORI_LIST_HTML = """
<html>
<body>
  <article><h2><a href="https://sento.tottori.jp/2025/01/10/tottori-yu/">鳥取湯</a></h2></article>
  <article><h2><a href="/2025/02/01/yonago-yu/">米子湯</a></h2></article>
  <a href="https://sento.tottori.jp/category/sento/">一覧（除外）</a>
  <a href="https://sento.tottori.jp/wp-admin/">管理（除外）</a>
</body>
</html>
"""


TOTTORI_DETAIL_HTML_HAPPY = """
<html>
<body>
  <h1 class="entry-title">鳥取湯</h1>
  <dl>
    <dt>住所</dt><dd>鳥取県鳥取市1-2-3</dd>
    <dt>TEL</dt><dd>0857-12-3456</dd>
    <dt>営業時間</dt><dd>15:00〜23:00</dd>
    <dt>定休日</dt><dd>木曜日</dd>
  </dl>
  <a href="https://www.google.com/maps?q=35.5011,134.2350">地図</a>
</body>
</html>
"""


TOTTORI_DETAIL_HTML_IFRAME = """
<html>
<body>
  <h1>米子湯</h1>
  <dl><dt>住所</dt><dd>鳥取県米子市2-3-4</dd></dl>
  <iframe src="https://www.google.com/maps/embed?pb=!1m18!2d133.3375!3d35.4281"></iframe>
</body>
</html>
"""


TOTTORI_DETAIL_HTML_NO_ADDRESS = """
<html>
<body>
  <h1>住所なし湯</h1>
</body>
</html>
"""


TOTTORI_DETAIL_HTML_NO_NAME = """
<html>
<body>
  <dl><dt>住所</dt><dd>鳥取県倉吉市3-4-5</dd></dl>
</body>
</html>
"""


def test_parse_sento_happy_path(parser: TottoriParser) -> None:
    result = parser.parse_sento(TOTTORI_DETAIL_HTML_HAPPY, "https://sento.tottori.jp/2025/01/10/tottori-yu/")

    assert result is not None
    assert result["name"] == "鳥取湯"
    assert result["address"] == "鳥取県鳥取市1-2-3"
    assert result["phone"] == "0857-12-3456"
    assert result["open_hours"] == "15:00〜23:00"
    assert result["holiday"] == "木曜日"
    assert result["lat"] == pytest.approx(35.5011)
    assert result["lng"] == pytest.approx(134.2350)
    assert result["prefecture"] == "鳥取県"
    assert result["region"] == "中国"
    assert result["facility_type"] == "sento"


def test_parse_sento_extracts_coordinates_from_iframe(parser: TottoriParser) -> None:
    result = parser.parse_sento(TOTTORI_DETAIL_HTML_IFRAME, "https://sento.tottori.jp/2025/02/01/yonago-yu/")
    assert result is not None
    assert result["lat"] == pytest.approx(35.4281)
    assert result["lng"] == pytest.approx(133.3375)


def test_parse_sento_returns_none_when_address_missing(parser: TottoriParser) -> None:
    result = parser.parse_sento(TOTTORI_DETAIL_HTML_NO_ADDRESS, "https://sento.tottori.jp/2025/03/01/no-address/")
    assert result is None


def test_parse_sento_returns_none_when_name_missing(parser: TottoriParser) -> None:
    result = parser.parse_sento(TOTTORI_DETAIL_HTML_NO_NAME, "https://sento.tottori.jp/2025/03/01/no-name/")
    assert result is None


def test_get_all_list_urls_collects_list_pages(parser: TottoriParser) -> None:
    urls = parser.get_all_list_urls(TOTTORI_TOP_HTML)
    assert "https://sento.tottori.jp/" in urls
    assert "https://sento.tottori.jp/category/sento" in urls
    assert "https://sento.tottori.jp/category/news" in urls
    assert all("example.com" not in url for url in urls)


def test_get_item_urls_extracts_detail_urls(parser: TottoriParser) -> None:
    urls = parser.get_item_urls(TOTTORI_LIST_HTML, "https://sento.tottori.jp/category/sento/")
    assert "https://sento.tottori.jp/2025/01/10/tottori-yu" in urls
    assert "https://sento.tottori.jp/2025/02/01/yonago-yu" in urls
    assert all("/category/" not in url for url in urls)
    assert all("/wp-admin" not in url for url in urls)


def test_parsers_contains_tottori() -> None:
    assert "鳥取県" in PARSERS
    assert PARSERS["鳥取県"] is TottoriParser
