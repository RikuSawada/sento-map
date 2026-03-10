"""栃木県銭湯組合 (tochigi1010.jp) パーサー。

実装方針:
- 一覧ページから個別ページ URL を収集
- 個別ページから基本情報を抽出
- 座標は Google Maps リンクから抽出
- Google Maps リンクが無い場合は lat/lng=None（OSM 補完を想定）
"""
import logging
import re
from typing import Optional
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup

from parsers.base import BaseParser

logger = logging.getLogger(__name__)

BASE_URL = "https://tochigi1010.jp"
LIST_URL = f"{BASE_URL}/shoplist/"

_DETAIL_URL_PATTERN = re.compile(
    r"/(?:shop|sento|tenpo|store|detail)/[^/?#]+/?$|/page/detail/l/\d+/?$"
)
_EXCLUDED_PATH_PATTERN = re.compile(
    r"/(?:shoplist|list|category|tag|news|blog|about|contact|privacy|wp-admin|wp-login|page/\d+)/?",
    re.IGNORECASE,
)

_GMAPS_Q_PATTERN = re.compile(r"[?&]q=([-\d.]+),([-\d.]+)")
_DESTINATION_PATTERN = re.compile(r"[?&]destination=([-\d.]+),([-\d.]+)")
_LL_PATTERN = re.compile(r"[?&]ll=([-\d.]+),([-\d.]+)")
_AT_PATTERN = re.compile(r"@([-\d.]+),([-\d.]+),")
_QUERY_COORD_PATTERN = re.compile(r"^([-\d.]+),([-\d.]+)$")
_PHONE_PATTERN = re.compile(r"(0\d{1,4}-\d{1,4}-\d{3,4})")


class TochigiParser(BaseParser):
    prefecture = "栃木県"
    region = "関東"

    def get_list_urls(self) -> list[str]:
        return [LIST_URL]

    def get_item_urls(self, html: str, page_url: str) -> list[str]:
        soup = BeautifulSoup(html, "lxml")
        urls: list[str] = []
        seen: set[str] = set()

        for a in soup.find_all("a", href=True):
            href: str = a["href"]
            if not href.startswith("http"):
                href = urljoin(BASE_URL, href)

            parsed = urlparse(href)
            if "tochigi1010.jp" not in parsed.netloc:
                continue
            if _EXCLUDED_PATH_PATTERN.search(parsed.path):
                continue
            if not _DETAIL_URL_PATTERN.search(parsed.path):
                continue

            normalized = href.rstrip("/") + "/"
            if normalized not in seen:
                seen.add(normalized)
                urls.append(normalized)

        return urls

    def parse_sento(self, html: str, page_url: str) -> Optional[dict]:
        soup = BeautifulSoup(html, "lxml")

        name = self._extract_name(soup)
        if not name:
            logger.warning("name が取得できません: %s", page_url)
            return None

        address = (
            self.extract_label_value(soup, "住所")
            or self.extract_table_value(soup, "住所")
            or self._extract_text_by_label(soup, "住所")
            or ""
        )
        phone = (
            self.extract_label_value(soup, "TEL")
            or self.extract_label_value(soup, "電話")
            or self.extract_table_value(soup, "TEL")
            or self.extract_table_value(soup, "電話")
            or self._extract_tel_link(soup)
            or self._extract_text_by_label(soup, "TEL")
            or self._extract_text_by_label(soup, "電話")
        )
        open_hours = (
            self.extract_label_value(soup, "営業時間")
            or self.extract_table_value(soup, "営業時間")
            or self._extract_text_by_label(soup, "営業時間")
        )
        holiday = (
            self.extract_label_value(soup, "定休日")
            or self.extract_label_value(soup, "休日")
            or self.extract_table_value(soup, "定休日")
            or self.extract_table_value(soup, "休業日")
            or self._extract_text_by_label(soup, "定休日")
            or self._extract_text_by_label(soup, "休日")
        )

        lat: Optional[float] = None
        lng: Optional[float] = None
        for maps_tag in soup.find_all("a", href=True):
            href: str = maps_tag["href"]
            if "google." not in href or "/maps" not in href:
                continue
            coords = self._extract_coords_from_map_url(href)
            if coords:
                lat, lng = coords
                break

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

    def _extract_name(self, soup: BeautifulSoup) -> Optional[str]:
        for selector in ("h1.entry-title", "h1.sento-name", "h1", "h2"):
            tag = soup.select_one(selector)
            if not tag:
                continue
            raw = tag.get_text(" ", strip=True)
            if not raw:
                continue
            name = raw.split("|")[0].split("｜")[0].strip()
            if 1 <= len(name) <= 60:
                return name
        return None

    @staticmethod
    def _extract_text_by_label(soup: BeautifulSoup, label: str) -> Optional[str]:
        text = soup.get_text(separator="\n")
        m = re.search(rf"{re.escape(label)}\s*[:：]\s*(.+)", text)
        if m:
            value = m.group(1).strip()
            return value if value else None
        return None

    @staticmethod
    def _extract_tel_link(soup: BeautifulSoup) -> Optional[str]:
        tel_tag = soup.find("a", href=re.compile(r"^tel:"))
        if not tel_tag:
            return None
        return tel_tag["href"].replace("tel:", "").strip()

    @staticmethod
    def _extract_coords_from_map_url(url: str) -> Optional[tuple[float, float]]:
        for pattern in (_GMAPS_Q_PATTERN, _DESTINATION_PATTERN, _LL_PATTERN, _AT_PATTERN):
            m = pattern.search(url)
            if not m:
                continue
            try:
                return float(m.group(1)), float(m.group(2))
            except ValueError:
                continue

        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        q_values = query.get("query", []) + query.get("q", [])
        for value in q_values:
            m = _QUERY_COORD_PATTERN.match(value)
            if not m:
                continue
            try:
                return float(m.group(1)), float(m.group(2))
            except ValueError:
                continue

        m_phone = _PHONE_PATTERN.search(url)
        if m_phone:
            return None
        return None
