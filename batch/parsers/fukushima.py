"""福島県銭湯組合 (fukushima1010.com) パーサー。"""
import logging
import re
from typing import Optional
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup

from parsers.base import BaseParser

logger = logging.getLogger(__name__)

BASE_URL = "https://fukushima1010.com"
LIST_URL = f"{BASE_URL}/"

# Google Maps リンクから緯度経度を抽出
_GMAPS_Q_PATTERN = re.compile(r"[?&]q=([-\d.]+),([-\d.]+)")
_DESTINATION_PATTERN = re.compile(r"destination=([-\d.]+),([-\d.]+)")
_GMAPS_LL_PATTERN = re.compile(r"[?&]ll=([-\d.]+),([-\d.]+)")
_GMAPS_AT_PATTERN = re.compile(r"/@([-\d.]+),([-\d.]+)")
_GMAPS_EMBED_PATTERN = re.compile(r"!3d([-\d.]+)!.*!4d([-\d.]+)")
_GMAPS_EMBED_2D3D_PATTERN = re.compile(r"!2d([-\d.]+)!3d([-\d.]+)")

# 一覧ページから拾う個別ページ URL の候補
_DETAIL_PATH_PATTERN = re.compile(
    r"/(?:sento|bath|shop|facility|sento_list|store)/[^/?#]+/?$|"
    r"/\d{4}/\d{2}/\d{2}/[^/?#]+/?$"
)
_EXCLUDED_PATH_PATTERN = re.compile(
    r"/(?:wp-admin|wp-login|category|tag|author|feed|contact|privacy|terms)(?:/|$)"
)


class FukushimaParser(BaseParser):
    prefecture = "福島県"
    region = "東北"

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
            if "fukushima1010.com" not in parsed.netloc:
                continue
            if _EXCLUDED_PATH_PATTERN.search(parsed.path):
                continue
            if href.rstrip("/") == BASE_URL:
                continue

            # 一覧ページのカードリンクや典型的な詳細 URL を対象にする
            classes = set(a.get("class") or [])
            looks_like_card = bool(classes & {"card", "shop-card", "entry-card", "item-link"})
            if not (_DETAIL_PATH_PATTERN.search(parsed.path) or looks_like_card):
                continue

            normalized = href.split("#", 1)[0]
            if normalized not in seen:
                seen.add(normalized)
                urls.append(normalized)

        return urls

    def parse_sento(self, html: str, page_url: str) -> Optional[dict]:
        soup = BeautifulSoup(html, "lxml")

        # 銭湯名
        name: Optional[str] = None
        for selector in ("h1.entry-title", "h1.sento-name", "h1", "h2"):
            tag = soup.select_one(selector)
            if tag:
                raw = tag.get_text(strip=True)
                if raw and len(raw) < 80:
                    name = raw
                    break

        if not name:
            logger.warning("name が取得できません: %s", page_url)
            return None

        # 基本情報
        address = (
            self.extract_label_value(soup, "住所")
            or self.extract_table_value(soup, "住所")
            or None
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
        )
        holiday = (
            self.extract_label_value(soup, "定休日")
            or self.extract_label_value(soup, "休日")
            or self.extract_table_value(soup, "定休日")
            or self.extract_table_value(soup, "休日")
        )

        # 緯度経度: Google Maps リンク優先。見つからなければ None のまま返し、後段で OSM 補完対象にする。
        lat: Optional[float] = None
        lng: Optional[float] = None

        for maps_tag in soup.find_all("a", href=True):
            href: str = maps_tag["href"]
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

    def _extract_coordinates_from_url(self, url: str) -> Optional[tuple[float, float]]:
        for pattern in (
            _GMAPS_Q_PATTERN,
            _DESTINATION_PATTERN,
            _GMAPS_LL_PATTERN,
            _GMAPS_AT_PATTERN,
            _GMAPS_EMBED_PATTERN,
            _GMAPS_EMBED_2D3D_PATTERN,
        ):
            matched = pattern.search(url)
            if matched:
                try:
                    first = float(matched.group(1))
                    second = float(matched.group(2))
                    if pattern is _GMAPS_EMBED_2D3D_PATTERN:
                        return second, first
                    return first, second
                except ValueError:
                    continue

        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        for key in ("q", "ll", "destination"):
            values = query.get(key, [])
            if not values:
                continue
            parts = values[0].split(",")
            if len(parts) != 2:
                continue
            try:
                return float(parts[0]), float(parts[1])
            except ValueError:
                continue

        return None
