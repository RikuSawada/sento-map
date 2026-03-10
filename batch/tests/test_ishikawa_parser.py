"""IshikawaParser のユニットテスト。"""
import pytest

from parsers.ishikawa import IshikawaParser


@pytest.fixture
def parser() -> IshikawaParser:
    return IshikawaParser()


def test_get_list_urls(parser: IshikawaParser) -> None:
    assert parser.get_list_urls() == ["https://ishikawa1010.com/bath"]


ISHIKAWA_LIST_HTML_DATA_ATTR = """
<html>
<body>
  <a href="/bath/21" data-lat="36.5610" data-lng="136.6562">松の湯</a>
  <a href="https://ishikawa1010.com/bath/22/" data-lat="36.5700" data-lng="136.6600">梅の湯</a>
  <a href="/bath/21">松の湯（重複）</a>
  <a href="/bath">一覧</a>
</body>
</html>
"""


def test_get_item_urls_extracts_and_deduplicates(parser: IshikawaParser) -> None:
    urls = parser.get_item_urls(ISHIKAWA_LIST_HTML_DATA_ATTR, "https://ishikawa1010.com/bath")
    assert urls == [
        "https://ishikawa1010.com/bath/21/",
        "https://ishikawa1010.com/bath/22/",
    ]


def test_get_item_urls_caches_coords_from_data_attrs(parser: IshikawaParser) -> None:
    parser.get_item_urls(ISHIKAWA_LIST_HTML_DATA_ATTR, "https://ishikawa1010.com/bath")

    assert parser._coord_cache["https://ishikawa1010.com/bath/21/"] == pytest.approx((36.5610, 136.6562))
    assert parser._coord_cache["https://ishikawa1010.com/bath/22/"] == pytest.approx((36.5700, 136.6600))


ISHIKAWA_LIST_HTML_JS = """
<html>
<body>
  <script>
    const sentoMarkers = [
      { "url": "/bath/31", "lat": "36.5801", "lng": "136.6702" },
      { "link": "/bath/32", "mapUrl": "https://www.google.com/maps?q=36.5903,136.6804" }
    ];
  </script>
</body>
</html>
"""


def test_get_item_urls_extracts_urls_and_coords_from_js(parser: IshikawaParser) -> None:
    urls = parser.get_item_urls(ISHIKAWA_LIST_HTML_JS, "https://ishikawa1010.com/bath")

    assert "https://ishikawa1010.com/bath/31/" in urls
    assert "https://ishikawa1010.com/bath/32/" in urls
    assert parser._coord_cache["https://ishikawa1010.com/bath/31/"] == pytest.approx((36.5801, 136.6702))
    assert parser._coord_cache["https://ishikawa1010.com/bath/32/"] == pytest.approx((36.5903, 136.6804))


ISHIKAWA_DETAIL_HTML_HAPPY = """
<html>
<body>
  <h1>松の湯</h1>
  <dl>
    <dt>住所</dt><dd>石川県金沢市1-2-3</dd>
    <dt>TEL</dt><dd>076-111-2222</dd>
    <dt>営業時間</dt><dd>14:00〜23:00</dd>
    <dt>定休日</dt><dd>月曜日</dd>
  </dl>
</body>
</html>
"""


def test_parse_sento_uses_cached_coords(parser: IshikawaParser) -> None:
    url = "https://ishikawa1010.com/bath/21/"
    parser._coord_cache[url] = (36.5610, 136.6562)

    result = parser.parse_sento(ISHIKAWA_DETAIL_HTML_HAPPY, url)

    assert result is not None
    assert result["name"] == "松の湯"
    assert result["address"] == "石川県金沢市1-2-3"
    assert result["phone"] == "076-111-2222"
    assert result["open_hours"] == "14:00〜23:00"
    assert result["holiday"] == "月曜日"
    assert result["lat"] == pytest.approx(36.5610)
    assert result["lng"] == pytest.approx(136.6562)
    assert result["prefecture"] == "石川県"
    assert result["region"] == "中部"
    assert result["facility_type"] == "sento"
    assert result["source_url"] == url


ISHIKAWA_DETAIL_HTML_IFRAME = """
<html>
<body>
  <h1>竹の湯</h1>
  <dl><dt>住所</dt><dd>石川県金沢市4-5-6</dd></dl>
  <iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d1012!2d136.7000!3d36.6000"></iframe>
</body>
</html>
"""


def test_parse_sento_extracts_coords_from_google_embed(parser: IshikawaParser) -> None:
    result = parser.parse_sento(ISHIKAWA_DETAIL_HTML_IFRAME, "https://ishikawa1010.com/bath/40")
    assert result is not None
    assert result["lat"] == pytest.approx(36.6000)
    assert result["lng"] == pytest.approx(136.7000)


ISHIKAWA_DETAIL_HTML_JS_COORDS = """
<html>
<body>
  <h2>桜の湯</h2>
  <dl><dt>住所</dt><dd>石川県小松市7-8-9</dd></dl>
  <script>
    window.sentoPoint = { lat: 36.6123, lng: 136.7123 };
  </script>
</body>
</html>
"""


def test_parse_sento_extracts_coords_from_js_variable(parser: IshikawaParser) -> None:
    result = parser.parse_sento(ISHIKAWA_DETAIL_HTML_JS_COORDS, "https://ishikawa1010.com/bath/41")
    assert result is not None
    assert result["lat"] == pytest.approx(36.6123)
    assert result["lng"] == pytest.approx(136.7123)


def test_parse_sento_returns_none_when_name_missing(parser: IshikawaParser) -> None:
    html = """
    <html><body><p>情報なし</p></body></html>
    """
    assert parser.parse_sento(html, "https://ishikawa1010.com/bath/99") is None


def test_parse_sento_keeps_lat_lng_none_when_not_found(parser: IshikawaParser) -> None:
    html = """
    <html>
    <body>
      <h1>謎の湯</h1>
      <dl><dt>住所</dt><dd>石川県白山市1-1</dd></dl>
    </body>
    </html>
    """
    result = parser.parse_sento(html, "https://ishikawa1010.com/bath/42")
    assert result is not None
    assert result["lat"] is None
    assert result["lng"] is None
