"""AichiParser のユニットテスト。"""
import pytest

from parsers.aichi import AichiParser, _extract_label_value
from bs4 import BeautifulSoup


@pytest.fixture
def parser() -> AichiParser:
    return AichiParser()


# ---------------------------------------------------------------------------
# parse_sento: ハッピーパス
# ---------------------------------------------------------------------------

AICHI_DETAIL_HTML_HAPPY = """
<html>
<body>
  <h2>梅の湯[中区]</h2>
  <dl>
    <dt>住所</dt><dd>愛知県名古屋市中区1-2-3</dd>
    <dt>TEL</dt><dd>052-111-2222</dd>
    <dt>営業時間</dt><dd>16:00〜23:30</dd>
    <dt>定休日</dt><dd>火曜日</dd>
  </dl>
  <a href="https://www.google.com/maps?q=35.1815,136.9066">地図</a>
</body>
</html>
"""


def test_parse_sento_happy_path(parser: AichiParser) -> None:
    result = parser.parse_sento(AICHI_DETAIL_HTML_HAPPY, "https://aichi1010.jp/page/detail/l/1")

    assert result is not None
    assert result["name"] == "梅の湯"  # [中区] が除去されること
    assert result["address"] == "愛知県名古屋市中区1-2-3"
    assert result["phone"] == "052-111-2222"
    assert result["open_hours"] == "16:00〜23:30"
    assert result["holiday"] == "火曜日"
    assert result["lat"] == pytest.approx(35.1815)
    assert result["lng"] == pytest.approx(136.9066)
    assert result["prefecture"] == "愛知県"
    assert result["region"] == "東海"
    assert result["facility_type"] == "sento"
    assert result["source_url"] == "https://aichi1010.jp/page/detail/l/1"


# ---------------------------------------------------------------------------
# parse_sento: name が取得できない場合 None を返す
# ---------------------------------------------------------------------------

AICHI_DETAIL_HTML_NO_NAME = """
<html>
<body>
  <p>情報なし</p>
</body>
</html>
"""


def test_parse_sento_returns_none_when_name_missing(parser: AichiParser) -> None:
    result = parser.parse_sento(AICHI_DETAIL_HTML_NO_NAME, "https://aichi1010.jp/page/detail/l/999")
    assert result is None


# ---------------------------------------------------------------------------
# parse_sento: tel: リンクから電話番号を取得する
# ---------------------------------------------------------------------------

AICHI_DETAIL_HTML_TEL_LINK = """
<html>
<body>
  <h2>桜の湯</h2>
  <dl>
    <dt>住所</dt><dd>愛知県豊橋市1-1</dd>
  </dl>
  <a href="tel:0532-99-8888">電話する</a>
  <a href="https://www.google.com/maps?q=34.7700,137.3900">地図</a>
</body>
</html>
"""


def test_parse_sento_phone_from_tel_link(parser: AichiParser) -> None:
    result = parser.parse_sento(AICHI_DETAIL_HTML_TEL_LINK, "https://aichi1010.jp/page/detail/l/2")
    assert result is not None
    assert result["phone"] == "0532-99-8888"


# ---------------------------------------------------------------------------
# parse_sento: 座標が取得できない場合 None になること
# ---------------------------------------------------------------------------

AICHI_DETAIL_HTML_NO_COORDS = """
<html>
<body>
  <h2>竹の湯</h2>
  <dl>
    <dt>住所</dt><dd>愛知県岡崎市2-3</dd>
  </dl>
</body>
</html>
"""


def test_parse_sento_lat_lng_none_when_no_maps_link(parser: AichiParser) -> None:
    result = parser.parse_sento(AICHI_DETAIL_HTML_NO_COORDS, "https://aichi1010.jp/page/detail/l/3")
    assert result is not None
    assert result["lat"] is None
    assert result["lng"] is None


# ---------------------------------------------------------------------------
# get_item_urls: 個別ページ URL を抽出する
# ---------------------------------------------------------------------------

AICHI_LIST_HTML = """
<html>
<body>
  <a href="/page/detail/l/10">松の湯</a>
  <a href="/page/detail/l/11">梅の湯</a>
  <a href="/page/list/l/2">次のページ</a>
  <a href="/about/">概要</a>
</body>
</html>
"""


def test_get_item_urls(parser: AichiParser) -> None:
    urls = parser.get_item_urls(AICHI_LIST_HTML, "https://aichi1010.jp/page/list/l/1")
    assert urls == [
        "https://aichi1010.jp/page/detail/l/10",
        "https://aichi1010.jp/page/detail/l/11",
    ]


def test_get_item_urls_deduplicates(parser: AichiParser) -> None:
    html = """
    <html><body>
      <a href="/page/detail/l/10">A</a>
      <a href="/page/detail/l/10">A dup</a>
    </body></html>
    """
    urls = parser.get_item_urls(html, "https://aichi1010.jp/page/list/l/1")
    assert len(urls) == 1


# ---------------------------------------------------------------------------
# _extract_label_value ヘルパー
# ---------------------------------------------------------------------------

def test_extract_label_value_dt_dd() -> None:
    soup = BeautifulSoup("<dl><dt>住所</dt><dd>名古屋市</dd></dl>", "lxml")
    assert _extract_label_value(soup, "住所") == "名古屋市"


def test_extract_label_value_returns_none_when_missing() -> None:
    soup = BeautifulSoup("<dl><dt>TEL</dt><dd>052-0000</dd></dl>", "lxml")
    assert _extract_label_value(soup, "住所") is None
