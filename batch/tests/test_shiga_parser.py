"""ShigaParser のユニットテスト。"""
import pytest

from parsers.shiga import ShigaParser


@pytest.fixture
def parser() -> ShigaParser:
    return ShigaParser()


def test_get_list_urls(parser: ShigaParser) -> None:
    assert parser.get_list_urls() == ["https://shiga1010.com/"]


SHIGA_LIST_HTML = """
<html>
<body>
  <a href="/sento/otsu-yu/">大津湯</a>
  <a href="https://shiga1010.com/bath/kusatsu-no-yu/">草津の湯</a>
  <a href="/shop/ritto-yu/">栗東湯</a>
  <a href="/list/">一覧ページ（除外）</a>
  <a href="/contact/">お問い合わせ（除外）</a>
  <a href="https://example.com/sento/ext/">外部（除外）</a>
  <a href="/sento/otsu-yu/">大津湯（重複）</a>
</body>
</html>
"""


def test_get_item_urls_collects_detail_urls_only(parser: ShigaParser) -> None:
    urls = parser.get_item_urls(SHIGA_LIST_HTML, "https://shiga1010.com/")
    assert urls == [
        "https://shiga1010.com/sento/otsu-yu/",
        "https://shiga1010.com/bath/kusatsu-no-yu/",
        "https://shiga1010.com/shop/ritto-yu/",
    ]


SHIGA_DETAIL_HTML_HAPPY = """
<html>
<body>
  <h1>大津湯</h1>
  <dl>
    <dt>住所</dt><dd>滋賀県大津市中央1-2-3</dd>
    <dt>TEL</dt><dd>077-123-4567</dd>
    <dt>営業時間</dt><dd>15:00〜23:00</dd>
    <dt>定休日</dt><dd>木曜日</dd>
  </dl>
  <a href="https://www.google.com/maps?q=35.0045,135.8686">地図</a>
</body>
</html>
"""


def test_parse_sento_happy_path(parser: ShigaParser) -> None:
    result = parser.parse_sento(SHIGA_DETAIL_HTML_HAPPY, "https://shiga1010.com/sento/otsu-yu/")

    assert result is not None
    assert result["name"] == "大津湯"
    assert result["address"] == "滋賀県大津市中央1-2-3"
    assert result["phone"] == "077-123-4567"
    assert result["open_hours"] == "15:00〜23:00"
    assert result["holiday"] == "木曜日"
    assert result["lat"] == pytest.approx(35.0045)
    assert result["lng"] == pytest.approx(135.8686)
    assert result["prefecture"] == "滋賀県"
    assert result["region"] == "近畿"
    assert result["facility_type"] == "sento"


SHIGA_DETAIL_HTML_IFRAME = """
<html>
<body>
  <h1>草津の湯</h1>
  <table>
    <tr><th>住所</th><td>滋賀県草津市1-1-1</td></tr>
    <tr><th>電話</th><td>077-987-6543</td></tr>
  </table>
  <iframe src="https://www.google.com/maps/embed?pb=!1m18!2m3!1d0!2d0!3d35.0211!4d135.9599"></iframe>
</body>
</html>
"""


def test_parse_sento_extracts_coords_from_iframe_embed(parser: ShigaParser) -> None:
    result = parser.parse_sento(SHIGA_DETAIL_HTML_IFRAME, "https://shiga1010.com/bath/kusatsu-no-yu/")
    assert result is not None
    assert result["lat"] == pytest.approx(35.0211)
    assert result["lng"] == pytest.approx(135.9599)


SHIGA_DETAIL_HTML_NO_COORDS = """
<html>
<body>
  <h1>守山湯</h1>
  <p>住所：滋賀県守山市2-3-4</p>
  <a href="https://www.google.com/maps/place/%E5%AE%88%E5%B1%B1%E6%B9%AF/">地図</a>
</body>
</html>
"""


def test_parse_sento_returns_none_coords_when_not_available(parser: ShigaParser) -> None:
    result = parser.parse_sento(SHIGA_DETAIL_HTML_NO_COORDS, "https://shiga1010.com/sento/moriyama-yu/")
    assert result is not None
    assert result["lat"] is None
    assert result["lng"] is None


SHIGA_DETAIL_HTML_TITLE_FALLBACK = """
<html>
<head><title>石山湯 | 滋賀県浴場組合</title></head>
<body>
  <p>住所：滋賀県大津市石山寺1-2-3</p>
  <a href="tel:077-111-2222">電話</a>
  <a href="https://www.google.com/maps?destination=34.9800,135.9000">地図</a>
</body>
</html>
"""


def test_parse_sento_uses_title_fallback_for_name(parser: ShigaParser) -> None:
    result = parser.parse_sento(
        SHIGA_DETAIL_HTML_TITLE_FALLBACK,
        "https://shiga1010.com/sento/ishiyama-yu/",
    )
    assert result is not None
    assert result["name"] == "石山湯"
    assert result["phone"] == "077-111-2222"
    assert result["lat"] == pytest.approx(34.9800)
    assert result["lng"] == pytest.approx(135.9000)


def test_parse_sento_returns_none_when_name_missing(parser: ShigaParser) -> None:
    html = "<html><body><p>住所: 滋賀県甲賀市1-2-3</p></body></html>"
    result = parser.parse_sento(html, "https://shiga1010.com/sento/unknown/")
    assert result is None
