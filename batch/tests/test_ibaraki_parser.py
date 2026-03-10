"""IbarakiParser のユニットテスト。"""
import pytest

from parsers.ibaraki import IbarakiParser


@pytest.fixture
def parser() -> IbarakiParser:
    return IbarakiParser()


IBARAKI_DETAIL_HTML_HAPPY = """
<html>
<body>
  <h1>みと湯</h1>
  <dl>
    <dt>住所</dt><dd>茨城県水戸市中央1-2-3</dd>
    <dt>TEL</dt><dd>029-123-4567</dd>
    <dt>営業時間</dt><dd>15:00〜23:00</dd>
    <dt>定休日</dt><dd>月曜日</dd>
  </dl>
  <a href="https://www.google.com/maps?q=36.3658,140.4712">地図</a>
</body>
</html>
"""


def test_parse_sento_happy_path(parser: IbarakiParser) -> None:
    result = parser.parse_sento(IBARAKI_DETAIL_HTML_HAPPY, "https://ibaraki1010.com/sento/mitoyu/")

    assert result is not None
    assert result["name"] == "みと湯"
    assert result["address"] == "茨城県水戸市中央1-2-3"
    assert result["phone"] == "029-123-4567"
    assert result["open_hours"] == "15:00〜23:00"
    assert result["holiday"] == "月曜日"
    assert result["lat"] == pytest.approx(36.3658)
    assert result["lng"] == pytest.approx(140.4712)
    assert result["prefecture"] == "茨城県"
    assert result["region"] == "関東"
    assert result["facility_type"] == "sento"


IBARAKI_DETAIL_HTML_MAPS_AT = """
<html>
<body>
  <h1>つくば湯</h1>
  <p>住所：茨城県つくば市研究学園1-1-1</p>
  <a href="https://www.google.com/maps/place/%E3%81%A4%E3%81%8F%E3%81%B0%E6%B9%AF/@36.0839,140.0765,17z">地図</a>
</body>
</html>
"""


def test_parse_sento_coords_from_maps_at_path(parser: IbarakiParser) -> None:
    result = parser.parse_sento(IBARAKI_DETAIL_HTML_MAPS_AT, "https://ibaraki1010.com/sento/tsukuba/")
    assert result is not None
    assert result["address"] == "茨城県つくば市研究学園1-1-1"
    assert result["lat"] == pytest.approx(36.0839)
    assert result["lng"] == pytest.approx(140.0765)


IBARAKI_DETAIL_HTML_NO_COORDS = """
<html>
<body>
  <h1>ひたち湯</h1>
  <dl>
    <dt>住所</dt><dd>茨城県日立市幸町2-2-2</dd>
  </dl>
</body>
</html>
"""


def test_parse_sento_without_maps_link_returns_none_coords(parser: IbarakiParser) -> None:
    result = parser.parse_sento(IBARAKI_DETAIL_HTML_NO_COORDS, "https://ibaraki1010.com/sento/hitachi/")
    assert result is not None
    assert result["lat"] is None
    assert result["lng"] is None


IBARAKI_DETAIL_HTML_TEL_LINK_TABLE = """
<html>
<body>
  <h1>土浦湯</h1>
  <table>
    <tr><th>所在地</th><td>茨城県土浦市桜町3-3-3</td></tr>
    <tr><th>入浴時間</th><td>16:00〜22:30</td></tr>
    <tr><th>休業日</th><td>木曜日</td></tr>
  </table>
  <a href="tel:029-222-3333">電話する</a>
</body>
</html>
"""


def test_parse_sento_extracts_table_and_tel_link(parser: IbarakiParser) -> None:
    result = parser.parse_sento(IBARAKI_DETAIL_HTML_TEL_LINK_TABLE, "https://ibaraki1010.com/sento/tsuchiura/")
    assert result is not None
    assert result["address"] == "茨城県土浦市桜町3-3-3"
    assert result["phone"] == "029-222-3333"
    assert result["open_hours"] == "16:00〜22:30"
    assert result["holiday"] == "木曜日"


IBARAKI_DETAIL_HTML_NO_NAME = """
<html>
<body>
  <p>店舗情報</p>
  <p>住所：茨城県水戸市</p>
</body>
</html>
"""


def test_parse_sento_returns_none_when_name_missing(parser: IbarakiParser) -> None:
    result = parser.parse_sento(IBARAKI_DETAIL_HTML_NO_NAME, "https://ibaraki1010.com/sento/unknown/")
    assert result is None


IBARAKI_LIST_HTML = """
<html>
<body>
  <a href="/shop/mitoyu/">みと湯</a>
  <a href="https://ibaraki1010.com/sento/tsukuba/">つくば湯</a>
  <a href="/news/2026/">ニュース（除外）</a>
  <a href="/contact/">お問い合わせ（除外）</a>
  <a href="https://example.com/sento/ext/">外部（除外）</a>
  <a href="mailto:test@example.com">メール（除外）</a>
  <a href="/shop/mitoyu/">重複</a>
</body>
</html>
"""


def test_get_item_urls_extracts_internal_detail_urls_only(parser: IbarakiParser) -> None:
    urls = parser.get_item_urls(IBARAKI_LIST_HTML, "https://ibaraki1010.com/")
    assert "https://ibaraki1010.com/shop/mitoyu/" in urls
    assert "https://ibaraki1010.com/sento/tsukuba/" in urls
    assert all("/news/" not in url for url in urls)
    assert all("/contact/" not in url for url in urls)
    assert all("example.com" not in url for url in urls)


def test_get_item_urls_deduplicates(parser: IbarakiParser) -> None:
    urls = parser.get_item_urls(IBARAKI_LIST_HTML, "https://ibaraki1010.com/")
    assert urls.count("https://ibaraki1010.com/shop/mitoyu/") == 1


def test_get_list_urls(parser: IbarakiParser) -> None:
    assert parser.get_list_urls() == ["https://ibaraki1010.com/"]
