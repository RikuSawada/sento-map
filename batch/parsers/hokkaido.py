"""北海道銭湯組合 (kita-no-sento.com) パーサー。

HTML 構造（調査済み）:
- 一覧: https://www.kita-no-sento.com/sentolist/
  - フィルタ方式（100+ 件が一覧ページに全件表示）
  - 個別リンク: /sento/{ID}/ または /sento/{ID-area}/
- 個別: /sento/{ID}/
  - 銭湯名: h1 または .sento-name
  - 住所・電話・営業時間・定休日: dl/dt/dd ペア
  - 緯度経度: Google Maps リンクまたは埋め込み iframe から取得
"""
import logging
import re
from typing import Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from parsers.base import BaseParser

logger = logging.getLogger(__name__)

BASE_URL = "https://www.kita-no-sento.com"
LIST_URL = f"{BASE_URL}/sentolist/"

# 個別ページ URL パターン: /sento/{ID or slug}/
_DETAIL_URL_PATTERN = re.compile(r"/sento/[\w-]+/?$")
# Google Maps リンクから緯度経度を抽出
_GMAPS_Q_PATTERN = re.compile(r"[?&]q=([-\d.]+),([-\d.]+)")
_DESTINATION_PATTERN = re.compile(r"destination=([-\d.]+),([-\d.]+)")
_GMAPS_LL_PATTERN = re.compile(r"[?&]ll=([-\d.]+),([-\d.]+)")
_GMAPS_CENTER_PATTERN = re.compile(r"center=([-\d.]+)(?:%2C|,)([-\d.]+)")
_INVALID_NAME_CANDIDATES = {"銭湯検索"}


class HokkaidoParser(BaseParser):
    prefecture = "北海道"
    region = "北海道"

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

            if _DETAIL_URL_PATTERN.search(href) and href not in seen:
                # 一覧ページ自体を除外
                if "sentolist" not in href:
                    seen.add(href)
                    urls.append(href)

        logger.info("北海道一覧: %d 件取得", len(urls))
        return urls

    def parse_sento(self, html: str, page_url: str) -> Optional[dict]:
        soup = BeautifulSoup(html, "lxml")

        # 銭湯名
        name: Optional[str] = None
        for selector in ("h2.sec_title", "h1.sento-name", ".sento-title", "h1", "h2"):
            tag = soup.select_one(selector)
            if tag:
                raw = tag.get_text(strip=True)
                if raw and len(raw) < 60 and raw not in _INVALID_NAME_CANDIDATES:
                    name = raw
                    break

        if not name:
            logger.warning("name が取得できません: %s", page_url)
            return None

        # 住所・電話・営業時間・定休日
        address = self.extract_label_value(soup, "住所") or ""
        phone = self.extract_label_value(soup, "TEL") or self.extract_label_value(soup, "電話番号")
        if not phone:
            tel_tag = soup.find("a", href=re.compile(r"^tel:"))
            if tel_tag:
                phone = tel_tag["href"].replace("tel:", "").strip()
        open_hours = self.extract_label_value(soup, "営業時間")
        holiday = self.extract_label_value(soup, "定休日") or self.extract_label_value(soup, "休日")

        # 緯度経度: Google Maps リンクまたは iframe
        lat: Optional[float] = None
        lng: Optional[float] = None

        for maps_tag in soup.find_all("a", href=True):
            href: str = maps_tag["href"]
            if "google.com/maps" not in href:
                continue
            for pat in (_GMAPS_Q_PATTERN, _DESTINATION_PATTERN, _GMAPS_LL_PATTERN):
                m = pat.search(href)
                if m:
                    try:
                        lat = float(m.group(1))
                        lng = float(m.group(2))
                    except ValueError:
                        pass
                    break
            if lat is not None:
                break

        if lat is None:
            for iframe in soup.find_all("iframe", src=True):
                src: str = iframe["src"]
                if "google.com/maps" not in src:
                    continue
                for pat in (_GMAPS_CENTER_PATTERN, _GMAPS_Q_PATTERN, _GMAPS_LL_PATTERN):
                    m = pat.search(src)
                    if m:
                        try:
                            lat = float(m.group(1))
                            lng = float(m.group(2))
                        except ValueError:
                            pass
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

