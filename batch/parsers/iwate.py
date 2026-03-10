"""岩手県公衆浴場業生活衛生同業組合 (seiei.or.jp/iwate) パーサー。

調査メモ:
- 候補ドメイン `iwate-sento.com` / `iwate1010.jp` は有効な公開サイトを確認できず。
- 公開検索で確認できた岩手県の公衆浴場組合関連ページを一覧起点にする。

実装方針:
- 一覧ページから同一ドメイン内の詳細ページ URL を収集
- 個別ページは dt/dd・table・本文テキストから項目抽出
- 座標は Google Maps リンク/iframe から抽出。なければ None（OSM 補完対象）
"""
import logging
import re
from typing import Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from parsers.base import BaseParser

logger = logging.getLogger(__name__)

BASE_URL = "https://www.seiei.or.jp"
LIST_URL = f"{BASE_URL}/iwate/yokujou.html"

_DETAIL_HINT_PATTERN = re.compile(r"(yokujou|bath|sento|onsen)", re.IGNORECASE)
_ADDR_TEXT_PATTERN = re.compile(r"住所\s*[:：]\s*([^\n\r]+)")
_PHONE_TEXT_PATTERN = re.compile(r"(?:TEL|電話(?:番号)?)\s*[:：]\s*([0-9\-（）()\s]{8,})", re.IGNORECASE)
_OPEN_HOURS_PATTERN = re.compile(r"(?:営業時間|営業)\s*[:：]\s*([^\n\r]+)")
_HOLIDAY_PATTERN = re.compile(r"(?:定休日|休日)\s*[:：]\s*([^\n\r]+)")

_GMAPS_Q_PATTERN = re.compile(r"[?&]q=([\-\d.]+),([\-\d.]+)")
_GMAPS_LL_PATTERN = re.compile(r"[?&]ll=([\-\d.]+),([\-\d.]+)")
_GMAPS_DESTINATION_PATTERN = re.compile(r"(?:destination|daddr)=([\-\d.]+),([\-\d.]+)")
_GMAPS_AT_PATTERN = re.compile(r"@([\-\d.]+),([\-\d.]+)")
_GMAPS_EMBED_PATTERN = re.compile(r"!3d([\-\d.]+)!.*!4d([\-\d.]+)")


class IwateParser(BaseParser):
    prefecture = "岩手県"
    region = "東北"

    def get_list_urls(self) -> list[str]:
        return [LIST_URL]

    def get_item_urls(self, html: str, page_url: str) -> list[str]:
        soup = BeautifulSoup(html, "lxml")
        urls: list[str] = []
        seen: set[str] = set()

        for a in soup.find_all("a", href=True):
            raw_href: str = a["href"].strip()
            if not raw_href or raw_href.startswith(("#", "mailto:", "tel:", "javascript:")):
                continue
            if raw_href.lower().endswith((".pdf", ".jpg", ".jpeg", ".png", ".gif")):
                continue

            href = urljoin(page_url, raw_href)
            parsed = urlparse(href)
            if "seiei.or.jp" not in parsed.netloc:
                continue
            if "/iwate/" not in parsed.path:
                continue

            # 一覧起点ページ自体は除外。詳細候補のみに絞る。
            if href.rstrip("/") == LIST_URL.rstrip("/"):
                continue

            anchor_text = a.get_text(" ", strip=True)
            if not _DETAIL_HINT_PATTERN.search(href) and not any(k in anchor_text for k in ("湯", "浴場", "銭湯", "温泉")):
                continue

            if href not in seen:
                seen.add(href)
                urls.append(href)

        return urls

    def parse_sento(self, html: str, page_url: str) -> Optional[dict]:
        soup = BeautifulSoup(html, "lxml")

        name = self._extract_name(soup)
        address = self._extract_address(soup)

        if not name or not address:
            logger.warning("必須項目が取得できません: %s (name=%s, address=%s)", page_url, bool(name), bool(address))
            return None

        phone = self._extract_phone(soup)
        open_hours = self._extract_open_hours(soup)
        holiday = self._extract_holiday(soup)
        lat, lng = self._extract_lat_lng(soup)

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

    @staticmethod
    def _extract_name(soup: BeautifulSoup) -> Optional[str]:
        for selector in ("h1", "h2", "h3", ".entry-title", ".page-title", "title"):
            tag = soup.select_one(selector)
            if not tag:
                continue
            raw = tag.get_text(" ", strip=True)
            if not raw:
                continue
            cleaned = re.sub(r"\s*[|｜].*$", "", raw).strip()
            if 1 <= len(cleaned) <= 80:
                return cleaned
        return None

    def _extract_address(self, soup: BeautifulSoup) -> Optional[str]:
        address = (
            self.extract_label_value(soup, "住所")
            or self.extract_table_value(soup, "住所")
            or self._extract_from_text(soup, _ADDR_TEXT_PATTERN)
        )
        if not address:
            return None

        normalized = re.sub(r"\s+", " ", address).strip()
        normalized = re.sub(r"^(?:〒\d{3}-\d{4}\s*)", "", normalized)
        return normalized or None

    def _extract_phone(self, soup: BeautifulSoup) -> Optional[str]:
        phone = (
            self.extract_label_value(soup, "TEL")
            or self.extract_label_value(soup, "電話")
            or self.extract_table_value(soup, "TEL")
            or self.extract_table_value(soup, "電話")
            or self._extract_from_text(soup, _PHONE_TEXT_PATTERN)
        )
        if not phone:
            tel_tag = soup.find("a", href=re.compile(r"^tel:"))
            if tel_tag:
                phone = tel_tag["href"].replace("tel:", "").strip()

        if not phone:
            return None

        normalized = re.sub(r"\s+", "", phone)
        return normalized.strip("-") or None

    def _extract_open_hours(self, soup: BeautifulSoup) -> Optional[str]:
        return (
            self.extract_label_value(soup, "営業時間")
            or self.extract_table_value(soup, "営業時間")
            or self._extract_from_text(soup, _OPEN_HOURS_PATTERN)
        )

    def _extract_holiday(self, soup: BeautifulSoup) -> Optional[str]:
        return (
            self.extract_label_value(soup, "定休日")
            or self.extract_label_value(soup, "休日")
            or self.extract_table_value(soup, "定休日")
            or self.extract_table_value(soup, "休日")
            or self._extract_from_text(soup, _HOLIDAY_PATTERN)
        )

    @staticmethod
    def _extract_from_text(soup: BeautifulSoup, pattern: re.Pattern[str]) -> Optional[str]:
        text = soup.get_text("\n", strip=True)
        m = pattern.search(text)
        if m:
            value = m.group(1).strip()
            return value if value else None
        return None

    def _extract_lat_lng(self, soup: BeautifulSoup) -> tuple[Optional[float], Optional[float]]:
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "google" not in href or "map" not in href:
                continue
            coords = self._extract_coords_from_url(href)
            if coords is not None:
                return coords

        for iframe in soup.find_all("iframe", src=True):
            src = iframe["src"]
            if "google" not in src or "map" not in src:
                continue
            coords = self._extract_coords_from_url(src)
            if coords is not None:
                return coords

        return None, None

    @staticmethod
    def _extract_coords_from_url(url: str) -> Optional[tuple[float, float]]:
        for pattern in (
            _GMAPS_Q_PATTERN,
            _GMAPS_LL_PATTERN,
            _GMAPS_DESTINATION_PATTERN,
            _GMAPS_AT_PATTERN,
            _GMAPS_EMBED_PATTERN,
        ):
            m = pattern.search(url)
            if not m:
                continue
            try:
                return float(m.group(1)), float(m.group(2))
            except ValueError:
                continue
        return None
