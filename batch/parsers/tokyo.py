"""東京都銭湯組合 (1010.or.jp) パーサー。

既存の parser.py のロジックを BaseParser インターフェースに移植。
"""
import logging
import math
import re
from typing import Optional

from bs4 import BeautifulSoup

from parsers.base import BaseParser

logger = logging.getLogger(__name__)

BASE_URL = "https://www.1010.or.jp"
LIST_URL = f"{BASE_URL}/map/item"

_ITEM_URL_PATTERN = re.compile(r"https://www\.1010\.or\.jp/map/item/item-cnt-\d+$")
_POSTAL_PATTERN = re.compile(r"〒\d{3}-\d{4}")
_DESTINATION_PATTERN = re.compile(r"destination=([-\d.]+),([-\d.]+)")
_EXCLUDE_URL_PATTERNS = [
    "1010.or.jp", "google.com", "maps.google.com",
    "maps.app.goo.gl", "goo.gl", "facebook.com", "twitter.com", "instagram.com",
]
_PAGE_URL_PATTERN = re.compile(r"https://www\.1010\.or\.jp/map/item/page/(\d+)")
_HIT_COUNT_PATTERN = re.compile(r"(\d+)件ヒット")
_ITEMS_PER_PAGE = 10


class TokyoParser(BaseParser):
    prefecture = "東京都"
    region = "関東"

    def __init__(self, last_page: int = 41):
        self._last_page = last_page

    def get_list_urls(self) -> list[str]:
        return [f"{LIST_URL}/page/{i}" for i in range(1, self._last_page + 1)]

    def update_last_page(self, html: str) -> None:
        """ページ1の HTML から最終ページ番号を更新する。"""
        soup = BeautifulSoup(html, "lxml")
        full_text = soup.get_text(separator="\n")
        m = _HIT_COUNT_PATTERN.search(full_text)
        if m:
            self._last_page = math.ceil(int(m.group(1)) / _ITEMS_PER_PAGE)
            return
        max_page = 1
        for a in soup.find_all("a", href=True):
            pm = _PAGE_URL_PATTERN.match(a["href"])
            if pm:
                page_num = int(pm.group(1))
                if page_num > max_page:
                    max_page = page_num
        self._last_page = max_page

    def get_item_urls(self, html: str, page_url: str) -> list[str]:
        soup = BeautifulSoup(html, "lxml")
        urls: list[str] = []
        seen: set[str] = set()
        for a in soup.find_all("a", href=True):
            href: str = a["href"]
            if href.startswith("/"):
                href = BASE_URL + href
            if _ITEM_URL_PATTERN.match(href) and href not in seen:
                seen.add(href)
                urls.append(href)
        return urls

    def parse_sento(self, html: str, page_url: str) -> Optional[dict]:
        soup = BeautifulSoup(html, "lxml")
        full_text = soup.get_text(separator="\n")
        lines = [ln.strip() for ln in full_text.splitlines() if ln.strip()]

        # 銭湯名
        name: Optional[str] = None
        h2_tags = soup.find_all("h2")
        if h2_tags:
            raw = h2_tags[0].get_text(strip=True)
            name = re.sub(r"\s*\[.+?\]\s*$", "", raw).strip()
        if not name:
            title_tag = soup.find("title")
            if title_tag:
                title_text = title_tag.get_text(strip=True)
                name = title_text.split("東京銭湯マップ")[0].split("：")[0].strip()

        # 住所
        address: Optional[str] = None
        for i, line in enumerate(lines):
            if _POSTAL_PATTERN.match(line):
                if i + 1 < len(lines):
                    candidate = lines[i + 1]
                    if re.search(r"[都道府県区市町村]", candidate):
                        address = candidate
                break
            elif _POSTAL_PATTERN.search(line):
                after = _POSTAL_PATTERN.split(line)[-1].strip()
                if after and re.search(r"[都道府県区市町村]", after):
                    address = after
                elif i + 1 < len(lines):
                    candidate = lines[i + 1]
                    if re.search(r"[都道府県区市町村]", candidate):
                        address = candidate
                break

        # 電話番号
        phone: Optional[str] = None
        tel_tag = soup.find("a", href=re.compile(r"^tel:"))
        if tel_tag:
            phone = tel_tag["href"].replace("tel:", "").strip()

        # 営業時間 / 定休日
        def _extract_label_value(label: str) -> Optional[str]:
            for i, line in enumerate(lines):
                if line == label and i + 1 < len(lines):
                    value = lines[i + 1]
                    if value and len(value) < 80:
                        return value
            return None

        open_hours = _extract_label_value("営業時間")
        holiday = _extract_label_value("休日") or _extract_label_value("定休日")

        # 緯度経度
        lat: Optional[float] = None
        lng: Optional[float] = None
        maps_tag = soup.find("a", href=re.compile(r"google\.com/maps"))
        if maps_tag:
            m = _DESTINATION_PATTERN.search(maps_tag["href"])
            if m:
                try:
                    lat = float(m.group(1))
                    lng = float(m.group(2))
                except ValueError:
                    pass

        # 外部 URL
        external_url: Optional[str] = None
        for a in soup.find_all("a", href=True):
            href: str = a["href"]
            if not href.startswith("http"):
                continue
            domain = href.split("/")[2].lower().removeprefix("www.")
            if not any(ex in domain for ex in _EXCLUDE_URL_PATTERNS):
                external_url = href
                break

        if not name:
            logger.warning("name が取得できません: %s", page_url)
            return None
        if not address:
            address = ""

        return self.make_sento_dict(
            name=name, address=address, lat=lat, lng=lng,
            phone=phone, url=external_url, open_hours=open_hours,
            holiday=holiday, source_url=page_url,
            facility_type="sento",
        )
