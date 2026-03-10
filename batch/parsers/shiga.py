"""滋賀県銭湯組合 (shiga1010.com) パーサー。"""
import logging
import re
from typing import Optional
from urllib.parse import parse_qs, unquote, urljoin, urlparse

from bs4 import BeautifulSoup

from parsers.base import BaseParser

logger = logging.getLogger(__name__)

BASE_URL = "https://shiga1010.com"
LIST_URL = f"{BASE_URL}/"

_DETAIL_HINTS = (
    "/sento/",
    "/bath/",
    "/bathhouse/",
    "/shop/",
    "/introduce/",
)
_EXCLUDE_PATH_KEYWORDS = (
    "/contact",
    "/privacy",
    "/policy",
    "/about",
    "/news",
    "/category/",
    "/tag/",
    "/feed",
    "/wp-admin",
    "/wp-json",
)
_SKIP_EXT_PATTERN = re.compile(r"\.(?:pdf|jpg|jpeg|png|gif|webp|svg|zip)$", re.IGNORECASE)
_PHONE_PATTERN = re.compile(r"\d{2,4}-\d{2,4}-\d{3,4}")

_GMAPS_Q_PATTERN = re.compile(r"[?&]q=([-\d.]+),([-\d.]+)")
_GMAPS_LL_PATTERN = re.compile(r"[?&]ll=([-\d.]+),([-\d.]+)")
_DESTINATION_PATTERN = re.compile(r"[?&]destination=([-\d.]+),([-\d.]+)")
_CENTER_PATTERN = re.compile(r"[?&]center=([-\d.]+)(?:%2C|,)([-\d.]+)")
_AT_PATTERN = re.compile(r"/@([-\d.]+),([-\d.]+)")
_EMBED_PATTERN = re.compile(r"!3d([-\d.]+)!4d([-\d.]+)")


class ShigaParser(BaseParser):
    prefecture = "滋賀県"
    region = "近畿"

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

            url = href if href.startswith("http") else urljoin(BASE_URL, href)
            parsed = urlparse(url)
            if "shiga1010.com" not in parsed.netloc:
                continue
            if _SKIP_EXT_PATTERN.search(parsed.path):
                continue
            if url == page_url or parsed.path in ("", "/"):
                continue
            if any(k in parsed.path for k in _EXCLUDE_PATH_KEYWORDS):
                continue

            anchor_text = a.get_text(" ", strip=True)
            if self._is_detail_candidate(parsed.path, anchor_text) and url not in seen:
                seen.add(url)
                urls.append(url)

        return urls

    def parse_sento(self, html: str, page_url: str) -> Optional[dict]:
        soup = BeautifulSoup(html, "lxml")

        name: Optional[str] = None
        for selector in ("h1.entry-title", "h1", "h2.entry-title", "h2"):
            tag = soup.select_one(selector)
            if not tag:
                continue
            raw = tag.get_text(strip=True)
            if raw and len(raw) < 80:
                name = raw
                break

        if not name:
            title = soup.title.get_text(strip=True) if soup.title else ""
            title = re.sub(r"\s*[\-|｜|].*$", "", title).strip()
            if title:
                name = title

        if not name:
            logger.warning("name が取得できません: %s", page_url)
            return None

        address = (
            self.extract_label_value(soup, "住所")
            or self.extract_table_value(soup, "住所")
            or self._extract_by_text_pattern(soup.get_text("\n", strip=True), "住所")
            or ""
        )

        phone = (
            self.extract_label_value(soup, "電話")
            or self.extract_label_value(soup, "TEL")
            or self.extract_table_value(soup, "電話")
            or self.extract_table_value(soup, "TEL")
        )
        if not phone:
            tel_tag = soup.find("a", href=re.compile(r"^tel:"))
            if tel_tag:
                phone = str(tel_tag["href"]).replace("tel:", "").strip()
            else:
                text_match = _PHONE_PATTERN.search(soup.get_text(" ", strip=True))
                if text_match:
                    phone = text_match.group(0)

        open_hours = (
            self.extract_label_value(soup, "営業時間")
            or self.extract_table_value(soup, "営業時間")
            or self._extract_by_text_pattern(soup.get_text("\n", strip=True), "営業時間")
        )
        holiday = (
            self.extract_label_value(soup, "定休日")
            or self.extract_label_value(soup, "休日")
            or self.extract_table_value(soup, "定休日")
            or self.extract_table_value(soup, "休日")
            or self._extract_by_text_pattern(soup.get_text("\n", strip=True), "定休日")
        )

        lat: Optional[float] = None
        lng: Optional[float] = None

        for tag in soup.find_all(["a", "iframe"], href=True):
            href = str(tag["href"])
            if "google." not in href or "maps" not in href:
                continue
            lat, lng = self._extract_coords_from_gmaps_url(href)
            if lat is not None:
                break

        if lat is None:
            for iframe in soup.find_all("iframe", src=True):
                src = str(iframe["src"])
                if "google." not in src or "maps" not in src:
                    continue
                lat, lng = self._extract_coords_from_gmaps_url(src)
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
    def _is_detail_candidate(path: str, anchor_text: str) -> bool:
        if any(hint in path for hint in _DETAIL_HINTS):
            return True
        if "銭湯" in anchor_text or "湯" in anchor_text:
            # 一覧/地図リンクは除外する。
            return not any(x in path for x in ("/list", "/map"))
        return False

    @staticmethod
    def _extract_by_text_pattern(text: str, label: str) -> Optional[str]:
        m = re.search(rf"{re.escape(label)}\s*[:：]\s*([^\n]+)", text)
        if m:
            return m.group(1).strip()
        return None

    @staticmethod
    def _extract_coords_from_gmaps_url(url: str) -> tuple[Optional[float], Optional[float]]:
        decoded = unquote(url)

        for pattern in (_GMAPS_Q_PATTERN, _DESTINATION_PATTERN, _GMAPS_LL_PATTERN, _CENTER_PATTERN, _AT_PATTERN):
            m = pattern.search(decoded)
            if m:
                try:
                    return float(m.group(1)), float(m.group(2))
                except ValueError:
                    pass

        m_embed = _EMBED_PATTERN.search(decoded)
        if m_embed:
            try:
                return float(m_embed.group(1)), float(m_embed.group(2))
            except ValueError:
                pass

        parsed = urlparse(decoded)
        qs = parse_qs(parsed.query)
        if "query" in qs:
            q = qs["query"][0]
            m = re.search(r"([-\d.]+),([-\d.]+)", q)
            if m:
                try:
                    return float(m.group(1)), float(m.group(2))
                except ValueError:
                    pass

        return None, None
