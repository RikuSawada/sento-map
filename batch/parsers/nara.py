"""奈良県銭湯組合 (nara1010.com) パーサー。"""
import logging
import re
from typing import Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from parsers.base import BaseParser

logger = logging.getLogger(__name__)

BASE_URL = "https://nara1010.com"
LIST_URL = f"{BASE_URL}/"

# Google Maps リンクから緯度経度を抽出
_GMAPS_Q_PATTERN = re.compile(r"[?&]q=([-\d.]+),([-\d.]+)")
_DESTINATION_PATTERN = re.compile(r"destination=([-\d.]+),([-\d.]+)")
_GMAPS_LL_PATTERN = re.compile(r"[?&]ll=([-\d.]+),([-\d.]+)")
_DADDR_PATTERN = re.compile(r"[?&]daddr=([-\d.]+),([-\d.]+)")
_QUERY_PATTERN = re.compile(r"[?&]query=([-\d.]+),([-\d.]+)")
_AT_PATTERN = re.compile(r"@([-\d.]+),([-\d.]+)")

# 一覧・共通ページとみなすパス断片（個別ページ URL 抽出から除外）
_EXCLUDE_PATH_KEYWORDS = (
    "/wp-admin",
    "/wp-login",
    "/privacy",
    "/contact",
    "/news",
    "/category/",
    "/tag/",
    "/author/",
    "/feed",
)

# 個別ページ URL とみなすパス断片
_DETAIL_HINTS = (
    "/sento",
    "/bath",
    "/koten",
    "/shop",
    "/store",
)


class NaraParser(BaseParser):
    prefecture = "奈良県"
    region = "近畿"

    def get_list_urls(self) -> list[str]:
        return [LIST_URL]

    def get_item_urls(self, html: str, page_url: str) -> list[str]:
        soup = BeautifulSoup(html, "lxml")
        urls: list[str] = []
        seen: set[str] = set()

        for a in soup.find_all("a", href=True):
            raw_href = str(a["href"]).strip()
            if not raw_href:
                continue

            url = urljoin(BASE_URL, raw_href)
            parsed = urlparse(url)

            if parsed.scheme not in ("http", "https"):
                continue
            if parsed.netloc not in ("nara1010.com", "www.nara1010.com"):
                continue

            normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/") + "/"
            if normalized == LIST_URL and not parsed.query:
                continue
            if any(k in parsed.path for k in _EXCLUDE_PATH_KEYWORDS):
                continue

            label = a.get_text(" ", strip=True)
            is_detail = self._looks_like_detail_url(parsed.path, parsed.query, label)
            if not is_detail:
                continue

            final_url = normalized
            if parsed.query:
                final_url = f"{final_url}?{parsed.query}"

            if final_url not in seen:
                seen.add(final_url)
                urls.append(final_url)

        return urls

    @staticmethod
    def _looks_like_detail_url(path: str, query: str, label: str) -> bool:
        lower_path = path.lower()
        lower_query = query.lower()
        lower_label = label.lower()

        if any(hint in lower_path for hint in _DETAIL_HINTS):
            return True

        if re.search(r"(?:^|&)p=\d+(?:&|$)", lower_query):
            return True

        # WordPress の投稿 URL（/2026/03/...）と固定ページ（?p=123）以外の単独スラッグを許可
        if re.search(r"/\d{4}/\d{2}/\d{2}/", lower_path):
            return True
        if re.search(r"/[^/]+/$", lower_path) and "/" != lower_path:
            if lower_path.count("/") <= 2:
                return True

        if any(token in lower_label for token in ("詳細", "店舗", "銭湯", "浴場")):
            return True

        return False

    def parse_sento(self, html: str, page_url: str) -> Optional[dict]:
        soup = BeautifulSoup(html, "lxml")

        name: Optional[str] = None
        for selector in ("h1", "h2.entry-title", "h2", "h3"):
            tag = soup.select_one(selector)
            if not tag:
                continue
            raw = tag.get_text(" ", strip=True)
            if raw and len(raw) <= 80:
                name = raw
                break

        if not name:
            title_tag = soup.find("title")
            if title_tag:
                title = title_tag.get_text(" ", strip=True)
                title = title.split("|")[0].split("｜")[0].strip()
                if title:
                    name = title

        if not name:
            logger.warning("name が取得できません: %s", page_url)
            return None

        address = (
            self.extract_label_value(soup, "住所")
            or self.extract_table_value(soup, "住所")
            or self._extract_address_from_text(soup)
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
                phone = str(tel_tag["href"]).replace("tel:", "").strip()

        open_hours = (
            self.extract_label_value(soup, "営業時間")
            or self.extract_table_value(soup, "営業時間")
            or self.extract_label_value(soup, "営業")
            or self.extract_table_value(soup, "営業")
        )
        holiday = (
            self.extract_label_value(soup, "定休日")
            or self.extract_table_value(soup, "定休日")
            or self.extract_label_value(soup, "休日")
            or self.extract_table_value(soup, "休日")
        )

        lat, lng = self._extract_coords_from_google_maps(soup)

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
    def _extract_address_from_text(soup: BeautifulSoup) -> Optional[str]:
        text = soup.get_text("\n", strip=True)
        # 例: 住所: 奈良県奈良市...
        m = re.search(r"住所[:：]\s*(.+)", text)
        if m:
            value = m.group(1).strip()
            if value:
                return value
        return None

    @staticmethod
    def _extract_coords_from_google_maps(soup: BeautifulSoup) -> tuple[Optional[float], Optional[float]]:
        for a in soup.find_all("a", href=True):
            href = str(a["href"])
            if "google." not in href or "/maps" not in href:
                continue

            for pattern in (
                _GMAPS_Q_PATTERN,
                _DESTINATION_PATTERN,
                _GMAPS_LL_PATTERN,
                _DADDR_PATTERN,
                _QUERY_PATTERN,
                _AT_PATTERN,
            ):
                m = pattern.search(href)
                if not m:
                    continue
                try:
                    return float(m.group(1)), float(m.group(2))
                except ValueError:
                    continue

        return None, None
