"""京都銭湯 (1010.kyoto) パーサー。

HTML 構造（調査済み）:
- 一覧: ul#spot-ul > li.spot-li > dl.spot-dl > dt.spot-thumbnail > a[href]
- ページネーション: p#page-navi a.page-numbers（数字のもの）、/spot/page/{n}/
- 件数: <span class="l orange fb">84</span>件の記事がヒットしました。
- 個別ページ:
  - 銭湯名: h2#spot-single-h2
  - 施設情報: dl.spot-info-dl の dt/dd ペア
  - 緯度経度: div#spot-single-map の次の script タグ内 var center = {lat:X, lng:Y}
"""
import logging
import math
import re
from typing import Optional

from bs4 import BeautifulSoup

from parsers.base import BaseParser

logger = logging.getLogger(__name__)

BASE_URL = "https://1010.kyoto"
LIST_URL = f"{BASE_URL}/spot/"
_LAT_LNG_PATTERN = re.compile(r"lat\s*:\s*([\d.]+)\s*,\s*lng\s*:\s*([\d.]+)")


class KyotoParser(BaseParser):
    prefecture = "京都府"
    region = "関西"

    def get_list_urls(self) -> list[str]:
        """ページ1のみ返す。update_last_page() 呼び出し後に全ページ URL を取得できる。"""
        return [LIST_URL]

    def get_all_list_urls(self, page1_html: str) -> list[str]:
        """ページ1の HTML から最終ページ番号を取得して全一覧ページ URL を返す。"""
        soup = BeautifulSoup(page1_html, "lxml")

        # 件数テキストから計算
        count_span = soup.find("span", class_=re.compile(r"orange"))
        if count_span:
            try:
                total = int(count_span.get_text(strip=True))
                last_page = math.ceil(total / 10)
            except (ValueError, TypeError):
                last_page = self._get_last_page_from_navi(soup)
        else:
            last_page = self._get_last_page_from_navi(soup)

        logger.info("京都銭湯: 全 %d ページ", last_page)
        return [f"{BASE_URL}/spot/page/{i}/" for i in range(1, last_page + 1)]

    def _get_last_page_from_navi(self, soup: BeautifulSoup) -> int:
        nums = [
            int(a.get_text(strip=True))
            for a in soup.select("p#page-navi a.page-numbers")
            if a.get_text(strip=True).isdigit()
        ]
        return max(nums) if nums else 1

    def get_item_urls(self, html: str, page_url: str) -> list[str]:
        soup = BeautifulSoup(html, "lxml")
        urls: list[str] = []
        seen: set[str] = set()
        for a in soup.select("li.spot-li dt.spot-thumbnail a[href]"):
            href: str = a["href"]
            if "/spot/" in href and href not in seen:
                seen.add(href)
                urls.append(href)
        return urls

    def parse_sento(self, html: str, page_url: str) -> Optional[dict]:
        soup = BeautifulSoup(html, "lxml")

        # 銭湯名
        name_tag = soup.select_one("h2#spot-single-h2")
        if not name_tag:
            logger.warning("name が取得できません: %s", page_url)
            return None
        name = name_tag.get_text(strip=True)

        # 施設情報（dl.spot-info-dl の dt/dd ペア）
        info: dict[str, str] = {}
        info_dl = soup.select_one("dl.spot-info-dl")
        if info_dl:
            for dt in info_dl.select("dt"):
                dd = dt.find_next_sibling("dd")
                if dd:
                    info[dt.get_text(strip=True)] = dd.get_text(strip=True)

        address = info.get("住所", "")
        phone = info.get("電話番号") or info.get("電話")
        open_hours = info.get("営業時間")
        holiday = info.get("定休日")

        # 緯度経度（div#spot-single-map の次の script タグ）
        lat: Optional[float] = None
        lng: Optional[float] = None
        map_div = soup.find("div", id="spot-single-map")
        if map_div:
            script_tag = map_div.find_next_sibling("script")
            if script_tag and script_tag.string:
                m = _LAT_LNG_PATTERN.search(script_tag.string)
                if m:
                    try:
                        lat = float(m.group(1))
                        lng = float(m.group(2))
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
