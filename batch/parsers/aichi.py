"""愛知銭湯組合 (aichi1010.jp) パーサー。

HTML 構造（調査済み）:
- 一覧: https://aichi1010.jp/page/list/l/{page}
  - ページネーション: ?per_page= または個別ページ URL パターンから最終ページを取得
  - 個別ページリンク: a[href] が /page/detail/l/{ID} に一致するもの
- 個別: https://aichi1010.jp/page/detail/l/{ID}
  - 銭湯名: h2 タグ → 「銭湯名[区名]」形式の場合 [区名] を除去
  - 住所: .address または dt/dd 「住所」ペア
  - 電話: <a href="tel:..."> または dt/dd 「TEL」ペア
  - 緯度経度: <a href="https://www.google.com/maps?q=lat,lng"> から取得
"""
import logging
import math
import re
from typing import Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from parsers.base import BaseParser

logger = logging.getLogger(__name__)

BASE_URL = "https://aichi1010.jp"
LIST_URL_TEMPLATE = f"{BASE_URL}/page/list/l/{{page}}"

# 個別ページ URL パターン: /page/detail/l/{ID}
_DETAIL_URL_PATTERN = re.compile(r"/page/detail/l/\d+")
# ページネーション: /page/list/l/{n}
_PAGE_URL_PATTERN = re.compile(r"/page/list/l/(\d+)")
# Google Maps q=lat,lng
_GMAPS_Q_PATTERN = re.compile(r"[?&]q=([-\d.]+),([-\d.]+)")
# Google Maps destination=lat,lng
_DESTINATION_PATTERN = re.compile(r"destination=([-\d.]+),([-\d.]+)")
# 銭湯名から [区名] を除去
_AREA_SUFFIX_PATTERN = re.compile(r"\s*\[.+?\]\s*$")


class AichiParser(BaseParser):
    prefecture = "愛知県"
    region = "東海"

    def __init__(self) -> None:
        self._last_page: int = 1

    def get_list_urls(self) -> list[str]:
        """ページ1の URL のみ返す。get_all_list_urls でページ数確定。"""
        return [LIST_URL_TEMPLATE.format(page=1)]

    def get_all_list_urls(self, page1_html: str) -> list[str]:
        """ページ1の HTML から最終ページ番号を取得して全一覧ページ URL を返す。"""
        soup = BeautifulSoup(page1_html, "lxml")
        last_page = self._detect_last_page(soup)
        logger.info("愛知銭湯: 全 %d ページ", last_page)
        return [LIST_URL_TEMPLATE.format(page=i) for i in range(1, last_page + 1)]

    def _detect_last_page(self, soup: BeautifulSoup) -> int:
        """ページネーションリンクから最終ページ番号を取得する。"""
        max_page = 1
        for a in soup.find_all("a", href=True):
            m = _PAGE_URL_PATTERN.search(a["href"])
            if m:
                page_num = int(m.group(1))
                if page_num > max_page:
                    max_page = page_num

        # 件数テキストから逆算（ページ内に総件数が表示される場合）
        text = soup.get_text(separator="\n")
        m_total = re.search(r"全\s*(\d+)\s*件", text)
        if m_total:
            per_page_links = [
                int(m.group(1))
                for a in soup.find_all("a", href=True)
                if (m := _PAGE_URL_PATTERN.search(a["href"]))
            ]
            if not per_page_links:
                # 1ページ目に表示される件数からページ数を推測
                items_on_page = len(soup.select("a[href*='/page/detail/l/']"))
                if items_on_page > 0:
                    total = int(m_total.group(1))
                    calculated = math.ceil(total / items_on_page)
                    if calculated > max_page:
                        max_page = calculated

        return max_page

    def get_item_urls(self, html: str, page_url: str) -> list[str]:
        soup = BeautifulSoup(html, "lxml")
        urls: list[str] = []
        seen: set[str] = set()
        for a in soup.find_all("a", href=True):
            href: str = a["href"]
            if _DETAIL_URL_PATTERN.search(href):
                if not href.startswith("http"):
                    href = urljoin(BASE_URL, href)
                if href not in seen:
                    seen.add(href)
                    urls.append(href)
        return urls

    def parse_sento(self, html: str, page_url: str) -> Optional[dict]:
        soup = BeautifulSoup(html, "lxml")

        # 銭湯名（h2 から [区名] を除去）
        name: Optional[str] = None
        for h in soup.find_all(["h1", "h2"]):
            raw = h.get_text(strip=True)
            if raw and len(raw) < 50:
                name = _AREA_SUFFIX_PATTERN.sub("", raw).strip()
                if name:
                    break
        if not name:
            logger.warning("name が取得できません: %s", page_url)
            return None

        # 住所・電話・営業時間・定休日（dt/dd ペア）
        address = _extract_label_value(soup, "住所") or ""
        phone = _extract_label_value(soup, "TEL") or _extract_label_value(soup, "電話番号")
        open_hours = _extract_label_value(soup, "営業時間")
        holiday = _extract_label_value(soup, "定休日") or _extract_label_value(soup, "休日")

        # 電話: tel: リンクも確認
        if not phone:
            tel_tag = soup.find("a", href=re.compile(r"^tel:"))
            if tel_tag:
                phone = tel_tag["href"].replace("tel:", "").strip()

        # 緯度経度: Google Maps リンクから取得
        lat: Optional[float] = None
        lng: Optional[float] = None
        for maps_tag in soup.find_all("a", href=True):
            href: str = maps_tag["href"]
            if "google.com/maps" not in href:
                continue
            m = _GMAPS_Q_PATTERN.search(href) or _DESTINATION_PATTERN.search(href)
            if m:
                try:
                    lat = float(m.group(1))
                    lng = float(m.group(2))
                except ValueError:
                    pass
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


def _extract_label_value(soup: BeautifulSoup, label: str) -> Optional[str]:
    """dt または th テキストが label に一致する dd/td の値を返す。"""
    for dt in soup.find_all(["dt", "th"]):
        if label in dt.get_text(strip=True):
            sibling = dt.find_next_sibling(["dd", "td"])
            if sibling:
                val = sibling.get_text(strip=True)
                if val:
                    return val
    return None
