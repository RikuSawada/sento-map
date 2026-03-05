"""SaitamaParser のユニットテスト。"""
import pytest

from parsers.saitama import SaitamaParser


@pytest.fixture
def parser() -> SaitamaParser:
    return SaitamaParser()


# ---------------------------------------------------------------------------
# parse_sento: ハッピーパス
# ---------------------------------------------------------------------------

SAITAMA_DETAIL_HTML_HAPPY = """
<html>
<head><title>さいたま湯 | 彩浴</title></head>
<body>
  <h1>さいたま湯</h1>
  <dl>
    <dt>住所</dt><dd>埼玉県さいたま市浦和区1-2-3</dd>
    <dt>TEL</dt><dd>048-123-4567</dd>
    <dt>営業時間</dt><dd>15:00〜23:00</dd>
    <dt>定休日</dt><dd>火曜日</dd>
  </dl>
  <a href="https://www.google.com/maps?q=35.8617,139.6455">地図</a>
</body>
</html>
"""


def test_parse_sento_happy_path(parser: SaitamaParser) -> None:
    result = parser.parse_sento(SAITAMA_DETAIL_HTML_HAPPY, "https://saiyoku.jp/id-1/42/")

    assert result is not None
    assert result["name"] == "さいたま湯"
    assert result["address"] == "埼玉県さいたま市浦和区1-2-3"
    assert result["phone"] == "048-123-4567"
    assert result["open_hours"] == "15:00〜23:00"
    assert result["holiday"] == "火曜日"
    assert result["lat"] == pytest.approx(35.8617)
    assert result["lng"] == pytest.approx(139.6455)
    assert result["prefecture"] == "埼玉県"
    assert result["region"] == "関東"
    assert result["facility_type"] == "sento"
    assert result["source_url"] == "https://saiyoku.jp/id-1/42/"


# ---------------------------------------------------------------------------
# parse_sento: name が取得できない場合 None を返す
# ---------------------------------------------------------------------------

SAITAMA_DETAIL_HTML_NO_NAME = """
<html>
<body>
  <p>銭湯情報が見つかりません</p>
</body>
</html>
"""


def test_parse_sento_returns_none_when_name_missing(parser: SaitamaParser) -> None:
    result = parser.parse_sento(SAITAMA_DETAIL_HTML_NO_NAME, "https://saiyoku.jp/id-1/99/")
    assert result is None


# ---------------------------------------------------------------------------
# parse_sento: lat/lng が取得できない場合は None のまま返す
# ---------------------------------------------------------------------------

SAITAMA_DETAIL_HTML_NO_COORDS = """
<html>
<body>
  <h1>川口湯</h1>
  <dl>
    <dt>住所</dt><dd>埼玉県川口市2-3-4</dd>
  </dl>
</body>
</html>
"""


def test_parse_sento_without_coords(parser: SaitamaParser) -> None:
    result = parser.parse_sento(SAITAMA_DETAIL_HTML_NO_COORDS, "https://saiyoku.jp/id-1/10/")
    assert result is not None
    assert result["name"] == "川口湯"
    assert result["lat"] is None
    assert result["lng"] is None


# ---------------------------------------------------------------------------
# get_item_urls: /id-1/{ID}/ パターンの URL を収集する
# ---------------------------------------------------------------------------

SAITAMA_LIST_HTML = """
<html>
<body>
  <a href="/id-1/1/">湯1</a>
  <a href="/id-1/2/">湯2</a>
  <a href="https://saiyoku.jp/id-1/3/">湯3</a>
  <a href="/about/">会社概要</a>
  <a href="https://example.com/id-1/4/">外部リンク</a>
</body>
</html>
"""


def test_get_item_urls_extracts_detail_urls(parser: SaitamaParser) -> None:
    urls = parser.get_item_urls(SAITAMA_LIST_HTML, "https://saiyoku.jp/")
    assert "https://saiyoku.jp/id-1/1/" in urls
    assert "https://saiyoku.jp/id-1/2/" in urls
    assert "https://saiyoku.jp/id-1/3/" in urls
    assert len([u for u in urls if "/about/" in u]) == 0


def test_get_item_urls_deduplicates(parser: SaitamaParser) -> None:
    html = """
    <html><body>
      <a href="/id-1/1/">湯1</a>
      <a href="/id-1/1/">湯1（重複）</a>
    </body></html>
    """
    urls = parser.get_item_urls(html, "https://saiyoku.jp/")
    assert len(urls) == 1
