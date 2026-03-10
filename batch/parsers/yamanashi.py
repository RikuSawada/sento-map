"""山梨県公衆浴場業生活衛生同業組合 (sento-yamanashi.com) パーサー。"""
import logging
import re
from typing import Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from parsers.base import BaseParser

logger = logging.getLogger(__name__)

BASE_URL = "https://sento-yamanashi.com"
LIST_URL = f"{BASE_URL}/"

_PAGINATION_PATTERNS = (
    re.compile(r"/page/(\d+)/?$"),
    re.compile(r"[?&]paged=(\d+)(?:[&#].*)?$"),
    re.compile(r"[?&]page=(\d+)(?:[&#].*)?$"),
)
_DETAIL_URL_PATTERNS = (
    re.compile(r"/(sento|bath|shop)/[^/]+/?$"),
    re.compile(r"/\d{4}/\d{2}/[^/]+/?$"),
    re.compile(r"/[^/]+/?$"),
)
_GMAPS_PATTERNS = (
    re.compile(r"[?&]q=([-\d.]+),([-\d.]+)"),
    re.compile(r"[?&]ll=([-\d.]+),([-\d.]+)"),
    re.compile(r"destination=([-\d.]+),([-\d.]+)"),
    re.compile(r"daddr=([-\d.]+),([-\d.]+)"),
    re.compile(r"/@([-\d.]+),([-\d.]+),"),
)


class YamanashiParser(BaseParser):
    prefecture = "山梨県"
    region = "中部"

    def get_list_urls(self) -> list[str]:
        return [LIST_URL]

    def get_all_list_urls(self, page1_html: str) -> list[str]:
        """ページ1からページネーション URL を収集する。"""
        soup = BeautifulSoup(page1_html, "lxml")
        urls = [LIST_URL]
        seen = {LIST_URL}

        for a in soup.find_all("a", href=True):
            href = a["href"]
            if not href.startswith("http"):
                href = urljoin(BASE_URL, href)
            if "sento-yamanashi.com" not in urlparse(href).netloc:
                continue
            if self._is_pagination_url(href) and href not in seen:
                seen.add(href)
                urls.append(href)

        return urls

    def get_item_urls(self, html: str, page_url: str) -> list[str]:
        soup = BeautifulSoup(html, "lxml")
        urls: list[str] = []
        seen: set[str] = set()

        for a in soup.find_all("a", href=True):
            href = a["href"]
            if not href.startswith("http"):
                href = urljoin(BASE_URL, href)

            parsed = urlparse(href)
            if "sento-yamanashi.com" not in parsed.netloc:
                continue
            if self._is_pagination_url(href):
                continue
            if any(token in parsed.path for token in ("/category/", "/tag/", "/author/", "/wp-", "/contact", "/about")):
                continue
            if parsed.path.rstrip("/") in ("", "/"):
                continue
            if not any(pattern.search(parsed.path) for pattern in _DETAIL_URL_PATTERNS):
                continue
            if href not in seen:
                seen.add(href)
                urls.append(href)

        return urls

    def parse_sento(self, html: str, page_url: str) -> Optional[dict]:
        soup = BeautifulSoup(html, "lxml")

        name: Optional[str] = None
        for selector in ("h1.entry-title", "h1.post-title", ".entry-title", ".post-title", "h1", "h2"):
            tag = soup.select_one(selector)
            if tag:
                raw = tag.get_text(strip=True)
                if raw and len(raw) < 80:
                    name = raw
                    break

        if not name:
            logger.warning("name が取得できません: %s", page_url)
            return None

        address = self.extract_label_value(soup, "住所") or self.extract_table_value(soup, "住所") or ""
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

        open_hours = self.extract_label_value(soup, "営業時間") or self.extract_table_value(soup, "営業時間")
        holiday = (
            self.extract_label_value(soup, "定休日")
            or self.extract_label_value(soup, "休日")
            or self.extract_table_value(soup, "定休日")
            or self.extract_table_value(soup, "休業日")
        )

        lat: Optional[float] = None
        lng: Optional[float] = None
        for maps_tag in soup.find_all("a", href=True):
            href = maps_tag["href"]
            if "google.com/maps" not in href and "maps.google.com" not in href:
                continue
            for pattern in _GMAPS_PATTERNS:
                match = pattern.search(href)
                if not match:
                    continue
                try:
                    lat = float(match.group(1))
                    lng = float(match.group(2))
                except ValueError:
                    lat = None
                    lng = None
                break
            if lat is not None:
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

    @staticmethod
    def _is_pagination_url(url: str) -> bool:
        return any(pattern.search(url) for pattern in _PAGINATION_PATTERNS)
