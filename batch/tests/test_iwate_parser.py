"""IwateParser のユニットテスト。"""
import pytest

from parsers import PARSERS
from parsers.iwate import IwateParser, LIST_URL


@pytest.fixture
def parser() -> IwateParser:
    return IwateParser()


def test_parsers_registry_contains_iwate() -> None:
    assert "岩手県" in PARSERS
    assert PARSERS["岩手県"] is IwateParser


def test_get_list_urls(parser: IwateParser) -> None:
    assert parser.get_list_urls() == [LIST_URL]


IWATE_LIST_HTML = """
<html><body>
  <a href="/iwate/yokujou/store-a.html">盛岡湯</a>
  <a href="https://www.seiei.or.jp/iwate/yokujou/store-b.html">花巻湯</a>
  <a href="/iwate/store-c.html">施設C</a>
  <a href="/iwate/yokujou/store-a.html">盛岡湯(重複)</a>
  <a href="https://www.google.com/maps?q=39.7036,141.1527">外部地図（除外）</a>
  <a href="/iwate/oshirase.html">お知らせ（除外）</a>
  <a href="/iwate/yokujou.pdf">PDF（除外）</a>
</body></html>
"""


def test_get_item_urls_extracts_detail_links(parser: IwateParser) -> None:
    urls = parser.get_item_urls(IWATE_LIST_HTML, LIST_URL)

    assert "https://www.seiei.or.jp/iwate/yokujou/store-a.html" in urls
    assert "https://www.seiei.or.jp/iwate/yokujou/store-b.html" in urls
    assert "https://www.seiei.or.jp/iwate/store-c.html" in urls
    assert len(urls) == 3


IWATE_DETAIL_HTML_HAPPY = """
<html><body>
  <h1>盛岡湯</h1>
  <dl>
    <dt>住所</dt><dd>岩手県盛岡市中央通1-2-3</dd>
    <dt>TEL</dt><dd>019-123-4567</dd>
    <dt>営業時間</dt><dd>14:00〜22:00</dd>
    <dt>定休日</dt><dd>月曜日</dd>
  </dl>
  <a href="https://www.google.com/maps?q=39.7036,141.1527">地図</a>
</body></html>
"""


def test_parse_sento_happy_path(parser: IwateParser) -> None:
    url = "https://www.seiei.or.jp/iwate/yokujou/store-a.html"
    result = parser.parse_sento(IWATE_DETAIL_HTML_HAPPY, url)

    assert result is not None
    assert result["name"] == "盛岡湯"
    assert result["address"] == "岩手県盛岡市中央通1-2-3"
    assert result["phone"] == "019-123-4567"
    assert result["open_hours"] == "14:00〜22:00"
    assert result["holiday"] == "月曜日"
    assert result["lat"] == pytest.approx(39.7036)
    assert result["lng"] == pytest.approx(141.1527)
    assert result["prefecture"] == "岩手県"
    assert result["region"] == "東北"
    assert result["facility_type"] == "sento"
    assert result["source_url"] == url


IWATE_DETAIL_HTML_NO_COORDS = """
<html><body>
  <h1>花巻湯</h1>
  <table>
    <tr><th>住所</th><td>岩手県花巻市末広町4-5-6</td></tr>
    <tr><th>電話</th><td>0198-12-3456</td></tr>
  </table>
</body></html>
"""


def test_parse_sento_without_coords_returns_none_lat_lng(parser: IwateParser) -> None:
    result = parser.parse_sento(
        IWATE_DETAIL_HTML_NO_COORDS,
        "https://www.seiei.or.jp/iwate/yokujou/store-b.html",
    )

    assert result is not None
    assert result["lat"] is None
    assert result["lng"] is None


IWATE_DETAIL_HTML_MISSING_REQUIRED = """
<html><body>
  <h1>見出しのみ</h1>
  <p>住所情報がありません</p>
</body></html>
"""


def test_parse_sento_returns_none_when_required_missing(parser: IwateParser) -> None:
    result = parser.parse_sento(
        IWATE_DETAIL_HTML_MISSING_REQUIRED,
        "https://www.seiei.or.jp/iwate/yokujou/unknown.html",
    )

    assert result is None


IWATE_DETAIL_HTML_IFRAME_COORDS = """
<html><body>
  <h1>一関湯</h1>
  <p>住所：岩手県一関市1-2-3</p>
  <iframe src="https://www.google.com/maps/embed?pb=!1m18!...!3d38.9340!...!4d141.1300!..."></iframe>
</body></html>
"""


def test_parse_sento_extracts_coords_from_iframe(parser: IwateParser) -> None:
    result = parser.parse_sento(
        IWATE_DETAIL_HTML_IFRAME_COORDS,
        "https://www.seiei.or.jp/iwate/store-c.html",
    )

    assert result is not None
    assert result["address"] == "岩手県一関市1-2-3"
    assert result["lat"] == pytest.approx(38.9340)
    assert result["lng"] == pytest.approx(141.1300)
