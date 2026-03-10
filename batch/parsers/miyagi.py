"""宮城県銭湯組合 (miyagi1010.com) パーサー。"""
import logging
import re
from typing import Optional
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup

from parsers.base import BaseParser

logger = logging.getLogger(__name__)

BASE_URL = "https://miyagi1010.com"
TOP_URL = f"{BASE_URL}/"

_POST_URL_PATTERN = re.compile(r"/\d{4}/\d{2}/\d{2}/")
_GMAPS_Q_PATTERN = re.compile(r"[?&]q=([-\d.]+),([-\d.]+)")
_GMAPS_LL_PATTERN = re.compile(r"[?&]ll=([-\d.]+),([-\d.]+)")
_GMAPS_DEST_PATTERN = re.compile(r"[?&]destination=([-\d.]+),([-\d.]+)")
_GMAPS_AT_PATTERN = re.compile(r"/@([-\d.]+),([-\d.]+),")
_GMAPS_QUERY_PATTERN = re.compile(r"[?&]query=([-\d.]+),([-\d.]+)")
_GMAPS_EMBED_PATTERN = re.compile(r"!3d([-\d.]+)!.*!4d([-\d.]+)")
_LIST_PATH_KEYWORDS = (
    "/category/",
    "/tag/",
    "/author/",
    "/page/",
    "/news/",
    "/blog/",
    "/archives/",
)
_SENTO_PAGE_HINTS = ("住所", "営業時間", "定休日", "電話", "TEL")


class MiyagiParser(BaseParser):
    prefecture = "宮城県"
    region = "東北"

    def get_list_urls(self) -> list[str]:
        return [TOP_URL]

    def get_all_list_urls(self, page1_html: str) -> list[str]:
        """トップページ HTML から一覧ページ候補を収集する。"""
        soup = BeautifulSoup(page1_html, "lxml")
        urls: list[str] = [TOP_URL]
        seen: set[str] = {TOP_URL}

        for a in soup.find_all("a", href=True):
            href = self._normalize_href(a["href"])
            if not href or not self._is_internal_url(href):
                continue

            text = a.get_text(" ", strip=True)
            if not self._is_list_like_url(href, text):
                continue

            if href not in seen:
                seen.add(href)
                urls.append(href)

        return urls

    def get_item_urls(self, html: str, page_url: str) -> list[str]:
        """一覧ページから銭湯個別ページ URL を抽出する。"""
        soup = BeautifulSoup(html, "lxml")
        urls: list[str] = []
        seen: set[str] = set()

        for a in soup.select("article a[href], .post a[href], .entry a[href], h2 a[href], h3 a[href]"):
            href = self._normalize_href(a.get("href", ""))
            if href and self._is_sento_detail_url(href) and href not in seen:
                seen.add(href)
                urls.append(href)

        if urls:
            return urls

        for a in soup.find_all("a", href=True):
            href = self._normalize_href(a["href"])
            if href and self._is_sento_detail_url(href) and href not in seen:
                seen.add(href)
                urls.append(href)

        return urls

    def parse_sento(self, html: str, page_url: str) -> Optional[dict]:
        soup = BeautifulSoup(html, "lxml")

        if self._is_list_like_url(page_url, "") and not self._looks_like_sento_page(soup):
            return None

        name: Optional[str] = None
        for selector in ("h1.entry-title", "h1.post-title", ".entry-title", "h1", "h2"):
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

        address = self.extract_label_value(soup, "住所") or self.extract_table_value(soup, "住所") or ""
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

        open_hours = self.extract_label_value(soup, "営業時間") or self.extract_table_value(soup, "営業時間")
        holiday = (
            self.extract_label_value(soup, "定休日")
            or self.extract_label_value(soup, "休日")
            or self.extract_table_value(soup, "定休日")
            or self.extract_table_value(soup, "休業日")
            or self.extract_table_value(soup, "休日")
        )

        lat, lng = self._extract_coordinates(soup)

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

    def _extract_coordinates(self, soup: BeautifulSoup) -> tuple[Optional[float], Optional[float]]:
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "google.com/maps" not in href and "maps.app.goo.gl" not in href:
                continue

            coords = self._extract_coordinates_from_url(href)
            if coords is not None:
                return coords

        for iframe in soup.find_all("iframe", src=True):
            src = iframe["src"]
            if "google.com/maps" not in src and "maps.google.com" not in src:
                continue

            coords = self._extract_coordinates_from_url(src)
            if coords is not None:
                return coords

        return None, None

    def _extract_coordinates_from_url(self, url: str) -> Optional[tuple[float, float]]:
        for pattern in (
            _GMAPS_Q_PATTERN,
            _GMAPS_LL_PATTERN,
            _GMAPS_DEST_PATTERN,
            _GMAPS_QUERY_PATTERN,
            _GMAPS_AT_PATTERN,
            _GMAPS_EMBED_PATTERN,
        ):
            matched = pattern.search(url)
            if matched:
                try:
                    return float(matched.group(1)), float(matched.group(2))
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

    def _normalize_href(self, href: str) -> Optional[str]:
        if not href or href.startswith("#"):
            return None
        normalized = href.strip()
        if not normalized.startswith("http"):
            normalized = urljoin(BASE_URL, normalized)
        return normalized.rstrip("/")

    def _is_internal_url(self, url: str) -> bool:
        netloc = urlparse(url).netloc.lower()
        return netloc in {"miyagi1010.com", "www.miyagi1010.com"}

    def _is_list_like_url(self, href: str, text: str) -> bool:
        parsed = urlparse(href)
        lowered_text = text.lower()

        if any(keyword in parsed.path for keyword in _LIST_PATH_KEYWORDS):
            return True
        if any(token in lowered_text for token in ("一覧", "エリア", "search", "カテゴリ", "銭湯")):
            return True
        if "cat" in parse_qs(parsed.query):
            return True
        return False

    def _is_sento_detail_url(self, url: str) -> bool:
        if not self._is_internal_url(url):
            return False

        parsed = urlparse(url)
        path = parsed.path.lower()
        if any(token in path for token in ("/wp-admin", "/wp-login", "/wp-json", "/feed")):
            return False
        if any(keyword in path for keyword in _LIST_PATH_KEYWORDS):
            return False
        if _POST_URL_PATTERN.search(path):
            return True
        if path in ("", "/"):
            return False
        if path in ("/about", "/contact", "/privacy-policy", "/sitemap"):
            return False
        return len(path.strip("/").split("/")) >= 1

    def _looks_like_sento_page(self, soup: BeautifulSoup) -> bool:
        text = soup.get_text(separator="\n")
        return sum(1 for hint in _SENTO_PAGE_HINTS if hint in text) >= 2
