"""新潟県銭湯組合 (niigata1010.com) パーサー。"""
import logging
import re
from typing import Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from parsers.base import BaseParser

logger = logging.getLogger(__name__)

BASE_URL = "https://niigata1010.com"
LIST_URL = f"{BASE_URL}/sento-list/"

# 個別ページの候補となる URL パターン
_DETAIL_PATH_PATTERNS = (
    re.compile(r"/sento/[^/?#]+/?$"),
    re.compile(r"/sento_list/[^/?#]+/?$"),
    re.compile(r"/bath/[^/?#]+/?$"),
    re.compile(r"/\d{4}/\d{2}/[^/?#]+/?$"),
)

# 一覧・ナビゲーション等として除外する URL 文字列
_EXCLUDED_PATH_KEYWORDS = (
    "/sento-list/",
    "/category/",
    "/tag/",
    "/author/",
    "/page/",
    "/news/",
    "/about/",
    "/contact/",
    "/wp-admin",
    "/wp-login",
)

_GMAPS_Q_PATTERN = re.compile(r"[?&]q=([-\d.]+)(?:%2C|,)([-\d.]+)")
_DESTINATION_PATTERN = re.compile(r"destination=([-\d.]+)(?:%2C|,)([-\d.]+)")
_GMAPS_LL_PATTERN = re.compile(r"[?&]ll=([-\d.]+)(?:%2C|,)([-\d.]+)")
_GMAPS_AT_PATTERN = re.compile(r"/@([-\d.]+),([-\d.]+)")
_GMAPS_3D4D_PATTERN = re.compile(r"!3d([-\d.]+)!4d([-\d.]+)")


class NiigataParser(BaseParser):
    prefecture = "新潟県"
    region = "中部"

    def get_list_urls(self) -> list[str]:
        return [LIST_URL]

    def get_item_urls(self, html: str, page_url: str) -> list[str]:
        soup = BeautifulSoup(html, "lxml")
        urls: list[str] = []
        seen: set[str] = set()

        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if not href or href.startswith(("#", "javascript:")):
                continue

            if not href.startswith("http"):
                href = urljoin(BASE_URL, href)

            parsed = urlparse(href)
            if parsed.netloc not in {"niigata1010.com", "www.niigata1010.com"}:
                continue
            if any(keyword in parsed.path for keyword in _EXCLUDED_PATH_KEYWORDS):
                continue

            if any(pat.search(parsed.path) for pat in _DETAIL_PATH_PATTERNS):
                if href not in seen:
                    seen.add(href)
                    urls.append(href)

        return urls

    def parse_sento(self, html: str, page_url: str) -> Optional[dict]:
        soup = BeautifulSoup(html, "lxml")

        name: Optional[str] = None
        for selector in ("h1.entry-title", "h1.post-title", "h1", "h2.entry-title", "h2"):
            tag = soup.select_one(selector)
            if not tag:
                continue
            raw = tag.get_text(strip=True)
            if raw and len(raw) <= 80:
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
        open_hours = self.extract_label_value(soup, "営業時間") or self.extract_table_value(soup, "営業時間")
        holiday = (
            self.extract_label_value(soup, "定休日")
            or self.extract_label_value(soup, "休日")
            or self.extract_table_value(soup, "定休日")
            or self.extract_table_value(soup, "休業日")
            or self.extract_table_value(soup, "休日")
        )

        if not phone:
            tel_tag = soup.find("a", href=re.compile(r"^tel:"))
            if tel_tag:
                phone = tel_tag["href"].replace("tel:", "").strip()

        lat: Optional[float] = None
        lng: Optional[float] = None
        for maps_tag in soup.find_all("a", href=True):
            href = maps_tag["href"]
            if "google.com/maps" not in href and "maps.google." not in href:
                continue

            m = (
                _GMAPS_Q_PATTERN.search(href)
                or _DESTINATION_PATTERN.search(href)
                or _GMAPS_LL_PATTERN.search(href)
                or _GMAPS_AT_PATTERN.search(href)
                or _GMAPS_3D4D_PATTERN.search(href)
            )
            if not m:
                continue

            try:
                lat = float(m.group(1))
                lng = float(m.group(2))
                break
            except ValueError:
                continue

        return self.make_sento_dict(
            name=name,
            address=address,
            lat=lat,
            lng=lng,
            phone=phone,
            open_hours=open_hours,
            holiday=holiday,
            source_url=page_url,
            facility_type="sento",
        )
