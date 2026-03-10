"""岐阜銭湯組合 (gifu1010.com) パーサー。"""
import logging
import re
from typing import Optional
from urllib.parse import parse_qs, unquote, urljoin, urlparse

from bs4 import BeautifulSoup

from parsers.base import BaseParser

logger = logging.getLogger(__name__)

BASE_URL = "https://gifu1010.com"
LIST_URL = f"{BASE_URL}/"

_DETAIL_URL_PATTERN = re.compile(r"/sento/[^/?#]+/?$")
_COORD_PAIR_PATTERN = re.compile(r"\s*([\-\d.]+)\s*,\s*([\-\d.]+)\s*")
_AT_COORD_PATTERN = re.compile(r"/@([\-\d.]+),([\-\d.]+)(?:,|$)")


class GifuParser(BaseParser):
    prefecture = "岐阜県"
    region = "中部"

    def get_list_urls(self) -> list[str]:
        return [LIST_URL]

    def get_item_urls(self, html: str, page_url: str) -> list[str]:
        soup = BeautifulSoup(html, "lxml")
        urls: list[str] = []
        seen: set[str] = set()

        for a in soup.find_all("a", href=True):
            href: str = a["href"]
            if not _DETAIL_URL_PATTERN.search(href):
                continue
            if not href.startswith("http"):
                href = urljoin(BASE_URL, href)
            if href not in seen:
                seen.add(href)
                urls.append(href)

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
            or self._extract_text_by_selector(soup, [".address", ".shopAddress", "address"])
            or ""
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
                phone = tel_tag["href"].replace("tel:", "").strip()

        open_hours = (
            self.extract_label_value(soup, "営業時間")
            or self.extract_table_value(soup, "営業時間")
            or self.extract_table_value(soup, "営業")
        )
        holiday = (
            self.extract_label_value(soup, "定休日")
            or self.extract_label_value(soup, "休日")
            or self.extract_table_value(soup, "定休日")
            or self.extract_table_value(soup, "休日")
        )

        lat: Optional[float] = None
        lng: Optional[float] = None
        for a in soup.find_all("a", href=True):
            coords = self._extract_coords_from_maps_url(a["href"])
            if coords is None:
                continue
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

    @staticmethod
    def _extract_name(soup: BeautifulSoup) -> Optional[str]:
        for selector in ("h1", "h2", ".sentoName", ".shopName", ".entry-title"):
            tag = soup.select_one(selector)
            if not tag:
                continue
            raw = tag.get_text(strip=True)
            if raw and len(raw) < 80:
                return raw

        title = soup.title.get_text(strip=True) if soup.title else ""
        if title:
            head = re.split(r"[|｜：:]", title)[0].strip()
            if head and len(head) < 80:
                return head

        return None

    @staticmethod
    def _extract_text_by_selector(soup: BeautifulSoup, selectors: list[str]) -> Optional[str]:
        for selector in selectors:
            tag = soup.select_one(selector)
            if tag:
                value = tag.get_text(" ", strip=True)
                if value:
                    return value
        return None

    @staticmethod
    def _extract_coords_from_maps_url(url: str) -> Optional[tuple[float, float]]:
        parsed = urlparse(url)

        # 短縮URLや非地図URLは対象外
        if "google" not in parsed.netloc and "google" not in parsed.path:
            return None
        if "maps" not in parsed.path and "maps" not in parsed.netloc:
            return None

        query = parse_qs(parsed.query)
        for key in ("q", "ll", "destination"):
            raw = query.get(key, [""])[0]
            m = _COORD_PAIR_PATTERN.fullmatch(unquote(raw))
            if not m:
                continue
            try:
                return float(m.group(1)), float(m.group(2))
            except ValueError:
                continue

        m = _AT_COORD_PATTERN.search(unquote(url))
        if m:
            try:
                return float(m.group(1)), float(m.group(2))
            except ValueError:
                return None

        return None
