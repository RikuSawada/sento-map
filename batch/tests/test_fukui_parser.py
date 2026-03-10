"""FukuiParser のユニットテスト。"""
import pytest

from parsers.fukui import FukuiParser, _extract_coords_from_maps_url


@pytest.fixture
def parser() -> FukuiParser:
    return FukuiParser()


def test_get_list_urls(parser: FukuiParser) -> None:
    assert parser.get_list_urls() == ["https://fukui1010.com/"]


def test_get_item_urls_collects_detail_links(parser: FukuiParser) -> None:
    html = """
    <html><body>
      <a href="/sento/matsu-no-yu/">松の湯</a>
      <a href="https://fukui1010.com/bath/ume-no-yu/">梅の湯</a>
      <a href="/about/">このサイトについて</a>
      <a href="https://example.com/sento/foo/">外部</a>
    </body></html>
    """
    urls = parser.get_item_urls(html, "https://fukui1010.com/")
    assert urls == [
        "https://fukui1010.com/sento/matsu-no-yu/",
        "https://fukui1010.com/bath/ume-no-yu/",
    ]


def test_get_item_urls_deduplicates(parser: FukuiParser) -> None:
    html = """
    <html><body>
      <a href="/sento/matsu-no-yu/">松の湯</a>
      <a href="https://fukui1010.com/sento/matsu-no-yu/">松の湯(重複)</a>
    </body></html>
    """
    urls = parser.get_item_urls(html, "https://fukui1010.com/")
    assert len(urls) == 1


def test_parse_sento_happy_path(parser: FukuiParser) -> None:
    html = """
    <html><body>
      <h1>松の湯【福井市】</h1>
      <dl>
        <dt>住所</dt><dd>福井県福井市中央1-2-3</dd>
        <dt>TEL</dt><dd>0776-11-2222</dd>
        <dt>営業時間</dt><dd>15:00-23:00</dd>
        <dt>定休日</dt><dd>月曜日</dd>
      </dl>
      <a href="https://www.google.com/maps?q=36.0641,136.2196">地図</a>
    </body></html>
    """

    result = parser.parse_sento(html, "https://fukui1010.com/sento/matsu-no-yu/")

    assert result is not None
    assert result["name"] == "松の湯"
    assert result["address"] == "福井県福井市中央1-2-3"
    assert result["phone"] == "0776-11-2222"
    assert result["open_hours"] == "15:00-23:00"
    assert result["holiday"] == "月曜日"
    assert result["lat"] == pytest.approx(36.0641)
    assert result["lng"] == pytest.approx(136.2196)
    assert result["prefecture"] == "福井県"
    assert result["region"] == "中部"
    assert result["facility_type"] == "sento"


def test_parse_sento_destination_coords_and_tel_link(parser: FukuiParser) -> None:
    html = """
    <html><body>
      <h2>梅の湯</h2>
      <table>
        <tr><th>所在地</th><td>福井県坂井市1-2</td></tr>
        <tr><th>営業</th><td>16:00-22:30</td></tr>
        <tr><th>休業日</th><td>木曜日</td></tr>
      </table>
      <a href="tel:0776-33-4444">電話</a>
      <a href="https://www.google.com/maps/dir/?api=1&destination=36.2123,136.1478">地図</a>
    </body></html>
    """

    result = parser.parse_sento(html, "https://fukui1010.com/sento/ume-no-yu/")

    assert result is not None
    assert result["address"] == "福井県坂井市1-2"
    assert result["phone"] == "0776-33-4444"
    assert result["open_hours"] == "16:00-22:30"
    assert result["holiday"] == "木曜日"
    assert result["lat"] == pytest.approx(36.2123)
    assert result["lng"] == pytest.approx(136.1478)


def test_parse_sento_lat_lng_none_when_no_maps_link(parser: FukuiParser) -> None:
    html = """
    <html><body>
      <h1>竹の湯</h1>
      <p>福井県越前市2-3-4</p>
    </body></html>
    """
    result = parser.parse_sento(html, "https://fukui1010.com/sento/take-no-yu/")
    assert result is not None
    assert result["lat"] is None
    assert result["lng"] is None


def test_parse_sento_returns_none_when_name_missing(parser: FukuiParser) -> None:
    html = """
    <html><body>
      <p>福井県福井市1-2-3</p>
      <a href="https://www.google.com/maps?q=36.0,136.0">地図</a>
    </body></html>
    """
    assert parser.parse_sento(html, "https://fukui1010.com/sento/unknown/") is None


def test_extract_coords_from_maps_url_embed_pattern() -> None:
    url = "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d1!2d136.5544!3d35.9422!2m3!1f0!2f0!3f0"
    lat_lng = _extract_coords_from_maps_url(url)
    assert lat_lng == pytest.approx((35.9422, 136.5544))
