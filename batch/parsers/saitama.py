"""埼玉銭湯組合 (saiyoku.jp) パーサー。

HTML 構造（調査済み）:
- 個別 URL: /id-1/{ID}/
- robots.txt: 要確認（403 が発生する場合は OSM インポートにフォールバック）
- 銭湯名: h1 または h2
- 住所・電話・営業時間・定休日: dl/dt/dd ペア
- 緯度経度: Google Maps リンクから取得

注意:
  ホームページが 403 を返す場合があります。
  403 が解消しない場合は osm_geocoder.py --import-new --prefecture 埼玉県 を使用してください。
"""
import logging
import re
from typing import Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from parsers.base import BaseParser

logger = logging.getLogger(__name__)

BASE_URL = "https://saiyoku.jp"
# トップレベル一覧ページ（ID を収集するため）
LIST_URL = f"{BASE_URL}/"

# 個別ページ URL パターン: /id-1/{ID}/
_DETAIL_URL_PATTERN = re.compile(r"/id-1/\d+/?$")
# Google Maps リンクから緯度経度を抽出
_GMAPS_Q_PATTERN = re.compile(r"[?&]q=([-\d.]+),([-\d.]+)")
_DESTINATION_PATTERN = re.compile(r"destination=([-\d.]+),([-\d.]+)")
_GMAPS_LL_PATTERN = re.compile(r"[?&]ll=([-\d.]+),([-\d.]+)")


class SaitamaParser(BaseParser):
    prefecture = "埼玉県"
    region = "関東"

    def get_list_urls(self) -> list[str]:
        return [LIST_URL]

    def get_all_list_urls(self, page1_html: str) -> list[str]:
        """ページ1の HTML からページネーション URL を収集する。"""
        soup = BeautifulSoup(page1_html, "lxml")
        urls = [LIST_URL]
        seen = {LIST_URL}

        # ページネーションリンクを収集
        for a in soup.find_all("a", href=True):
            href: str = a["href"]
            if not href.startswith("http"):
                href = urljoin(BASE_URL, href)
            # /page/N/ または ?page=N 形式のページネーション
            if re.search(r"/page/\d+/?$|[?&]page=\d+$", href):
                if "saiyoku.jp" in href and href not in seen:
                    seen.add(href)
                    urls.append(href)

        return urls

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
        for selector in ("h1.sento-name", ".sento-title", "h1", "h2"):
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
        address = self.extract_label_value(soup, "住所") or ""
        phone = self.extract_label_value(soup, "TEL") or self.extract_label_value(soup, "電話番号")
        if not phone:
            tel_tag = soup.find("a", href=re.compile(r"^tel:"))
            if tel_tag:
                phone = tel_tag["href"].replace("tel:", "").strip()
        open_hours = self.extract_label_value(soup, "営業時間")
        holiday = self.extract_label_value(soup, "定休日") or self.extract_label_value(soup, "休日")

        # 緯度経度
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


