"""KanagawaParser のユニットテスト。"""
import pytest

from parsers.kanagawa import KanagawaParser, AREA_LIST_URLS


@pytest.fixture
def parser() -> KanagawaParser:
    return KanagawaParser()


# ---------------------------------------------------------------------------
# get_list_urls
# ---------------------------------------------------------------------------

def test_get_list_urls_returns_three_areas(parser: KanagawaParser) -> None:
    urls = parser.get_list_urls()
    assert len(urls) == 3
    assert any("yokohama" in u for u in urls)
    assert any("kawasaki" in u for u in urls)
    assert any("shonan" in u for u in urls)


# ---------------------------------------------------------------------------
# get_item_urls
# ---------------------------------------------------------------------------

KANAGAWA_LIST_HTML = """
<html>
<body>
  <a href="/koten/tsurumi-yu/">鶴見湯</a>
  <a href="/koten/sakura-yu/">さくら湯</a>
  <a href="https://k-o-i.jp/koten/hama-yu/">浜湯</a>
  <a href="/search_area/yokohama/">横浜エリア一覧</a>
  <a href="/other/page/">関係ないリンク</a>
</body>
</html>
"""


def test_get_item_urls_extracts_koten_urls(parser: KanagawaParser) -> None:
    urls = parser.get_item_urls(KANAGAWA_LIST_HTML, "https://k-o-i.jp/search_area/yokohama/")
    assert len(urls) == 3
    assert "https://k-o-i.jp/koten/tsurumi-yu/" in urls
    assert "https://k-o-i.jp/koten/sakura-yu/" in urls
    assert "https://k-o-i.jp/koten/hama-yu/" in urls


def test_get_item_urls_no_duplicates(parser: KanagawaParser) -> None:
    html = """
    <html><body>
      <a href="/koten/tsurumi-yu/">鶴見湯</a>
      <a href="/koten/tsurumi-yu/">鶴見湯（重複）</a>
    </body></html>
    """
    urls = parser.get_item_urls(html, "https://k-o-i.jp/search_area/yokohama/")
    assert urls.count("https://k-o-i.jp/koten/tsurumi-yu/") == 1


# ---------------------------------------------------------------------------
# parse_sento: ハッピーパス
# ---------------------------------------------------------------------------

KANAGAWA_DETAIL_HTML_HAPPY = """
<html>
<body>
  <h1 class="koten-name">鶴見湯</h1>
  <dl>
    <dt>住所</dt><dd>神奈川県横浜市鶴見区1-2-3</dd>
    <dt>TEL</dt><dd>045-111-2222</dd>
    <dt>営業時間</dt><dd>15:00〜23:00</dd>
    <dt>定休日</dt><dd>水曜日</dd>
  </dl>
  <a href="https://www.google.com/maps?q=35.5100,139.6800">地図</a>
</body>
</html>
"""


def test_parse_sento_happy_path(parser: KanagawaParser) -> None:
    result = parser.parse_sento(KANAGAWA_DETAIL_HTML_HAPPY, "https://k-o-i.jp/koten/tsurumi-yu/")

    assert result is not None
    assert result["name"] == "鶴見湯"
    assert result["address"] == "神奈川県横浜市鶴見区1-2-3"
    assert result["phone"] == "045-111-2222"
    assert result["open_hours"] == "15:00〜23:00"
    assert result["holiday"] == "水曜日"
    assert result["lat"] == pytest.approx(35.5100)
    assert result["lng"] == pytest.approx(139.6800)
    assert result["prefecture"] == "神奈川県"
    assert result["region"] == "関東"
    assert result["facility_type"] == "sento"
    assert result["source_url"] == "https://k-o-i.jp/koten/tsurumi-yu/"


# ---------------------------------------------------------------------------
# parse_sento: name が取得できない場合 None を返す
# ---------------------------------------------------------------------------

KANAGAWA_DETAIL_HTML_NO_NAME = """
<html>
<body>
  <p>情報なし</p>
</body>
</html>
"""


def test_parse_sento_returns_none_when_name_missing(parser: KanagawaParser) -> None:
    result = parser.parse_sento(KANAGAWA_DETAIL_HTML_NO_NAME, "https://k-o-i.jp/koten/unknown/")
    assert result is None


# ---------------------------------------------------------------------------
# parse_sento: tel: リンクから電話番号を取得する
# ---------------------------------------------------------------------------

KANAGAWA_DETAIL_HTML_TEL_LINK = """
<html>
<body>
  <h1>さくら湯</h1>
  <dl>
    <dt>住所</dt><dd>神奈川県川崎市川崎区4-5-6</dd>
  </dl>
  <a href="tel:044-333-4444">電話する</a>
  <a href="https://www.google.com/maps?destination=35.5200,139.7000">地図</a>
</body>
</html>
"""


def test_parse_sento_extracts_phone_from_tel_link(parser: KanagawaParser) -> None:
    result = parser.parse_sento(KANAGAWA_DETAIL_HTML_TEL_LINK, "https://k-o-i.jp/koten/sakura-yu/")
    assert result is not None
    assert result["phone"] == "044-333-4444"
    assert result["lat"] == pytest.approx(35.5200)
    assert result["lng"] == pytest.approx(139.7000)


# ---------------------------------------------------------------------------
# parse_sento: Google Maps iframe から座標を取得する
# ---------------------------------------------------------------------------

KANAGAWA_DETAIL_HTML_IFRAME = """
<html>
<body>
  <h1>浜湯</h1>
  <dl>
    <dt>住所</dt><dd>神奈川県横浜市中区7-8-9</dd>
  </dl>
  <iframe src="https://www.google.com/maps/embed?ll=35.4500,139.6400&z=16"></iframe>
</body>
</html>
"""


def test_parse_sento_extracts_coords_from_iframe(parser: KanagawaParser) -> None:
    result = parser.parse_sento(KANAGAWA_DETAIL_HTML_IFRAME, "https://k-o-i.jp/koten/hama-yu/")
    assert result is not None
    assert result["lat"] == pytest.approx(35.4500)
    assert result["lng"] == pytest.approx(139.6400)


# ---------------------------------------------------------------------------
# parse_sento: 座標がない場合は None のまま返る（エラーにならない）
# ---------------------------------------------------------------------------

KANAGAWA_DETAIL_HTML_NO_COORDS = """
<html>
<body>
  <h1>謎の湯</h1>
  <dl>
    <dt>住所</dt><dd>神奈川県相模原市1-1-1</dd>
  </dl>
</body>
</html>
"""


def test_parse_sento_no_coords_returns_dict_with_none(parser: KanagawaParser) -> None:
    result = parser.parse_sento(KANAGAWA_DETAIL_HTML_NO_COORDS, "https://k-o-i.jp/koten/nazo-yu/")
    assert result is not None
    assert result["lat"] is None
    assert result["lng"] is None
