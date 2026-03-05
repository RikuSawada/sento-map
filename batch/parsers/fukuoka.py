"""福岡県銭湯 (fukuoka1010.com) パーサー。

HTML 構造（調査済み）:
- 一覧: 地域別ページに全件が1ページで収まる（ページネーションなし）
  - /list-fukuoka/ → 福岡市内、URLパターン /fukuoka/{slug}/
  - /list-kitakyu/ → 北九州、URLパターン /kitakyu/{slug}/
  - /list-chikugo/ → 筑後・筑豊
- 一覧構造: div.list ul.box li a[href] > h3（銭湯名「〇〇【区名】」）, h4（住所）
- 個別ページ:
  - 銭湯名: div.bath h3:not(.headline)
  - 施設情報: div.bath table の th/td ペア
  - 緯度経度: div.bath iframe[src] の !2d{lng}!3d{lat} パターン
"""
import logging
import re
from typing import Optional

from bs4 import BeautifulSoup

from parsers.base import BaseParser

logger = logging.getLogger(__name__)

BASE_URL = "https://fukuoka1010.com"
LIST_PAGES = [
    f"{BASE_URL}/list-fukuoka/",
    f"{BASE_URL}/list-kitakyu/",
    f"{BASE_URL}/list-chikugo/",
]
_IFRAME_LAT_PATTERN = re.compile(r"!3d([-\d.]+)")
_IFRAME_LNG_PATTERN = re.compile(r"!2d([-\d.]+)")


class FukuokaParser(BaseParser):
    prefecture = "福岡県"
    region = "九州"

    def get_list_urls(self) -> list[str]:
        return LIST_PAGES

    def get_item_urls(self, html: str, page_url: str) -> list[str]:
        soup = BeautifulSoup(html, "lxml")
        urls: list[str] = []
        seen: set[str] = set()
        for a in soup.select("div.list ul.box li a[href]"):
            href: str = a["href"]
            if href.startswith("/"):
                href = BASE_URL + href
            if BASE_URL in href and href not in seen:
                seen.add(href)
                urls.append(href)
        return urls

    def parse_sento(self, html: str, page_url: str) -> Optional[dict]:
        soup = BeautifulSoup(html, "lxml")

        bath_div = soup.select_one("div.bath")
        if not bath_div:
            logger.warning("div.bath が見つかりません: %s", page_url)
            return None

        # 銭湯名（.headline クラスを除く h3）
        name_tag = bath_div.select_one("h3:not(.headline)")
        if not name_tag:
            logger.warning("name が取得できません: %s", page_url)
            return None
        name = name_tag.get_text(strip=True)

        # 施設情報（table の th/td ペア）
        info: dict[str, str] = {}
        for row in bath_div.select("table tr"):
            th = row.select_one("th")
            td = row.select_one("td")
            if th and td:
                info[th.get_text(strip=True)] = td.get_text(strip=True)

        address = info.get("住所", "")
        phone = info.get("電話番号") or info.get("電話")
        open_hours = info.get("営業時間")
        holiday = info.get("定休日")

        # 緯度経度（Google Maps embed iframe のパラメータから）
        lat: Optional[float] = None
        lng: Optional[float] = None
        iframe = bath_div.select_one("iframe[src]")
        if iframe:
            src = str(iframe.get("src", ""))
            m_lat = _IFRAME_LAT_PATTERN.search(src)
            m_lng = _IFRAME_LNG_PATTERN.search(src)
            if m_lat and m_lng:
                try:
                    lat = float(m_lat.group(1))
                    lng = float(m_lng.group(1))
                except ValueError:
                    pass

        if not address:
            logger.warning("住所が取得できません: %s (name=%s)", page_url, name)

        return self.make_sento_dict(
            name=name, address=address, lat=lat, lng=lng,
            phone=phone, open_hours=open_hours, holiday=holiday,
            source_url=page_url,
            facility_type="sento",
        )
