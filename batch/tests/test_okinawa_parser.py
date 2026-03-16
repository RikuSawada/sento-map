"""OkinawaParser のユニットテスト。"""
import pytest

from parsers import PARSERS
from parsers.okinawa import OkinawaParser


@pytest.fixture
def parser() -> OkinawaParser:
    return OkinawaParser()


OKINAWA_TOP_HTML = """
<html>
<body>
  <a href="https://okinawa-sento.jp/category/sento/">銭湯一覧</a>
  <a href="/category/news/">お知らせ</a>
  <a href="https://example.com/category/sento/">外部</a>
</body>
</html>
"""


OKINAWA_LIST_HTML = """
<html>
<body>
  <article><h2><a href="https://okinawa-sento.jp/2025/01/10/naha-yu/">那覇湯</a></h2></article>
  <article><h2><a href="/2025/02/01/uruma-yu/">うるま湯</a></h2></article>
  <a href="https://okinawa-sento.jp/category/sento/">一覧（除外）</a>
  <a href="https://okinawa-sento.jp/wp-admin/">管理（除外）</a>
</body>
</html>
"""


OKINAWA_DETAIL_HTML_HAPPY = """
<html>
<body>
  <h1 class="entry-title">那覇湯</h1>
  <dl>
    <dt>住所</dt><dd>沖縄県那覇市1-2-3</dd>
    <dt>TEL</dt><dd>098-123-4567</dd>
    <dt>営業時間</dt><dd>15:00〜23:00</dd>
    <dt>定休日</dt><dd>火曜日</dd>
  </dl>
  <a href="https://www.google.com/maps?q=26.2124,127.6809">地図</a>
</body>
</html>
"""


OKINAWA_DETAIL_HTML_IFRAME = """
<html>
<body>
  <h1>うるま湯</h1>
  <dl><dt>住所</dt><dd>沖縄県うるま市2-3-4</dd></dl>
  <iframe src="https://www.google.com/maps/embed?pb=!1m18!2d127.8575!3d26.3344"></iframe>
</body>
</html>
"""


OKINAWA_DETAIL_HTML_NO_ADDRESS = """
<html>
<body>
  <h1>住所なし湯</h1>
</body>
</html>
"""


OKINAWA_DETAIL_HTML_NO_NAME = """
<html>
<body>
  <dl><dt>住所</dt><dd>沖縄県沖縄市3-4-5</dd></dl>
</body>
</html>
"""


def test_parse_sento_happy_path(parser: OkinawaParser) -> None:
    result = parser.parse_sento(OKINAWA_DETAIL_HTML_HAPPY, "https://okinawa-sento.jp/2025/01/10/naha-yu/")

    assert result is not None
    assert result["name"] == "那覇湯"
    assert result["address"] == "沖縄県那覇市1-2-3"
    assert result["phone"] == "098-123-4567"
    assert result["open_hours"] == "15:00〜23:00"
    assert result["holiday"] == "火曜日"
    assert result["lat"] == pytest.approx(26.2124)
    assert result["lng"] == pytest.approx(127.6809)
    assert result["prefecture"] == "沖縄県"
    assert result["region"] == "九州"
    assert result["facility_type"] == "sento"


def test_parse_sento_extracts_coordinates_from_iframe(parser: OkinawaParser) -> None:
    result = parser.parse_sento(OKINAWA_DETAIL_HTML_IFRAME, "https://okinawa-sento.jp/2025/02/01/uruma-yu/")
    assert result is not None
    assert result["lat"] == pytest.approx(26.3344)
    assert result["lng"] == pytest.approx(127.8575)


def test_parse_sento_returns_none_when_address_missing(parser: OkinawaParser) -> None:
    result = parser.parse_sento(OKINAWA_DETAIL_HTML_NO_ADDRESS, "https://okinawa-sento.jp/2025/03/01/no-address/")
    assert result is None


def test_parse_sento_returns_none_when_name_missing(parser: OkinawaParser) -> None:
    result = parser.parse_sento(OKINAWA_DETAIL_HTML_NO_NAME, "https://okinawa-sento.jp/2025/03/01/no-name/")
    assert result is None


def test_get_all_list_urls_collects_list_pages(parser: OkinawaParser) -> None:
    urls = parser.get_all_list_urls(OKINAWA_TOP_HTML)
    assert "https://okinawa-sento.jp/" in urls
    assert "https://okinawa-sento.jp/category/sento" in urls
    assert "https://okinawa-sento.jp/category/news" in urls
    assert all("example.com" not in url for url in urls)


def test_get_item_urls_extracts_detail_urls(parser: OkinawaParser) -> None:
    urls = parser.get_item_urls(OKINAWA_LIST_HTML, "https://okinawa-sento.jp/category/sento/")
    assert "https://okinawa-sento.jp/2025/01/10/naha-yu" in urls
    assert "https://okinawa-sento.jp/2025/02/01/uruma-yu" in urls
    assert all("/category/" not in url for url in urls)
    assert all("/wp-admin" not in url for url in urls)


def test_parsers_contains_okinawa() -> None:
    assert "沖縄県" in PARSERS
    assert PARSERS["沖縄県"] is OkinawaParser
