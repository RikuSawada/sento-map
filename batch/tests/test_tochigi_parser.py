"""TochigiParser のユニットテスト。"""
import pytest

from parsers import PARSERS
from parsers.tochigi import TochigiParser


@pytest.fixture
def parser() -> TochigiParser:
    return TochigiParser()


TOCHIGI_LIST_HTML = """
<html>
<body>
  <a href="/shop/utsunomiya-yu/">宇都宮湯</a>
  <a href="https://tochigi1010.jp/sento/ashikaga-no-yu/">足利の湯</a>
  <a href="/shoplist/">一覧</a>
  <a href="/news/notice/">お知らせ</a>
  <a href="https://example.com/shop/other/">外部</a>
</body>
</html>
"""


def test_get_list_urls(parser: TochigiParser) -> None:
    assert parser.get_list_urls() == ["https://tochigi1010.jp/shoplist/"]


def test_get_item_urls_extracts_detail_links(parser: TochigiParser) -> None:
    urls = parser.get_item_urls(TOCHIGI_LIST_HTML, "https://tochigi1010.jp/shoplist/")
    assert "https://tochigi1010.jp/shop/utsunomiya-yu/" in urls
    assert "https://tochigi1010.jp/sento/ashikaga-no-yu/" in urls
    assert all("example.com" not in u for u in urls)
    assert all("/shoplist/" not in u for u in urls)


def test_get_item_urls_deduplicates(parser: TochigiParser) -> None:
    html = """
    <html><body>
      <a href="/shop/utsunomiya-yu/">A</a>
      <a href="/shop/utsunomiya-yu/">A duplicate</a>
    </body></html>
    """
    urls = parser.get_item_urls(html, "https://tochigi1010.jp/shoplist/")
    assert len(urls) == 1


TOCHIGI_DETAIL_HTML_HAPPY = """
<html>
<body>
  <h1 class="entry-title">宇都宮湯</h1>
  <dl>
    <dt>住所</dt><dd>栃木県宇都宮市1-2-3</dd>
    <dt>TEL</dt><dd>028-111-2222</dd>
    <dt>営業時間</dt><dd>15:00〜23:00</dd>
    <dt>定休日</dt><dd>月曜日</dd>
  </dl>
  <a href="https://www.google.com/maps?q=36.5551,139.8828">地図</a>
</body>
</html>
"""


def test_parse_sento_happy_path(parser: TochigiParser) -> None:
    url = "https://tochigi1010.jp/shop/utsunomiya-yu/"
    result = parser.parse_sento(TOCHIGI_DETAIL_HTML_HAPPY, url)

    assert result is not None
    assert result["name"] == "宇都宮湯"
    assert result["address"] == "栃木県宇都宮市1-2-3"
    assert result["phone"] == "028-111-2222"
    assert result["open_hours"] == "15:00〜23:00"
    assert result["holiday"] == "月曜日"
    assert result["lat"] == pytest.approx(36.5551)
    assert result["lng"] == pytest.approx(139.8828)
    assert result["prefecture"] == "栃木県"
    assert result["region"] == "関東"
    assert result["facility_type"] == "sento"
    assert result["source_url"] == url


TOCHIGI_DETAIL_HTML_DESTINATION = """
<html>
<body>
  <h1>足利の湯</h1>
  <table>
    <tr><th>住所</th><td>栃木県足利市2-3-4</td></tr>
    <tr><th>電話</th><td>0284-11-3333</td></tr>
    <tr><th>営業時間</th><td>14:00〜22:00</td></tr>
    <tr><th>休業日</th><td>火曜日</td></tr>
  </table>
  <a href="https://www.google.com/maps?destination=36.3380,139.4497">地図</a>
</body>
</html>
"""


def test_parse_sento_extracts_destination_coords(parser: TochigiParser) -> None:
    result = parser.parse_sento(TOCHIGI_DETAIL_HTML_DESTINATION, "https://tochigi1010.jp/sento/ashikaga-no-yu/")
    assert result is not None
    assert result["lat"] == pytest.approx(36.3380)
    assert result["lng"] == pytest.approx(139.4497)
    assert result["holiday"] == "火曜日"


TOCHIGI_DETAIL_HTML_TEL_AND_NO_MAP = """
<html>
<body>
  <h1>小山湯</h1>
  <p>住所: 栃木県小山市5-6-7</p>
  <a href="tel:0285-55-6666">電話</a>
</body>
</html>
"""


def test_parse_sento_tel_link_and_osm_fallback_none(parser: TochigiParser) -> None:
    result = parser.parse_sento(TOCHIGI_DETAIL_HTML_TEL_AND_NO_MAP, "https://tochigi1010.jp/shop/oyama-yu/")
    assert result is not None
    assert result["phone"] == "0285-55-6666"
    assert result["lat"] is None
    assert result["lng"] is None


def test_parse_sento_returns_none_when_name_missing(parser: TochigiParser) -> None:
    html = "<html><body><p>情報なし</p></body></html>"
    result = parser.parse_sento(html, "https://tochigi1010.jp/shop/unknown/")
    assert result is None


def test_parsers_register_tochigi() -> None:
    assert "栃木県" in PARSERS
    assert PARSERS["栃木県"] is TochigiParser
