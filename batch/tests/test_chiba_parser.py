"""ChibaParser のユニットテスト。"""
import pytest

from parsers.chiba import ChibaParser, _AREA_PAGE_PATTERN


@pytest.fixture
def parser() -> ChibaParser:
    return ChibaParser()


# ---------------------------------------------------------------------------
# parse_sento: ハッピーパス
# ---------------------------------------------------------------------------

CHIBA_DETAIL_HTML_HAPPY = """
<html>
<head><title>千葉湯 | 千葉銭湯</title></head>
<body>
  <h1 class="entry-title">千葉湯</h1>
  <dl>
    <dt>住所</dt><dd>千葉県千葉市中央区1-2-3</dd>
    <dt>TEL</dt><dd>043-123-4567</dd>
    <dt>営業時間</dt><dd>15:00〜23:00</dd>
    <dt>定休日</dt><dd>水曜日</dd>
  </dl>
  <a href="https://www.google.com/maps?q=35.6074,140.1065">地図</a>
</body>
</html>
"""


def test_parse_sento_happy_path(parser: ChibaParser) -> None:
    result = parser.parse_sento(CHIBA_DETAIL_HTML_HAPPY, "https://chiba1126sento.com/2024/01/01/chiba-yu/")

    assert result is not None
    assert result["name"] == "千葉湯"
    assert result["address"] == "千葉県千葉市中央区1-2-3"
    assert result["phone"] == "043-123-4567"
    assert result["open_hours"] == "15:00〜23:00"
    assert result["holiday"] == "水曜日"
    assert result["lat"] == pytest.approx(35.6074)
    assert result["lng"] == pytest.approx(140.1065)
    assert result["prefecture"] == "千葉県"
    assert result["region"] == "関東"
    assert result["facility_type"] == "sento"
    assert result["source_url"] == "https://chiba1126sento.com/2024/01/01/chiba-yu/"


# ---------------------------------------------------------------------------
# parse_sento: Google Maps embed iframe から座標を取得する
# ---------------------------------------------------------------------------

CHIBA_DETAIL_HTML_IFRAME = """
<html>
<body>
  <h1 class="entry-title">船橋湯</h1>
  <dl>
    <dt>住所</dt><dd>千葉県船橋市2-3-4</dd>
  </dl>
  <iframe src="https://www.google.com/maps/embed?pb=!1m18!...!3d35.6940!...!4d139.9830!..."></iframe>
</body>
</html>
"""


def test_parse_sento_coords_from_iframe_embed(parser: ChibaParser) -> None:
    result = parser.parse_sento(CHIBA_DETAIL_HTML_IFRAME, "https://chiba1126sento.com/2024/02/01/funabashi/")
    assert result is not None
    assert result["lat"] == pytest.approx(35.6940)
    assert result["lng"] == pytest.approx(139.9830)


# ---------------------------------------------------------------------------
# parse_sento: エリアページの場合 None を返す
# ---------------------------------------------------------------------------

CHIBA_AREA_HTML = """
<html>
<body>
  <h1>千葉エリア一覧</h1>
  <ul>
    <li><a href="https://chiba1126sento.com/2024/01/01/chiba-yu/">千葉湯</a></li>
    <li><a href="https://chiba1126sento.com/2024/02/01/funabashi/">船橋湯</a></li>
  </ul>
</body>
</html>
"""


def test_parse_sento_returns_none_for_area_page(parser: ChibaParser) -> None:
    result = parser.parse_sento(CHIBA_AREA_HTML, "https://chiba1126sento.com/?page_id=5")
    assert result is None


# ---------------------------------------------------------------------------
# parse_sento: name が取得できない場合 None を返す
# ---------------------------------------------------------------------------

CHIBA_DETAIL_HTML_NO_NAME = """
<html>
<body>
  <p>銭湯情報が見つかりません</p>
</body>
</html>
"""


def test_parse_sento_returns_none_when_name_missing(parser: ChibaParser) -> None:
    result = parser.parse_sento(CHIBA_DETAIL_HTML_NO_NAME, "https://chiba1126sento.com/2024/01/01/unknown/")
    assert result is None


# ---------------------------------------------------------------------------
# get_item_urls: 銭湯個別ページ URL のみを収集し、エリアページを除外する
# ---------------------------------------------------------------------------

CHIBA_TOP_HTML = """
<html>
<body>
  <a href="https://chiba1126sento.com/2024/01/01/sento-a/">銭湯A</a>
  <a href="https://chiba1126sento.com/2024/02/15/sento-b/">銭湯B</a>
  <a href="https://chiba1126sento.com/?page_id=5">エリアページ（除外）</a>
  <a href="https://chiba1126sento.com/?page_id=6">エリアページ2（除外）</a>
  <a href="/wp-admin/">管理（除外）</a>
  <a href="https://example.com/external/">外部（除外）</a>
</body>
</html>
"""


def test_get_item_urls_returns_sento_urls_only(parser: ChibaParser) -> None:
    urls = parser.get_item_urls(CHIBA_TOP_HTML, "https://chiba1126sento.com/")
    assert "https://chiba1126sento.com/2024/01/01/sento-a/" in urls
    assert "https://chiba1126sento.com/2024/02/15/sento-b/" in urls
    # エリアページは含まない
    assert all("page_id" not in u for u in urls)
    # 管理・外部URLは含まない
    assert all("wp-admin" not in u for u in urls)
    assert all("example.com" not in u for u in urls)


def test_get_item_urls_deduplicates(parser: ChibaParser) -> None:
    html = """
    <html><body>
      <a href="https://chiba1126sento.com/2024/01/01/sento-a/">銭湯A</a>
      <a href="https://chiba1126sento.com/2024/01/01/sento-a/">銭湯A（重複）</a>
    </body></html>
    """
    urls = parser.get_item_urls(html, "https://chiba1126sento.com/")
    assert len(urls) == 1


# ---------------------------------------------------------------------------
# get_all_list_urls: トップページからエリアページURLを収集する
# ---------------------------------------------------------------------------

def test_get_all_list_urls_collects_area_pages(parser: ChibaParser) -> None:
    urls = parser.get_all_list_urls(CHIBA_TOP_HTML)
    assert "https://chiba1126sento.com/" in urls
    assert "https://chiba1126sento.com/?page_id=5" in urls
    assert "https://chiba1126sento.com/?page_id=6" in urls


def test_get_all_list_urls_deduplicates(parser: ChibaParser) -> None:
    html = """
    <html><body>
      <a href="https://chiba1126sento.com/?page_id=5">エリア（重複）</a>
      <a href="https://chiba1126sento.com/?page_id=5">エリア（重複）</a>
    </body></html>
    """
    urls = parser.get_all_list_urls(html)
    assert urls.count("https://chiba1126sento.com/?page_id=5") == 1
