"""MieParser のユニットテスト。"""
import pytest

from parsers.mie import MieParser


@pytest.fixture
def parser() -> MieParser:
    return MieParser()


def test_get_item_urls_extracts_from_js_array(parser: MieParser) -> None:
    html = """
    <html><body>
      <script>
      var sentoMarkers = [
        {"url": "/sento/a/", "lat": 34.7303, "lng": 136.5086},
        {"url": "https://mie1010.com/sento/b/", "latitude": "34.7011", "longitude": "136.4962"}
      ];
      </script>
    </body></html>
    """
    urls = parser.get_item_urls(html, "https://mie1010.com/")

    assert urls == [
        "https://mie1010.com/sento/a/",
        "https://mie1010.com/sento/b/",
    ]
    assert parser._coord_cache["https://mie1010.com/sento/a/"] == pytest.approx((34.7303, 136.5086))
    assert parser._coord_cache["https://mie1010.com/sento/b/"] == pytest.approx((34.7011, 136.4962))


def test_get_item_urls_extracts_from_geojson(parser: MieParser) -> None:
    html = """
    <html><body>
      <script>
      const mapData = {
        "type": "FeatureCollection",
        "features": [
          {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [136.5050, 34.7200]},
            "properties": {"url": "/sento/geo/"}
          }
        ]
      };
      </script>
    </body></html>
    """
    urls = parser.get_item_urls(html, "https://mie1010.com/")
    assert urls == ["https://mie1010.com/sento/geo/"]
    assert parser._coord_cache["https://mie1010.com/sento/geo/"] == pytest.approx((34.72, 136.505))


def test_get_item_urls_extracts_url_from_html_fragment(parser: MieParser) -> None:
    html = """
    <html><body>
      <script>
      let markers = [
        {
          "html": "<div><a href='/sento/from-html/'>詳細</a></div>",
          "position": {"lat": 34.6800, "lng": 136.4600}
        }
      ];
      </script>
    </body></html>
    """
    urls = parser.get_item_urls(html, "https://mie1010.com/")
    assert urls == ["https://mie1010.com/sento/from-html/"]
    assert parser._coord_cache["https://mie1010.com/sento/from-html/"] == pytest.approx((34.68, 136.46))


def test_get_item_urls_deduplicates(parser: MieParser) -> None:
    html = """
    <html><body>
      <script>
      const markers = [
        {"url": "/sento/dup/", "lat": 34.70, "lng": 136.50},
        {"url": "/sento/dup/", "lat": 34.70, "lng": 136.50}
      ];
      </script>
    </body></html>
    """
    urls = parser.get_item_urls(html, "https://mie1010.com/")
    assert urls == ["https://mie1010.com/sento/dup/"]


def test_parse_sento_uses_cached_coords(parser: MieParser) -> None:
    url = "https://mie1010.com/sento/cache/"
    parser._coord_cache[url] = (34.7111, 136.5222)

    html = """
    <html><body>
      <h1>津の湯</h1>
      <dl><dt>住所</dt><dd>三重県津市1-2-3</dd></dl>
    </body></html>
    """
    result = parser.parse_sento(html, url)

    assert result is not None
    assert result["name"] == "津の湯"
    assert result["address"] == "三重県津市1-2-3"
    assert result["lat"] == pytest.approx(34.7111)
    assert result["lng"] == pytest.approx(136.5222)
    assert result["prefecture"] == "三重県"
    assert result["region"] == "近畿"
    assert result["facility_type"] == "sento"


def test_parse_sento_lat_lng_none_when_not_found(parser: MieParser) -> None:
    html = """
    <html><body>
      <h1>伊勢の湯</h1>
      <dl><dt>住所</dt><dd>三重県伊勢市4-5-6</dd></dl>
    </body></html>
    """
    result = parser.parse_sento(html, "https://mie1010.com/sento/no-coord/")
    assert result is not None
    assert result["lat"] is None
    assert result["lng"] is None


def test_parse_sento_returns_none_when_name_missing(parser: MieParser) -> None:
    html = """
    <html><body>
      <p>準備中</p>
    </body></html>
    """
    assert parser.parse_sento(html, "https://mie1010.com/sento/unknown/") is None
