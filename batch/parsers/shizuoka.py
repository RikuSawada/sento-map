"""静岡県銭湯組合 (shizuoka1010.com) パーサー。"""
import logging
import re
from typing import Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from parsers.base import BaseParser

logger = logging.getLogger(__name__)

BASE_URL = "https://shizuoka1010.com"
LIST_URL = f"{BASE_URL}/"

_GOOGLE_MAP_HOST_PATTERN = re.compile(r"(?:^|\.)google\.[^/]+$")
_MAPS_COORD_PATTERNS = (
    re.compile(r"[?&]q=([-\d.]+),([-\d.]+)"),
    re.compile(r"[?&]ll=([-\d.]+),([-\d.]+)"),
    re.compile(r"[?&]destination=([-\d.]+),([-\d.]+)"),
    re.compile(r"[?&]daddr=([-\d.]+),([-\d.]+)"),
    re.compile(r"@([-\d.]+),([-\d.]+),"),
    re.compile(r"!3d([-\d.]+)!.*!4d([-\d.]+)"),
)
_TEL_INLINE_PATTERN = re.compile(r"(?:TEL|電話)\s*[:：]?\s*(\d{2,4}-\d{2,4}-\d{3,4})")
_STATIC_FILE_PATTERN = re.compile(r"\.(?:jpg|jpeg|png|gif|svg|pdf|zip)$", re.IGNORECASE)
_EXCLUDED_PATH_PARTS = (
    "/news",
    "/topics",
    "/blog",
    "/about",
    "/contact",
    "/privacy",
    "/policy",
    "/association",
    "/kumiai",
)
_DETAIL_HINT_PARTS = ("/shop/", "/sento/", "/bath/", "/store/")


class ShizuokaParser(BaseParser):
    prefecture = "静岡県"
    region = "中部"

    def get_list_urls(self) -> list[str]:
        return [LIST_URL]

    def get_item_urls(self, html: str, page_url: str) -> list[str]:
        soup = BeautifulSoup(html, "lxml")
        urls: list[str] = []
        seen: set[str] = set()
        normalized_page_url = self._normalize_url(page_url)

        for a in soup.find_all("a", href=True):
            href = str(a["href"]).strip()
            if not href:
                continue
            abs_url = self._normalize_url(urljoin(BASE_URL, href))
            if not abs_url:
                continue
            if abs_url == normalized_page_url:
                continue
            if not self._is_candidate_detail_url(abs_url):
                continue
            if abs_url in seen:
                continue
            seen.add(abs_url)
            urls.append(abs_url)

        return urls

    def parse_sento(self, html: str, page_url: str) -> Optional[dict]:
        soup = BeautifulSoup(html, "lxml")

        name = self._extract_name(soup)
        if not name:
            logger.warning("name が取得できません: %s", page_url)
            return None

        address = self._extract_address(soup)
        if not address:
            logger.warning("address が取得できません: %s", page_url)
            return None

        phone = self._extract_phone(soup)
        open_hours = (
            self.extract_label_value(soup, "営業時間")
            or self.extract_table_value(soup, "営業時間")
            or self.extract_table_value(soup, "営業")
        )
        holiday = (
            self.extract_label_value(soup, "定休日")
            or self.extract_label_value(soup, "休日")
            or self.extract_table_value(soup, "定休日")
            or self.extract_table_value(soup, "休業日")
            or self.extract_table_value(soup, "休日")
        )

        lat, lng = self._extract_coords(soup)

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
        for selector in ("h1", "h2", ".entry-title", ".post-title", ".shop-title"):
            tag = soup.select_one(selector)
            if not tag:
                continue
            raw = tag.get_text(strip=True)
            if raw and len(raw) < 80:
                return raw
        title_tag = soup.find("title")
        if title_tag:
            raw_title = title_tag.get_text(strip=True)
            if raw_title:
                return raw_title.split("|")[0].split("｜")[0].strip()
        return None

    def _extract_address(self, soup: BeautifulSoup) -> Optional[str]:
        address = (
            self.extract_label_value(soup, "住所")
            or self.extract_table_value(soup, "住所")
        )
        if address:
            return address

        text = soup.get_text(" ", strip=True)
        m = re.search(r"(静岡県[^ ]{3,100})", text)
        return m.group(1) if m else None

    def _extract_phone(self, soup: BeautifulSoup) -> Optional[str]:
        tel_link = soup.find("a", href=re.compile(r"^tel:"))
        if tel_link:
            return str(tel_link["href"]).replace("tel:", "").strip()

        phone = (
            self.extract_label_value(soup, "TEL")
            or self.extract_label_value(soup, "電話")
            or self.extract_table_value(soup, "TEL")
            or self.extract_table_value(soup, "電話")
        )
        if phone:
            return phone

        m = _TEL_INLINE_PATTERN.search(soup.get_text(" ", strip=True))
        return m.group(1) if m else None

    def _extract_coords(self, soup: BeautifulSoup) -> tuple[Optional[float], Optional[float]]:
        for tag in soup.find_all(["a", "iframe"], href=True):
            lat, lng = self._extract_coords_from_url(str(tag["href"]))
            if lat is not None:
                return lat, lng

        for iframe in soup.find_all("iframe", src=True):
            lat, lng = self._extract_coords_from_url(str(iframe["src"]))
            if lat is not None:
                return lat, lng

        return None, None

    def _extract_coords_from_url(self, url: str) -> tuple[Optional[float], Optional[float]]:
        try:
            parsed = urlparse(url)
        except ValueError:
            return None, None

        host = parsed.netloc.lower()
        if "maps.app.goo.gl" not in host and not _GOOGLE_MAP_HOST_PATTERN.search(host):
            return None, None
        if "maps" not in parsed.path and "maps" not in url and "goo.gl" not in host:
            return None, None

        for pattern in _MAPS_COORD_PATTERNS:
            m = pattern.search(url)
            if not m:
                continue
            try:
                return float(m.group(1)), float(m.group(2))
            except ValueError:
                continue
        return None, None

    def _is_candidate_detail_url(self, url: str) -> bool:
        parsed = urlparse(url)
        if "shizuoka1010.com" not in parsed.netloc.lower():
            return False
        if parsed.scheme not in ("http", "https"):
            return False
        if _STATIC_FILE_PATTERN.search(parsed.path):
            return False
        lowered = parsed.path.lower()
        if any(part in lowered for part in _EXCLUDED_PATH_PARTS):
            return False
        if any(part in lowered for part in _DETAIL_HINT_PARTS):
            return True
        depth = len([seg for seg in lowered.split("/") if seg])
        return depth >= 1

    @staticmethod
    def _normalize_url(url: str) -> str:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return ""
        clean = parsed._replace(fragment="").geturl()
        return clean.rstrip("/")
