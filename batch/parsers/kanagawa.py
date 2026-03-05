"""神奈川銭湯組合 (k-o-i.jp) パーサー。

HTML 構造（調査済み）:
- 一覧: エリア別ページ（既知の3エリアをハードコードで対応。追加エリアが確認された場合はリストを更新する）
  - /search_area/yokohama/  （横浜市）
  - /search_area/kawasaki/  （川崎市）
  - /search_area/shonan/    （湘南・その他）
- 個別: /koten/{slug}/
  - 銭湯名: h1 または h2 タグ
  - 住所: dt/dd 「住所」ペア、または .address
  - 電話: tel: リンク または dt/dd 「TEL」ペア
  - 緯度経度: Google Maps リンクから取得
"""
import logging
import re
from typing import Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from parsers.base import BaseParser
from parsers.utils import extract_label_value

logger = logging.getLogger(__name__)

BASE_URL = "https://k-o-i.jp"
# 既知のエリア一覧ページ
AREA_LIST_URLS = [
    f"{BASE_URL}/search_area/yokohama/",
    f"{BASE_URL}/search_area/kawasaki/",
    f"{BASE_URL}/search_area/shonan/",
]

# 個別ページ URL パターン
_DETAIL_URL_PATTERN = re.compile(r"/koten/[^/]+/?$")
# Google Maps リンクから緯度経度を抽出
_GMAPS_Q_PATTERN = re.compile(r"[?&]q=([-\d.]+),([-\d.]+)")
_DESTINATION_PATTERN = re.compile(r"destination=([-\d.]+),([-\d.]+)")
_GMAPS_LL_PATTERN = re.compile(r"[?&]ll=([-\d.]+),([-\d.]+)")
_GMAPS_DADDR_PATTERN = re.compile(r"daddr=([-\d.]+),([-\d.]+)")


class KanagawaParser(BaseParser):
    prefecture = "神奈川県"
    region = "関東"

    def get_list_urls(self) -> list[str]:
        return AREA_LIST_URLS

    def get_item_urls(self, html: str, page_url: str) -> list[str]:
        soup = BeautifulSoup(html, "lxml")
        urls: list[str] = []
        seen: set[str] = set()

        for a in soup.find_all("a", href=True):
            href: str = a["href"]
            if not href.startswith("http"):
                href = urljoin(BASE_URL, href)

            if _DETAIL_URL_PATTERN.search(href) and href not in seen:
                seen.add(href)
                urls.append(href)

        return urls

    def parse_sento(self, html: str, page_url: str) -> Optional[dict]:
        soup = BeautifulSoup(html, "lxml")

        # 銭湯名
        name: Optional[str] = None
        for selector in ("h1.koten-name", "h1.entry-title", ".koten-title", "h1", "h2"):
            tag = soup.select_one(selector)
            if tag:
                raw = tag.get_text(strip=True)
                if raw and len(raw) < 60:
                    name = raw
                    break

        if not name:
            logger.warning("name が取得できません: %s", page_url)
            return None

        # 住所・電話・営業時間・定休日
        address = extract_label_value(soup, "住所") or ""
        phone = extract_label_value(soup, "TEL") or extract_label_value(soup, "電話")
        if not phone:
            tel_tag = soup.find("a", href=re.compile(r"^tel:"))
            if tel_tag:
                phone = tel_tag["href"].replace("tel:", "").strip()
        open_hours = extract_label_value(soup, "営業時間")
        holiday = extract_label_value(soup, "定休日") or extract_label_value(soup, "休日")

        # 緯度経度: Google Maps リンク（短縮 URL は座標を含まないため google.com/maps のみ対象）
        lat: Optional[float] = None
        lng: Optional[float] = None
        for maps_tag in soup.find_all("a", href=True):
            href: str = maps_tag["href"]
            if "google.com/maps" not in href:
                continue
            for pattern in (_GMAPS_Q_PATTERN, _DESTINATION_PATTERN, _GMAPS_LL_PATTERN, _GMAPS_DADDR_PATTERN):
                m = pattern.search(href)
                if m:
                    try:
                        lat = float(m.group(1))
                        lng = float(m.group(2))
                    except ValueError:
                        pass
                    break
            if lat is not None:
                break

        # Google Maps iframe からも試みる
        if lat is None:
            for iframe in soup.find_all("iframe", src=True):
                src: str = iframe["src"]
                if "google.com/maps" in src:
                    for pattern in (_GMAPS_Q_PATTERN, _GMAPS_LL_PATTERN):
                        m = pattern.search(src)
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
