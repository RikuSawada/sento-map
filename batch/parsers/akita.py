"""秋田県銭湯 (akita-sento.com) パーサー。

静的 HTML サイトを前提に BeautifulSoup のみで抽出する。
"""
import logging
import re
from typing import Optional
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup

from parsers.base import BaseParser

logger = logging.getLogger(__name__)

BASE_URL = "https://akita-sento.com"
LIST_URLS = [
    f"{BASE_URL}/",
    f"{BASE_URL}/sento/",
]

_DETAIL_URL_PATTERNS = [
    re.compile(r"/sento/[^/?#]+/?$"),
    re.compile(r"/bath/[^/?#]+/?$"),
    re.compile(r"/shop/[^/?#]+/?$"),
    re.compile(r"/facility/[^/?#]+/?$"),
]
_LIST_OR_INDEX_HINTS = ("/category/", "/tag/", "/author/", "/page/", "/news/", "/blog/")

_GMAPS_Q_PATTERN = re.compile(r"[?&]q=([-\d.]+),([-\d.]+)")
_GMAPS_QUERY_PATTERN = re.compile(r"[?&]query=([-\d.]+),([-\d.]+)")
_GMAPS_DEST_PATTERN = re.compile(r"[?&]destination=([-\d.]+),([-\d.]+)")
_GMAPS_LL_PATTERN = re.compile(r"[?&]ll=([-\d.]+),([-\d.]+)")
_GMAPS_AT_PATTERN = re.compile(r"/@([-\d.]+),([-\d.]+)")
_GMAPS_EMBED_PATTERN = re.compile(r"!3d([-\d.]+)!.*!4d([-\d.]+)")
_GMAPS_EMBED_2D3D_PATTERN = re.compile(r"!2d([-\d.]+)!3d([-\d.]+)")


class AkitaParser(BaseParser):
    prefecture = "秋田県"
    region = "東北"

    def get_list_urls(self) -> list[str]:
        return LIST_URLS

    def get_item_urls(self, html: str, page_url: str) -> list[str]:
        soup = BeautifulSoup(html, "lxml")
        urls: list[str] = []
        seen: set[str] = set()

        for a in soup.find_all("a", href=True):
            href: str = a["href"].strip()
            if not href:
                continue

            if not href.startswith("http"):
                href = urljoin(BASE_URL, href)

            parsed = urlparse(href)
            if "akita-sento.com" not in parsed.netloc:
                continue

            path = parsed.path or "/"
            if path in ("/", "/sento/"):
                continue
            if any(hint in path for hint in _LIST_OR_INDEX_HINTS):
                continue

            if any(pat.search(path) for pat in _DETAIL_URL_PATTERNS):
                if href not in seen:
                    seen.add(href)
                    urls.append(href)

        logger.info("秋田一覧: %d 件取得", len(urls))
        return urls

    def parse_sento(self, html: str, page_url: str) -> Optional[dict]:
        soup = BeautifulSoup(html, "lxml")

        name: Optional[str] = None
        for selector in (
            "h1.entry-title",
            "h1.post-title",
            "h1.page-title",
            ".sento-name",
            "main h1",
            "h1",
            "h2",
        ):
            tag = soup.select_one(selector)
            if not tag:
                continue
            raw = tag.get_text(strip=True)
            if raw and len(raw) < 80:
                name = raw
                break

        if not name:
            logger.warning("name が取得できません: %s", page_url)
            return None

        address = (
            self.extract_label_value(soup, "住所")
            or self.extract_table_value(soup, "住所")
            or (soup.find("address").get_text(" ", strip=True) if soup.find("address") else None)
        )
        if not address:
            logger.warning("address が取得できません: %s", page_url)
            return None

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

        open_hours = (
            self.extract_label_value(soup, "営業時間")
            or self.extract_label_value(soup, "営業時刻")
            or self.extract_table_value(soup, "営業時間")
        )
        holiday = (
            self.extract_label_value(soup, "定休日")
            or self.extract_label_value(soup, "休業日")
            or self.extract_label_value(soup, "休日")
            or self.extract_table_value(soup, "定休日")
            or self.extract_table_value(soup, "休業日")
        )

        lat: Optional[float] = None
        lng: Optional[float] = None

        for tag in soup.find_all("a", href=True):
            href = str(tag["href"])
            if "google." not in href or "/maps" not in href:
                continue
            coords = self._extract_coordinates_from_url(href)
            if coords is not None:
                lat, lng = coords
                break

        if lat is None:
            for iframe in soup.find_all("iframe", src=True):
                src = str(iframe["src"])
                if "google." not in src or "/maps" not in src:
                    continue
                coords = self._extract_coordinates_from_url(src)
                if coords is not None:
                    lat, lng = coords
                    break

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

    def _extract_coordinates_from_url(self, url: str) -> Optional[tuple[float, float]]:
        for pat in (
            _GMAPS_Q_PATTERN,
            _GMAPS_QUERY_PATTERN,
            _GMAPS_DEST_PATTERN,
            _GMAPS_LL_PATTERN,
            _GMAPS_AT_PATTERN,
            _GMAPS_EMBED_PATTERN,
            _GMAPS_EMBED_2D3D_PATTERN,
        ):
            m = pat.search(url)
            if not m:
                continue
            try:
                first = float(m.group(1))
                second = float(m.group(2))
                if pat is _GMAPS_EMBED_2D3D_PATTERN:
                    return second, first
                return first, second
            except ValueError:
                continue

        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        for key in ("q", "ll", "query", "destination"):
            value = query.get(key, [])
            if not value:
                continue
            parts = value[0].split(",")
            if len(parts) != 2:
                continue
            try:
                return float(parts[0]), float(parts[1])
            except ValueError:
                continue

        return None
