"""HokkaidoParser のユニットテスト。"""
import pytest

from parsers.hokkaido import HokkaidoParser


@pytest.fixture
def parser() -> HokkaidoParser:
    return HokkaidoParser()


# ---------------------------------------------------------------------------
# parse_sento: ハッピーパス
# ---------------------------------------------------------------------------

HOKKAIDO_DETAIL_HTML_HAPPY = """
<html>
<head><title>北の湯 | きたの銭湯</title></head>
<body>
  <h1>北の湯</h1>
  <dl>
    <dt>住所</dt><dd>北海道札幌市中央区1-2-3</dd>
    <dt>TEL</dt><dd>011-123-4567</dd>
    <dt>営業時間</dt><dd>14:00〜24:00</dd>
    <dt>定休日</dt><dd>月曜日</dd>
  </dl>
  <a href="https://www.google.com/maps?q=43.0621,141.3544">地図</a>
</body>
</html>
"""


def test_parse_sento_happy_path(parser: HokkaidoParser) -> None:
    result = parser.parse_sento(HOKKAIDO_DETAIL_HTML_HAPPY, "https://www.kita-no-sento.com/sento/kita-no-yu/")

    assert result is not None
    assert result["name"] == "北の湯"
    assert result["address"] == "北海道札幌市中央区1-2-3"
    assert result["phone"] == "011-123-4567"
    assert result["open_hours"] == "14:00〜24:00"
    assert result["holiday"] == "月曜日"
    assert result["lat"] == pytest.approx(43.0621)
    assert result["lng"] == pytest.approx(141.3544)
    assert result["prefecture"] == "北海道"
    assert result["region"] == "北海道"
    assert result["facility_type"] == "sento"
    assert result["source_url"] == "https://www.kita-no-sento.com/sento/kita-no-yu/"


# ---------------------------------------------------------------------------
# parse_sento: iframe の center= パラメータから座標を取得する
# ---------------------------------------------------------------------------

HOKKAIDO_DETAIL_HTML_IFRAME = """
<html>
<body>
  <h1>雪の湯</h1>
  <dl>
    <dt>住所</dt><dd>北海道旭川市2-3-4</dd>
  </dl>
  <iframe src="https://maps.google.com/maps?center=43.7700%2C142.3600&z=15"></iframe>
</body>
</html>
"""


def test_parse_sento_coords_from_iframe_center(parser: HokkaidoParser) -> None:
    result = parser.parse_sento(HOKKAIDO_DETAIL_HTML_IFRAME, "https://www.kita-no-sento.com/sento/yuki/")
    assert result is not None
    assert result["lat"] == pytest.approx(43.7700)
    assert result["lng"] == pytest.approx(142.3600)


# ---------------------------------------------------------------------------
# parse_sento: name が取得できない場合 None を返す
# ---------------------------------------------------------------------------

HOKKAIDO_DETAIL_HTML_NO_NAME = """
<html>
<body>
  <p>ページが見つかりません</p>
</body>
</html>
"""


def test_parse_sento_returns_none_when_name_missing(parser: HokkaidoParser) -> None:
    result = parser.parse_sento(HOKKAIDO_DETAIL_HTML_NO_NAME, "https://www.kita-no-sento.com/sento/missing/")
    assert result is None


# ---------------------------------------------------------------------------
# get_item_urls: /sento/{slug}/ 形式のURLを収集する
# ---------------------------------------------------------------------------

HOKKAIDO_LIST_HTML = """
<html>
<body>
  <a href="/sento/abc-1/">湯1</a>
  <a href="/sento/xyz-2/">湯2</a>
  <a href="https://www.kita-no-sento.com/sento/def-3/">湯3</a>
  <a href="/sentolist/">一覧（除外）</a>
  <a href="/about/">会社概要（除外）</a>
</body>
</html>
"""


def test_get_item_urls_extracts_detail_urls(parser: HokkaidoParser) -> None:
    urls = parser.get_item_urls(HOKKAIDO_LIST_HTML, "https://www.kita-no-sento.com/sentolist/")
    assert "https://www.kita-no-sento.com/sento/abc-1/" in urls
    assert "https://www.kita-no-sento.com/sento/xyz-2/" in urls
    assert "https://www.kita-no-sento.com/sento/def-3/" in urls
    # 一覧ページ自体は除外
    assert all("sentolist" not in u for u in urls)


def test_get_item_urls_deduplicates(parser: HokkaidoParser) -> None:
    html = """
    <html><body>
      <a href="/sento/abc-1/">湯1</a>
      <a href="/sento/abc-1/">湯1（重複）</a>
    </body></html>
    """
    urls = parser.get_item_urls(html, "https://www.kita-no-sento.com/sentolist/")
    assert len(urls) == 1
