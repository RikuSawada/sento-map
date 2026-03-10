"""三重銭湯組合 (mie1010.com) パーサー。"""
import json
import logging
import re
from typing import Any, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from parsers.base import BaseParser

logger = logging.getLogger(__name__)

BASE_URL = "https://mie1010.com"
LIST_URL = f"{BASE_URL}/"

_JSON_ARRAY_PATTERN = re.compile(
    r"(?:var|let|const)\s+[A-Za-z_$][\w$]*\s*=\s*(\[[\s\S]*?\])\s*;",
    re.DOTALL,
)
_JSON_OBJECT_PATTERN = re.compile(
    r"(?:var|let|const)\s+[A-Za-z_$][\w$]*\s*=\s*(\{[\s\S]*?\"features\"[\s\S]*?\})\s*;",
    re.DOTALL,
)
_MAPS_Q_PATTERN = re.compile(r"[?&]q=([-\d.]+),([-\d.]+)")
_DESTINATION_PATTERN = re.compile(r"destination=([-\d.]+),([-\d.]+)")
_LL_PATTERN = re.compile(r"[?&]ll=([-\d.]+),([-\d.]+)")
_URL_FROM_HTML_PATTERN = re.compile(r"""href=["']([^"']+)["']""")


class MieParser(BaseParser):
    prefecture = "三重県"
    region = "近畿"

    def __init__(self) -> None:
        self._coord_cache: dict[str, tuple[float, float]] = {}

    def get_list_urls(self) -> list[str]:
        return [LIST_URL]

    def get_item_urls(self, html: str, page_url: str) -> list[str]:
        urls: list[str] = []
        seen: set[str] = set()

        for data in self._extract_json_candidates(html):
            for url, lat, lng in self._collect_sento_entries(data):
                normalized_url = self._normalize_item_url(url)
                if not normalized_url:
                    continue
                if lat is not None and lng is not None:
                    self._coord_cache[normalized_url] = (lat, lng)
                if normalized_url not in seen:
                    seen.add(normalized_url)
                    urls.append(normalized_url)

        if urls:
            return urls

        return self._extract_item_urls_fallback(html)

    def parse_sento(self, html: str, page_url: str) -> Optional[dict]:
        soup = BeautifulSoup(html, "lxml")

        name: Optional[str] = None
        for selector in ("h1", "h2", ".sento-name", ".entry-title"):
            tag = soup.select_one(selector)
            if tag:
                raw = tag.get_text(strip=True)
                if raw and len(raw) < 80:
                    name = raw
                    break
        if not name:
            title = soup.find("title")
            if title:
                raw = title.get_text(strip=True)
                if raw:
                    name = raw.split("|")[0].strip()

        if not name:
            logger.warning("name が取得できません: %s", page_url)
            return None

        address = (
            self.extract_label_value(soup, "住所")
            or self.extract_table_value(soup, "住所")
            or ""
        )
        phone = (
            self.extract_label_value(soup, "TEL")
            or self.extract_label_value(soup, "電話")
            or self.extract_table_value(soup, "TEL")
            or self.extract_table_value(soup, "電話")
        )
        if not phone:
            tel_tag = soup.find("a", href=re.compile(r"^tel:"))
            if tel_tag:
                phone = str(tel_tag["href"]).replace("tel:", "").strip()

        open_hours = self.extract_label_value(soup, "営業時間") or self.extract_table_value(soup, "営業時間")
        holiday = (
            self.extract_label_value(soup, "定休日")
            or self.extract_label_value(soup, "休日")
            or self.extract_table_value(soup, "定休日")
            or self.extract_table_value(soup, "休日")
        )

        normalized_page_url = self._normalize_item_url(page_url)
        lat: Optional[float] = None
        lng: Optional[float] = None

        cached = self._coord_cache.get(normalized_page_url)
        if cached:
            lat, lng = cached
        else:
            lat, lng = self._extract_lat_lng_from_html(html)

        return {
            **self.make_sento_dict(
                name=name,
                address=address,
                lat=lat,
                lng=lng,
                phone=phone,
                open_hours=open_hours,
                holiday=holiday,
                source_url=page_url,
            ),
            "facility_type": "sento",
        }

    def _extract_item_urls_fallback(self, html: str) -> list[str]:
        soup = BeautifulSoup(html, "lxml")
        urls: list[str] = []
        seen: set[str] = set()
        for a in soup.find_all("a", href=True):
            href = str(a["href"]).strip()
            normalized = self._normalize_item_url(href)
            if not normalized:
                continue
            if normalized in (LIST_URL, BASE_URL):
                continue
            if normalized not in seen:
                seen.add(normalized)
                urls.append(normalized)
        return urls

    @staticmethod
    def _normalize_item_url(url: str) -> Optional[str]:
        if not url:
            return None
        if url.startswith(("javascript:", "mailto:", "tel:", "#")):
            return None
        normalized = urljoin(BASE_URL, url.strip())
        if not normalized.startswith(BASE_URL):
            return None
        return normalized.split("#", 1)[0]

    @staticmethod
    def _extract_json_candidates(html: str) -> list[Any]:
        candidates: list[Any] = []

        soup = BeautifulSoup(html, "lxml")
        for script in soup.find_all("script"):
            script_text = script.get_text("\n", strip=True)
            if not script_text:
                continue

            script_type = (script.get("type") or "").lower()
            if "json" in script_type:
                parsed = MieParser._safe_json_loads(script_text)
                if parsed is not None:
                    candidates.append(parsed)

            for pattern in (_JSON_ARRAY_PATTERN, _JSON_OBJECT_PATTERN):
                for m in pattern.finditer(script_text):
                    parsed = MieParser._safe_json_loads(m.group(1))
                    if parsed is not None:
                        candidates.append(parsed)

        return candidates

    @staticmethod
    def _safe_json_loads(raw: str) -> Optional[Any]:
        sanitized = re.sub(r",\s*([}\]])", r"\1", raw.strip())
        try:
            return json.loads(sanitized)
        except json.JSONDecodeError:
            return None

    def _collect_sento_entries(self, data: Any) -> list[tuple[str, Optional[float], Optional[float]]]:
        entries: list[tuple[str, Optional[float], Optional[float]]] = []
        self._walk_data(data, entries)
        return entries

    def _walk_data(self, data: Any, entries: list[tuple[str, Optional[float], Optional[float]]]) -> None:
        if isinstance(data, dict):
            entry = self._extract_entry_from_dict(data)
            if entry:
                entries.append(entry)
            for value in data.values():
                self._walk_data(value, entries)
        elif isinstance(data, list):
            for item in data:
                self._walk_data(item, entries)

    def _extract_entry_from_dict(self, item: dict[str, Any]) -> Optional[tuple[str, Optional[float], Optional[float]]]:
        url = self._extract_url(item)
        if not url:
            return None
        lat, lng = self._extract_lat_lng(item)
        return (url, lat, lng)

    @staticmethod
    def _extract_url(item: dict[str, Any]) -> Optional[str]:
        for key in ("url", "link", "href", "permalink"):
            value = item.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

        for key in ("html", "content", "popup"):
            value = item.get(key)
            if isinstance(value, str) and value.strip():
                m = _URL_FROM_HTML_PATTERN.search(value)
                if m:
                    return m.group(1).strip()

        properties = item.get("properties")
        if isinstance(properties, dict):
            for key in ("url", "link", "href"):
                value = properties.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
        return None

    @staticmethod
    def _to_float(value: Any) -> Optional[float]:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _extract_lat_lng(self, item: dict[str, Any]) -> tuple[Optional[float], Optional[float]]:
        lat = self._to_float(item.get("lat")) or self._to_float(item.get("latitude"))
        lng = self._to_float(item.get("lng")) or self._to_float(item.get("longitude"))
        if lat is not None and lng is not None:
            return lat, lng

        position = item.get("position")
        if isinstance(position, dict):
            p_lat = self._to_float(position.get("lat")) or self._to_float(position.get("latitude"))
            p_lng = self._to_float(position.get("lng")) or self._to_float(position.get("longitude"))
            if p_lat is not None and p_lng is not None:
                return p_lat, p_lng

        geometry = item.get("geometry")
        if isinstance(geometry, dict):
            coordinates = geometry.get("coordinates")
            if isinstance(coordinates, list) and len(coordinates) >= 2:
                g_lng = self._to_float(coordinates[0])
                g_lat = self._to_float(coordinates[1])
                if g_lat is not None and g_lng is not None:
                    return g_lat, g_lng

        properties = item.get("properties")
        if isinstance(properties, dict):
            prop_lat = self._to_float(properties.get("lat")) or self._to_float(properties.get("latitude"))
            prop_lng = self._to_float(properties.get("lng")) or self._to_float(properties.get("longitude"))
            if prop_lat is not None and prop_lng is not None:
                return prop_lat, prop_lng

        return None, None

    def _extract_lat_lng_from_html(self, html: str) -> tuple[Optional[float], Optional[float]]:
        for data in self._extract_json_candidates(html):
            for _, lat, lng in self._collect_sento_entries(data):
                if lat is not None and lng is not None:
                    return lat, lng

        soup = BeautifulSoup(html, "lxml")
        for tag in soup.find_all(["a", "iframe"], href=True):
            href = str(tag["href"])
            for pattern in (_MAPS_Q_PATTERN, _DESTINATION_PATTERN, _LL_PATTERN):
                m = pattern.search(href)
                if m:
                    return self._to_float(m.group(1)), self._to_float(m.group(2))

        for iframe in soup.find_all("iframe", src=True):
            src = str(iframe["src"])
            for pattern in (_MAPS_Q_PATTERN, _DESTINATION_PATTERN, _LL_PATTERN):
                m = pattern.search(src)
                if m:
                    return self._to_float(m.group(1)), self._to_float(m.group(2))

        return None, None
