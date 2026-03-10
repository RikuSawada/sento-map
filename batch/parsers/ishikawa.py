"""石川県銭湯組合 (ishikawa1010.com) パーサー。

HTML 構造（想定）:
- 一覧/地図: https://ishikawa1010.com/bath
  - 個別リンク: /bath/{ID}
  - 座標: data-lat/data-lng または JavaScript 変数（lat/lng）に埋め込み
- 個別: /bath/{ID}
  - 銭湯名: h1/h2
  - 住所・電話・営業時間・定休日: dt/dd ペア
  - 座標: Google Maps embed/link または JavaScript 変数
"""
import logging
import re
from typing import Optional
from urllib.parse import unquote, urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup
from bs4.element import Tag

from parsers.base import BaseParser
from parsers.utils import extract_label_value

logger = logging.getLogger(__name__)

BASE_URL = "https://ishikawa1010.com"
LIST_URL = f"{BASE_URL}/bath"

_DETAIL_URL_PATH_PATTERN = re.compile(r"^/bath/\d+/?$")
_DETAIL_URL_IN_HTML_PATTERN = re.compile(r"(?:https?://[^\"'\s]+)?/bath/\d+/?")

_GMAPS_Q_PATTERN = re.compile(r"[?&]q=([-\d.]+),([-\d.]+)")
_GMAPS_LL_PATTERN = re.compile(r"[?&]ll=([-\d.]+),([-\d.]+)")
_GMAPS_DESTINATION_PATTERN = re.compile(r"destination=([-\d.]+),([-\d.]+)")
_GMAPS_CENTER_PATTERN = re.compile(r"center=([-\d.]+)(?:,|%2C)([-\d.]+)")
_GMAPS_EMBED_3D4D_PATTERN = re.compile(r"!3d([-\d.]+)!4d([-\d.]+)")
_GMAPS_EMBED_2D3D_PATTERN = re.compile(r"!2d([-\d.]+)!3d([-\d.]+)")
_GMAPS_URL_PATTERN = re.compile(r"https?://(?:www\.)?google\.[^\"'\s]+/maps[^\"'\s]*")

_LAT_VALUE_PATTERN = re.compile(r"(?:[\"']?(?:lat|latitude)[\"']?)\s*[:=]\s*[\"']?([-\d.]+)")
_LNG_VALUE_PATTERN = re.compile(r"(?:[\"']?(?:lng|lon|longitude)[\"']?)\s*[:=]\s*[\"']?([-\d.]+)")


class IshikawaParser(BaseParser):
    prefecture = "石川県"
    region = "中部"

    def __init__(self) -> None:
        # source_url -> (lat, lng)
        self._coord_cache: dict[str, tuple[float, float]] = {}

    def get_list_urls(self) -> list[str]:
        return [LIST_URL]

    def get_item_urls(self, html: str, page_url: str) -> list[str]:
        soup = BeautifulSoup(html, "lxml")
        urls: list[str] = []
        seen: set[str] = set()

        # 1) a タグから個別 URL を抽出（data-* 座標があればキャッシュ）
        for a in soup.find_all("a", href=True):
            normalized = self._normalize_detail_url(a["href"])
            if not normalized:
                continue
            if normalized not in seen:
                seen.add(normalized)
                urls.append(normalized)

            coords = self._extract_coords_from_tag_context(a)
            if coords:
                self._coord_cache[normalized] = coords

        # 2) JS から個別 URL / 座標を抽出
        for m in _DETAIL_URL_IN_HTML_PATTERN.finditer(html):
            normalized = self._normalize_detail_url(m.group(0))
            if not normalized:
                continue
            if normalized not in seen:
                seen.add(normalized)
                urls.append(normalized)

            # URL 近傍のテキストから lat/lng もしくは Google Maps URL を抽出
            coords = self._extract_coords_from_object_near(html, m.start(), m.end())
            if not coords:
                start = max(0, m.start() - 400)
                end = min(len(html), m.end() + 400)
                coords = self._extract_coords_from_text(html[start:end])
            if coords and normalized not in self._coord_cache:
                self._coord_cache[normalized] = coords

        return urls

    def parse_sento(self, html: str, page_url: str) -> Optional[dict]:
        soup = BeautifulSoup(html, "lxml")
        normalized_page_url = self._normalize_detail_url(page_url) or page_url

        name: Optional[str] = None
        for selector in ("h1.entry-title", "h1", "h2"):
            tag = soup.select_one(selector)
            if tag:
                raw = tag.get_text(strip=True)
                if raw and len(raw) < 60:
                    name = raw
                    break
        if not name:
            logger.warning("name が取得できません: %s", page_url)
            return None

        address = extract_label_value(soup, "住所") or ""
        phone = extract_label_value(soup, "TEL") or extract_label_value(soup, "電話")
        if not phone:
            tel_tag = soup.find("a", href=re.compile(r"^tel:"))
            if tel_tag:
                phone = tel_tag["href"].replace("tel:", "").strip()
        open_hours = extract_label_value(soup, "営業時間")
        holiday = extract_label_value(soup, "定休日") or extract_label_value(soup, "休日")

        lat: Optional[float] = None
        lng: Optional[float] = None

        cached = self._coord_cache.get(normalized_page_url)
        if cached:
            lat, lng = cached

        if lat is None:
            for tag in soup.find_all(["a", "iframe"]):
                src_or_href = tag.get("href") or tag.get("src")
                if not src_or_href:
                    continue
                coords = self._extract_coords_from_google_maps_url(src_or_href)
                if coords:
                    lat, lng = coords
                    break

        if lat is None:
            coords = self._extract_coords_from_text(html)
            if coords:
                lat, lng = coords

        return {
            **self.make_sento_dict(
                name=name,
                address=address,
                lat=lat,
                lng=lng,
                phone=phone,
                open_hours=open_hours,
                holiday=holiday,
                source_url=normalized_page_url,
            ),
            "facility_type": "sento",
        }

    def _normalize_detail_url(self, raw_url: str) -> Optional[str]:
        url = urljoin(BASE_URL, raw_url)
        parsed = urlparse(url)
        if not _DETAIL_URL_PATH_PATTERN.match(parsed.path):
            return None

        path = parsed.path.rstrip("/") + "/"
        normalized = urlunparse(("https", "ishikawa1010.com", path, "", "", ""))
        return normalized

    def _extract_coords_from_tag_context(self, tag: Tag) -> Optional[tuple[float, float]]:
        for node in (tag, tag.parent):
            if not isinstance(node, Tag):
                continue

            attr_pairs = [
                ("data-lat", "data-lng"),
                ("data-lat", "data-lon"),
                ("data-latitude", "data-longitude"),
                ("lat", "lng"),
                ("latitude", "longitude"),
            ]
            for lat_key, lng_key in attr_pairs:
                lat_raw = node.attrs.get(lat_key)
                lng_raw = node.attrs.get(lng_key)
                coords = self._to_coord_pair(lat_raw, lng_raw)
                if coords:
                    return coords

            for attr_val in node.attrs.values():
                if isinstance(attr_val, str):
                    coords = self._extract_coords_from_google_maps_url(attr_val)
                    if coords:
                        return coords
                    coords = self._extract_coords_from_text(attr_val)
                    if coords:
                        return coords

        return None

    def _extract_coords_from_google_maps_url(self, raw_url: str) -> Optional[tuple[float, float]]:
        if "google" not in raw_url or "maps" not in raw_url:
            return None

        decoded = unquote(raw_url)
        for pattern in (
            _GMAPS_Q_PATTERN,
            _GMAPS_DESTINATION_PATTERN,
            _GMAPS_LL_PATTERN,
            _GMAPS_CENTER_PATTERN,
            _GMAPS_EMBED_3D4D_PATTERN,
        ):
            m = pattern.search(decoded)
            if m:
                coords = self._to_coord_pair(m.group(1), m.group(2))
                if coords:
                    return coords
        m_embed_2d3d = _GMAPS_EMBED_2D3D_PATTERN.search(decoded)
        if m_embed_2d3d:
            # !2d{lng}!3d{lat} の順序で埋め込まれる形式
            coords = self._to_coord_pair(m_embed_2d3d.group(2), m_embed_2d3d.group(1))
            if coords:
                return coords
        return None

    def _extract_coords_from_text(self, text: str) -> Optional[tuple[float, float]]:
        # Google Maps URL を優先（実際の表示座標を拾いやすいため）
        for m in _GMAPS_URL_PATTERN.finditer(text):
            coords = self._extract_coords_from_google_maps_url(m.group(0))
            if coords:
                return coords

        lat_match = _LAT_VALUE_PATTERN.search(text)
        lng_match = _LNG_VALUE_PATTERN.search(text)
        if lat_match and lng_match:
            return self._to_coord_pair(lat_match.group(1), lng_match.group(1))
        return None

    def _extract_coords_from_object_near(
        self,
        text: str,
        match_start: int,
        match_end: int,
    ) -> Optional[tuple[float, float]]:
        """URL を含む JS オブジェクト断片から優先的に座標を抽出する。"""
        obj_start = text.rfind("{", max(0, match_start - 300), match_start + 1)
        obj_end = text.find("}", match_end, min(len(text), match_end + 300))
        if obj_start == -1 or obj_end == -1 or obj_end <= obj_start:
            return None
        return self._extract_coords_from_text(text[obj_start:obj_end + 1])

    def _to_coord_pair(self, lat_raw: object, lng_raw: object) -> Optional[tuple[float, float]]:
        try:
            lat = float(str(lat_raw))
            lng = float(str(lng_raw))
        except (TypeError, ValueError):
            return None

        if not (-90 <= lat <= 90 and -180 <= lng <= 180):
            return None
        return lat, lng
