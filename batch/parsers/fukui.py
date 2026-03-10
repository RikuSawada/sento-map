"""福井県銭湯 (fukui1010.com) パーサー。"""
import logging
import re
from typing import Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from parsers.base import BaseParser

logger = logging.getLogger(__name__)

BASE_URL = "https://fukui1010.com"
LIST_URL = BASE_URL + "/"

_COORD_Q_PATTERN = re.compile(r"[?&]q=([\-\d.]+),([\-\d.]+)")
_COORD_LL_PATTERN = re.compile(r"[?&]ll=([\-\d.]+),([\-\d.]+)")
_COORD_DEST_PATTERN = re.compile(r"[?&]destination=([\-\d.]+),([\-\d.]+)")
_COORD_AT_PATTERN = re.compile(r"@([\-\d.]+),([\-\d.]+)")
_COORD_EMBED_PATTERN = re.compile(r"!3d([\-\d.]+)!4d([\-\d.]+)")
_COORD_EMBED_2D3D_PATTERN = re.compile(r"!2d([\-\d.]+)!3d([\-\d.]+)")


class FukuiParser(BaseParser):
    prefecture = "福井県"
    region = "中部"

    def get_list_urls(self) -> list[str]:
        return [LIST_URL]

    def get_item_urls(self, html: str, page_url: str) -> list[str]:
        soup = BeautifulSoup(html, "lxml")
        urls: list[str] = []
        seen: set[str] = set()

        for a in soup.find_all("a", href=True):
            href = str(a["href"]).strip()
            if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
                continue

            full_url = urljoin(BASE_URL, href)
            parsed = urlparse(full_url)
            if "fukui1010.com" not in parsed.netloc:
                continue

            path = parsed.path.rstrip("/").lower()
            if not path or path in {"", "/"}:
                continue

            # 一覧や案内ページを除き、銭湯詳細と推定できるリンクのみ対象にする。
            text = a.get_text(" ", strip=True)
            is_detail_like = (
                any(token in path for token in ("/sento/", "/bath/", "/shop/", "/store/", "/spot/"))
                or any(token in text for token in ("銭湯", "湯", "温泉"))
            )
            if not is_detail_like:
                continue

            if full_url not in seen:
                seen.add(full_url)
                urls.append(full_url)

        return urls

    def parse_sento(self, html: str, page_url: str) -> Optional[dict]:
        soup = BeautifulSoup(html, "lxml")

        name: Optional[str] = None
        for selector in ("h1", "h2", ".entry-title", ".post-title"):
            tag = soup.select_one(selector)
            if not tag:
                continue
            raw = tag.get_text(" ", strip=True)
            if raw and len(raw) < 80:
                name = re.sub(r"\s*[\[【].+?[\]】]\s*$", "", raw).strip()
                break
        if not name:
            logger.warning("name が取得できません: %s", page_url)
            return None

        address = (
            self.extract_label_value(soup, "住所")
            or self.extract_label_value(soup, "所在地")
            or self.extract_table_value(soup, "住所")
            or self.extract_table_value(soup, "所在地")
            or ""
        )
        if not address:
            for candidate in soup.stripped_strings:
                if "福井県" in candidate:
                    address = candidate.strip()
                    break

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
            or self.extract_label_value(soup, "営業")
            or self.extract_table_value(soup, "営業時間")
            or self.extract_table_value(soup, "営業")
        )
        holiday = (
            self.extract_label_value(soup, "定休日")
            or self.extract_label_value(soup, "休日")
            or self.extract_label_value(soup, "休業日")
            or self.extract_table_value(soup, "定休日")
            or self.extract_table_value(soup, "休日")
            or self.extract_table_value(soup, "休業日")
        )

        lat: Optional[float] = None
        lng: Optional[float] = None
        for tag in soup.find_all(["a", "iframe"], href=True) + soup.find_all("iframe", src=True):
            url = tag.get("href") or tag.get("src")
            if not url:
                continue
            coord = _extract_coords_from_maps_url(str(url))
            if coord:
                lat, lng = coord
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


def _extract_coords_from_maps_url(url: str) -> Optional[tuple[float, float]]:
    if "google.com/maps" not in url and "maps.app.goo.gl" not in url:
        return None

    for pattern in (
        _COORD_Q_PATTERN,
        _COORD_LL_PATTERN,
        _COORD_DEST_PATTERN,
        _COORD_AT_PATTERN,
        _COORD_EMBED_PATTERN,
    ):
        m = pattern.search(url)
        if not m:
            continue
        try:
            return float(m.group(1)), float(m.group(2))
        except ValueError:
            return None

    m = _COORD_EMBED_2D3D_PATTERN.search(url)
    if m:
        try:
            return float(m.group(2)), float(m.group(1))
        except ValueError:
            return None

    return None
