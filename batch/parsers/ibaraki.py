"""茨城県銭湯組合 (ibaraki1010.com) パーサー。"""
import logging
import re
from typing import Optional
from urllib.parse import unquote, urljoin, urlparse

from bs4 import BeautifulSoup

from parsers.base import BaseParser

logger = logging.getLogger(__name__)

BASE_URL = "https://ibaraki1010.com"
LIST_URL = f"{BASE_URL}/"

_EXCLUDE_PATH_PATTERNS = (
    r"^/$",
    r"^/news",
    r"^/category",
    r"^/tag",
    r"^/contact",
    r"^/about",
    r"^/privacy",
    r"^/policy",
    r"^/terms",
    r"^/sitemap",
    r"^/wp-",
)

_GMAPS_COORD_PATTERNS = (
    re.compile(r"[?&]q=([-\d.]+),([-\d.]+)"),
    re.compile(r"[?&]ll=([-\d.]+),([-\d.]+)"),
    re.compile(r"[?&]query=([-\d.]+),([-\d.]+)"),
    re.compile(r"[?&]destination=([-\d.]+),([-\d.]+)"),
    re.compile(r"/@([-\d.]+),([-\d.]+)"),
)
_ADDRESS_FALLBACK_PATTERN = re.compile(r"(?:住所|所在地)\s*[:：]\s*([^\n]+)")


class IbarakiParser(BaseParser):
    prefecture = "茨城県"
    region = "関東"

    def get_list_urls(self) -> list[str]:
        return [LIST_URL]

    def get_item_urls(self, html: str, page_url: str) -> list[str]:
        soup = BeautifulSoup(html, "lxml")
        urls: list[str] = []
        seen: set[str] = set()

        for a in soup.find_all("a", href=True):
            href: str = a["href"].strip()
            if href.startswith(("mailto:", "tel:", "javascript:", "#")):
                continue

            abs_url = urljoin(BASE_URL, href)
            parsed = urlparse(abs_url)
            if parsed.scheme not in ("http", "https"):
                continue
            if "ibaraki1010.com" not in parsed.netloc:
                continue
            if any(re.search(pattern, parsed.path) for pattern in _EXCLUDE_PATH_PATTERNS):
                continue

            normalized = parsed._replace(fragment="").geturl()
            if normalized in seen:
                continue

            seen.add(normalized)
            urls.append(normalized)

        return urls

    def parse_sento(self, html: str, page_url: str) -> Optional[dict]:
        soup = BeautifulSoup(html, "lxml")

        name: Optional[str] = None
        for selector in ("h1", "h2.entry-title", "h2", ".entry-title", ".post-title"):
            tag = soup.select_one(selector)
            if not tag:
                continue
            raw = tag.get_text(" ", strip=True)
            if raw and len(raw) < 80:
                name = re.sub(r"\s*[|｜\-].*$", "", raw).strip()
                break

        if not name:
            logger.warning("name が取得できません: %s", page_url)
            return None

        address = (
            self.extract_label_value(soup, "住所")
            or self.extract_label_value(soup, "所在地")
            or self.extract_table_value(soup, "住所")
            or self.extract_table_value(soup, "所在地")
            or self._extract_address_fallback(soup)
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
                phone = tel_tag["href"].replace("tel:", "").strip()

        open_hours = (
            self.extract_label_value(soup, "営業時間")
            or self.extract_label_value(soup, "入浴時間")
            or self.extract_table_value(soup, "営業時間")
            or self.extract_table_value(soup, "入浴時間")
        )
        holiday = (
            self.extract_label_value(soup, "定休日")
            or self.extract_label_value(soup, "休日")
            or self.extract_table_value(soup, "定休日")
            or self.extract_table_value(soup, "休業日")
            or self.extract_table_value(soup, "休日")
        )

        lat, lng = self._extract_coords_from_maps_link(soup)

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

    @staticmethod
    def _extract_address_fallback(soup: BeautifulSoup) -> Optional[str]:
        text = soup.get_text("\n", strip=True)
        m = _ADDRESS_FALLBACK_PATTERN.search(text)
        if not m:
            return None
        return m.group(1).strip()

    @staticmethod
    def _extract_coords_from_maps_link(soup: BeautifulSoup) -> tuple[Optional[float], Optional[float]]:
        for a in soup.find_all("a", href=True):
            href = unquote(a["href"])
            if "google.com/maps" not in href and "maps.app.goo.gl" not in href:
                continue
            for pattern in _GMAPS_COORD_PATTERNS:
                m = pattern.search(href)
                if not m:
                    continue
                try:
                    return float(m.group(1)), float(m.group(2))
                except ValueError:
                    continue
        return None, None
