"""ToyamaParser のユニットテスト。"""
import pytest

from parsers import PARSERS
from parsers.toyama import ToyamaParser


@pytest.fixture
def parser() -> ToyamaParser:
    return ToyamaParser()


TOYAMA_DETAIL_HTML_HAPPY = """
<html>
<body>
  <h1 class="entry-title">ファミリー銭湯くさじま</h1>
  <div id="page-content">
    <p>
      【住所】 〒930-2201 富山市草島 236-4 <br>
      【電話番号】 076-435-1019 <br>
      【営業時間】 [平日]10:00～22:00 [日・祝]8:00～22:00 <br>
      【定休日】 第3月・火曜日 <br>
      【URL】 http://example.com/kusajima <br>
    </p>
    <iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3197.005740997716!2d137.2086403151387!3d36.74643327842448!2m3!1f0"></iframe>
  </div>
</body>
</html>
"""


def test_parse_sento_happy_path(parser: ToyamaParser) -> None:
    result = parser.parse_sento(TOYAMA_DETAIL_HTML_HAPPY, "https://toyama1010.com/toyama-f-kusajima.html")

    assert result is not None
    assert result["name"] == "ファミリー銭湯くさじま"
    assert result["address"] == "〒930-2201 富山市草島 236-4"
    assert result["phone"] == "076-435-1019"
    assert result["open_hours"] == "[平日]10:00～22:00 [日・祝]8:00～22:00"
    assert result["holiday"] == "第3月・火曜日"
    assert result["url"] == "http://example.com/kusajima"
    assert result["lat"] == pytest.approx(36.7464332784)
    assert result["lng"] == pytest.approx(137.2086403151)
    assert result["prefecture"] == "富山県"
    assert result["region"] == "中部"
    assert result["facility_type"] == "sento"


TOYAMA_DETAIL_HTML_Q_COORDS = """
<html>
<body>
  <h1 class="entry-title">朝日湯</h1>
  <div id="page-content">
    <p>【住所】 富山市堀川小泉町１－２３２</p>
    <a href="https://www.google.com/maps?q=36.6952,137.2138">地図</a>
  </div>
</body>
</html>
"""


def test_parse_sento_extracts_coords_from_google_maps_q(parser: ToyamaParser) -> None:
    result = parser.parse_sento(TOYAMA_DETAIL_HTML_Q_COORDS, "https://toyama1010.com/toyama-asahiyu.html")
    assert result is not None
    assert result["lat"] == pytest.approx(36.6952)
    assert result["lng"] == pytest.approx(137.2138)


TOYAMA_DETAIL_HTML_NO_MAP = """
<html>
<body>
  <h1 class="entry-title">浦乃湯</h1>
  <div id="page-content">
    <p>【住所】 富山市羽根２区８６</p>
    <p>【営業時間】 14:00～22:00</p>
  </div>
</body>
</html>
"""


def test_parse_sento_returns_none_coords_when_map_missing(parser: ToyamaParser) -> None:
    result = parser.parse_sento(TOYAMA_DETAIL_HTML_NO_MAP, "https://toyama1010.com/toyama-uranoyu.html")
    assert result is not None
    assert result["lat"] is None
    assert result["lng"] is None


TOYAMA_DETAIL_HTML_NO_NAME = """
<html>
<body>
  <div id="page-content">
    <p>【住所】 富山市草島236-4</p>
  </div>
</body>
</html>
"""


def test_parse_sento_returns_none_when_name_missing(parser: ToyamaParser) -> None:
    result = parser.parse_sento(TOYAMA_DETAIL_HTML_NO_NAME, "https://toyama1010.com/unknown.html")
    assert result is None


TOYAMA_LIST_HTML = """
<html>
<body>
  <table id="sp-table-3">
    <tr>
      <th class="col-title"><a href="toyama-asahiyu.html">朝日湯</a></th>
      <td>富山市</td>
    </tr>
    <tr>
      <th class="col-title"><a href="http://toyama1010.com/toyama-irifuneyu.html">入舟湯</a></th>
      <td>富山市</td>
    </tr>
    <tr>
      <th class="col-title"><a href="toyama-f-kusajima.html">ファミリー銭湯</a><a href="toyama-f-kusajima.html">くさじま</a></th>
      <td>富山市</td>
    </tr>
    <tr>
      <th class="col-title"><a href="https://example.com/not-target.html">外部</a></th>
      <td>外部</td>
    </tr>
  </table>
  <nav>
    <a href="index.html">HOME</a>
    <a href="about-union.html">組合について</a>
  </nav>
</body>
</html>
"""


def test_get_item_urls_extracts_only_detail_links_and_deduplicates(parser: ToyamaParser) -> None:
    urls = parser.get_item_urls(TOYAMA_LIST_HTML, "https://toyama1010.com/sentou-list.html")

    assert "https://toyama1010.com/toyama-asahiyu.html" in urls
    assert "http://toyama1010.com/toyama-irifuneyu.html" in urls
    assert "https://toyama1010.com/toyama-f-kusajima.html" in urls
    assert len(urls) == 3
    assert all("example.com" not in url for url in urls)
    assert all(not url.endswith("index.html") for url in urls)


TOYAMA_LIST_HTML_WITH_COMMON_PAGE = """
<html>
<body>
  <table id="sp-table-3">
    <tr>
      <th class="col-title"><a href="sentou-list.html">銭湯一覧</a></th>
    </tr>
    <tr>
      <th class="col-title"><a href="takaoka-akayu.html">赤湯</a></th>
    </tr>
  </table>
</body>
</html>
"""


def test_get_item_urls_excludes_common_pages(parser: ToyamaParser) -> None:
    urls = parser.get_item_urls(TOYAMA_LIST_HTML_WITH_COMMON_PAGE, "https://toyama1010.com/sentou-list.html")
    assert urls == ["https://toyama1010.com/takaoka-akayu.html"]


def test_parsers_registry_contains_toyama() -> None:
    assert "富山県" in PARSERS
    assert PARSERS["富山県"] is ToyamaParser
