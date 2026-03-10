"""osm_geocoder モジュールのユニットテスト。"""
import pytest

from osm_geocoder import (
    PARSER_IMPLEMENTED_PREFECTURES,
    PREFECTURE_NAMES,
    PREFECTURE_TO_REGION,
    _build_address,
    extract_coords,
    find_best_match,
    resolve_facility_type,
)


# ---------------------------------------------------------------------------
# resolve_facility_type
# ---------------------------------------------------------------------------

def test_resolve_facility_type_spa() -> None:
    assert resolve_facility_type({"amenity": "spa"}) == "super_sento"


def test_resolve_facility_type_onsen() -> None:
    assert resolve_facility_type({"amenity": "public_bath", "bath:type": "onsen"}) == "onsen"


def test_resolve_facility_type_sento() -> None:
    assert resolve_facility_type({"amenity": "public_bath"}) == "sento"


def test_resolve_facility_type_sento_unknown_bath_type() -> None:
    assert resolve_facility_type({"amenity": "public_bath", "bath:type": "other"}) == "sento"


def test_resolve_facility_type_empty_tags() -> None:
    assert resolve_facility_type({}) == "sento"


# ---------------------------------------------------------------------------
# extract_coords
# ---------------------------------------------------------------------------

def test_extract_coords_node() -> None:
    element = {"type": "node", "lat": 35.6895, "lon": 139.6917}
    lat, lng = extract_coords(element)
    assert lat == pytest.approx(35.6895)
    assert lng == pytest.approx(139.6917)


def test_extract_coords_way_with_center() -> None:
    element = {"type": "way", "center": {"lat": 35.1234, "lon": 136.9876}}
    lat, lng = extract_coords(element)
    assert lat == pytest.approx(35.1234)
    assert lng == pytest.approx(136.9876)


def test_extract_coords_way_without_center() -> None:
    element = {"type": "way"}
    lat, lng = extract_coords(element)
    assert lat is None
    assert lng is None


def test_extract_coords_relation_with_center() -> None:
    element = {"type": "relation", "center": {"lat": 43.0621, "lon": 141.3544}}
    lat, lng = extract_coords(element)
    assert lat == pytest.approx(43.0621)
    assert lng == pytest.approx(141.3544)


# ---------------------------------------------------------------------------
# find_best_match
# ---------------------------------------------------------------------------

def _make_element(name: str, lat: float = 35.0, lon: float = 135.0) -> dict:
    return {
        "type": "node",
        "lat": lat,
        "lon": lon,
        "tags": {"name": name, "amenity": "public_bath"},
    }


def test_find_best_match_exact() -> None:
    elements = [_make_element("鶴の湯"), _make_element("亀の湯")]
    result = find_best_match("鶴の湯", "東京都港区1-1-1", elements)
    assert result is not None
    assert result["tags"]["name"] == "鶴の湯"


def test_find_best_match_above_threshold() -> None:
    elements = [_make_element("松の湯銭湯")]
    result = find_best_match("松の湯", "大阪市中央区1-1", elements)
    assert result is not None
    assert result["tags"]["name"] == "松の湯銭湯"


def test_find_best_match_below_threshold_returns_none() -> None:
    elements = [_make_element("全然違う名前の施設")]
    result = find_best_match("鶴の湯", "東京都港区1-1-1", elements)
    assert result is None


def test_find_best_match_empty_list() -> None:
    result = find_best_match("鶴の湯", "東京都港区1-1-1", [])
    assert result is None


def test_find_best_match_element_without_name_is_skipped() -> None:
    elements = [{"type": "node", "lat": 35.0, "lon": 135.0, "tags": {}}]
    result = find_best_match("鶴の湯", "東京都港区1-1-1", elements)
    assert result is None


def test_find_best_match_returns_highest_score() -> None:
    elements = [
        _make_element("竹の湯"),
        _make_element("竹の湯銭湯"),  # より類似度が高い
    ]
    result = find_best_match("竹の湯銭湯", "埼玉県浦和市1-1", elements)
    assert result is not None
    assert result["tags"]["name"] == "竹の湯銭湯"


# ---------------------------------------------------------------------------
# _build_address
# ---------------------------------------------------------------------------

def test_build_address_with_addr_tags() -> None:
    tags = {
        "addr:city": "札幌市",
        "addr:suburb": "中央区",
        "addr:street": "大通西",
        "addr:housenumber": "1",
    }
    result = _build_address(tags, "北海道")
    assert result == "札幌市中央区大通西1"


def test_build_address_fallback_to_prefecture() -> None:
    result = _build_address({}, "大分県")
    assert result == "大分県"


def test_build_address_partial_tags() -> None:
    tags = {"addr:city": "福岡市"}
    result = _build_address(tags, "福岡県")
    assert result == "福岡市"


def test_build_address_addr_full_takes_precedence_in_caller() -> None:
    # _build_address 自体は addr:full を扱わない（呼び出し元で処理）
    # addr:full がない場合にフォールバックで呼ばれる前提
    tags = {"addr:province": "愛知県", "addr:city": "名古屋市"}
    result = _build_address(tags, "愛知県")
    assert result == "愛知県名古屋市"


def test_wakayama_in_prefecture_names() -> None:
    assert "和歌山県" in PREFECTURE_NAMES


def test_wakayama_region_is_kinki() -> None:
    assert PREFECTURE_TO_REGION["和歌山県"] == "近畿"


def test_wakayama_not_in_parser_implemented_prefectures() -> None:
    assert "和歌山県" not in PARSER_IMPLEMENTED_PREFECTURES
