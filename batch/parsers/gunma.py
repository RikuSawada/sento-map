"""群馬県公衆浴場業生活衛生同業組合 (gunma1010.com) パーサー。"""
import logging
import re
from typing import Optional
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup

from parsers.base import BaseParser

logger = logging.getLogger(__name__)

BASE_URL = "https://gunma1010.com"
TOP_URL = f"{BASE_URL}/"

# WordPress 投稿 URL: /YYYY/MM/DD/slug/
_POST_URL_PATTERN = re.compile(r"/\d{4}/\d{2}/\d{2}/[^/]+/?$")
# Google Maps リンクの座標パターン
_GMAPS_Q_PATTERN = re.compile(r"[?&]q=([-\d.]+),([-\d.]+)")
_GMAPS_LL_PATTERN = re.compile(r"[?&]ll=([-\d.]+),([-\d.]+)")
_GMAPS_DEST_PATTERN = re.compile(r"[?&]destination=([-\d.]+),([-\d.]+)")
_GMAPS_DADDR_PATTERN = re.compile(r"[?&]daddr=([-\d.]+),([-\d.]+)")
_GMAPS_AT_PATTERN = re.compile(r"/@([-\d.]+),([-\d.]+)")

# 一覧ページで使われやすいキーワード
_LIST_TEXT_KEYWORDS = ("一覧", "エリア", "地区", "地域", "市", "郡")
_LIST_PATH_KEYWORDS = ("/category/", "/tag/", "/area/", "/list/", "/archive/")
# 個別ページ名らしいアンカーテキスト
_DETAIL_TEXT_HINTS = ("湯", "温泉", "浴場", "銭湯")
# 個別ページではない固定ページのキーワード
_NON_DETAIL_PATH_KEYWORDS = (
    "/category/",
    "/tag/",
    "/author/",
    "/page/",
    "/archive/",
    "/about",
    "/contact",
    "/privacy",
    "/policy",
    "/news",
)


class GunmaParser(BaseParser):
    prefecture = "群馬県"
    region = "関東"

    def get_list_urls(self) -> list[str]:
        return [TOP_URL]

    def get_all_list_urls(self, page1_html: str) -> list[str]:
        """トップページから一覧ページ URL を収集する。"""
        soup = BeautifulSoup(page1_html, "lxml")
        urls: list[str] = [TOP_URL]
        seen: set[str] = {TOP_URL}

        for a in soup.find_all("a", href=True):
            href = self._normalize_internal_url(a["href"])
            if not href or href in seen:
                continue

            text = a.get_text(" ", strip=True)
            parsed = urlparse(href)
            query = parse_qs(parsed.query)
            path = parsed.path.lower()

            is_list = (
                any(k in text for k in _LIST_TEXT_KEYWORDS)
                or any(k in path for k in _LIST_PATH_KEYWORDS)
                or "cat" in query
                or "paged" in query
            )

            if is_list and not _POST_URL_PATTERN.search(parsed.path):
                seen.add(href)
                urls.append(href)

        return urls

    def get_item_urls(self, html: str, page_url: str) -> list[str]:
        """一覧ページ HTML から個別銭湯ページ URL を収集する。"""
        soup = BeautifulSoup(html, "lxml")
        urls: list[str] = []
        seen: set[str] = set()

        for a in soup.find_all("a", href=True):
            raw_href = a["href"]
            href = self._normalize_internal_url(raw_href)
            if not href:
                continue

            if href in seen:
                continue

            parsed = urlparse(href)
            path = parsed.path.lower()
            query = parse_qs(parsed.query)
            text = a.get_text(" ", strip=True)

            # 日付投稿 URL は個別ページとして採用
            if _POST_URL_PATTERN.search(parsed.path):
                seen.add(href)
                urls.append(href)
                continue

            # ?p=N は投稿 ID 指定なので個別ページとして採用
            if "p" in query:
                seen.add(href)
                urls.append(href)
                continue

            # 一覧・管理系は除外
            if any(k in path for k in _NON_DETAIL_PATH_KEYWORDS):
                continue
            if any(k in raw_href for k in ("/wp-admin", "/wp-login", "/feed", "/comments")):
                continue
            if "cat" in query or "paged" in query:
                continue

            # 1階層以上の固定ページで、銭湯名らしいテキストがあるリンクを個別候補にする
            is_flat_page = path not in ("", "/") and path.count("/") >= 2
            if is_flat_page and any(h in text for h in _DETAIL_TEXT_HINTS):
                seen.add(href)
                urls.append(href)

        return urls

    def parse_sento(self, html: str, page_url: str) -> Optional[dict]:
        soup = BeautifulSoup(html, "lxml")

        parsed_url = urlparse(page_url)
        page_query = parse_qs(parsed_url.query)
        if ("page_id" in page_query or "cat" in page_query) and not self._looks_like_sento_page(soup):
            return None

        name: Optional[str] = None
        for selector in (
            "h1.entry-title",
            "h1.wp-block-post-title",
            "h2.entry-title",
            ".entry-title",
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
            or self.extract_table_value(soup, "休日")
        )

        lat: Optional[float] = None
        lng: Optional[float] = None
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "google.com/maps" not in href:
                continue
            for pattern in (
                _GMAPS_Q_PATTERN,
                _GMAPS_LL_PATTERN,
                _GMAPS_DEST_PATTERN,
                _GMAPS_DADDR_PATTERN,
                _GMAPS_AT_PATTERN,
            ):
                m = pattern.search(href)
                if not m:
                    continue
                try:
                    lat = float(m.group(1))
                    lng = float(m.group(2))
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
    def _normalize_internal_url(href: str) -> Optional[str]:
        if not href:
            return None
        if href.startswith(("mailto:", "tel:", "javascript:")):
            return None

        abs_url = href if href.startswith("http") else urljoin(BASE_URL, href)
        parsed = urlparse(abs_url)
        if "gunma1010.com" not in parsed.netloc:
            return None
        return abs_url

    @staticmethod
    def _looks_like_sento_page(soup: BeautifulSoup) -> bool:
        text = soup.get_text(separator="\n")
        indicators = ("住所", "営業時間", "定休日", "TEL", "電話")
        return sum(1 for ind in indicators if ind in text) >= 2
