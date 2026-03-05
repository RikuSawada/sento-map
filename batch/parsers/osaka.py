"""大阪銭湯組合 (osaka268.com) パーサー。

HTML 構造（調査済み）:
- 一覧: /search/ の JavaScript `childaMarkers` 配列に全件の lat/lng + sento URL が含まれる
  形式: childaMarkers = [{id:..., lat:..., lng:..., url:"...", ...}, ...]
  ページネーション: なし（全件一括）
- 個別ページ: /sento/{encoded-name}/ （日本語URLエンコード）
  - 銭湯名: h1.sento-name または h1 直下テキスト
  - 住所: .sento-address または address タグ
  - 電話: <a href="tel:...">
  - 営業時間 / 定休日: .sento-info の dl/dt/dd ペア
"""
import json
import logging
import re
from typing import Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from parsers.base import BaseParser

logger = logging.getLogger(__name__)

BASE_URL = "https://osaka268.com"
SEARCH_URL = f"{BASE_URL}/search/"

# JavaScript の childaMarkers 配列を抽出するパターン
_CHILD_MARKERS_PATTERN = re.compile(
    r"childaMarkers\s*=\s*(\[.*?\])\s*;",
    re.DOTALL,
)

# Google Maps destination パラメータから緯度経度を抽出
_DESTINATION_PATTERN = re.compile(r"destination=([-\d.]+),([-\d.]+)")
# Google Maps q= パラメータから緯度経度を抽出
_MAPS_Q_PATTERN = re.compile(r"[?&]q=([-\d.]+),([-\d.]+)")


class OsakaParser(BaseParser):
    prefecture = "大阪府"
    region = "関西"

    def __init__(self) -> None:
        # URL → (lat, lng) キャッシュ（一覧ページの JS 配列から取得）
        self._coord_cache: dict[str, tuple[float, float]] = {}

    def get_list_urls(self) -> list[str]:
        """一覧ページは 1 件（全件一括）。"""
        return [SEARCH_URL]

    def get_item_urls(self, html: str, page_url: str) -> list[str]:
        """JS の childaMarkers 配列から個別ページ URL リストを抽出し、
        lat/lng をキャッシュする。
        """
        m = _CHILD_MARKERS_PATTERN.search(html)
        if not m:
            logger.warning("childaMarkers が見つかりません: %s", page_url)
            # フォールバック: a.sento-list-link のような通常リンクから取得
            return self._extract_item_urls_fallback(html)

        raw_json = m.group(1)
        # JS の trailing comma 対策（JSON は trailing comma 不可）
        raw_json = re.sub(r",\s*([}\]])", r"\1", raw_json)

        try:
            markers = json.loads(raw_json)
        except json.JSONDecodeError as exc:
            logger.warning("childaMarkers JSON パース失敗: %s (%s)", page_url, exc)
            return self._extract_item_urls_fallback(html)

        urls: list[str] = []
        seen: set[str] = set()

        for marker in markers:
            url = marker.get("url") or marker.get("link") or marker.get("href")
            if not url:
                continue

            # 相対 URL を絶対 URL に変換
            if url.startswith("/"):
                url = BASE_URL + url
            elif not url.startswith("http"):
                url = urljoin(BASE_URL, url)

            try:
                lat = float(marker.get("lat", 0) or 0)
                lng = float(marker.get("lng", 0) or 0)
            except (TypeError, ValueError):
                lat, lng = 0.0, 0.0

            if lat and lng:
                self._coord_cache[url] = (lat, lng)

            if url not in seen:
                seen.add(url)
                urls.append(url)

        logger.info("childaMarkers から %d 件取得（座標キャッシュ %d 件）",
                    len(urls), len(self._coord_cache))
        return urls

    def _extract_item_urls_fallback(self, html: str) -> list[str]:
        """childaMarkers が取得できなかった場合の a タグからの URL 抽出。"""
        soup = BeautifulSoup(html, "lxml")
        urls: list[str] = []
        seen: set[str] = set()
        for a in soup.find_all("a", href=True):
            href: str = a["href"]
            if href.startswith("/"):
                href = BASE_URL + href
            if "/sento/" in href and href not in seen:
                seen.add(href)
                urls.append(href)
        return urls

    def parse_sento(self, html: str, page_url: str) -> Optional[dict]:
        soup = BeautifulSoup(html, "lxml")

        # 銭湯名
        name: Optional[str] = None
        for selector in ("h1.sento-name", "h1.entry-title", "h1", ".name"):
            tag = soup.select_one(selector)
            if tag:
                name = tag.get_text(strip=True)
                break
        if not name:
            title_tag = soup.find("title")
            if title_tag:
                name = title_tag.get_text(strip=True).split("|")[0].split("【")[0].strip()

        if not name:
            logger.warning("name が取得できません: %s", page_url)
            return None

        # 住所
        address: Optional[str] = None
        for selector in (".sento-address", "address", ".address", ".post-address"):
            tag = soup.select_one(selector)
            if tag:
                address = tag.get_text(strip=True)
                break
        if not address:
            # dt/dd ペアから「住所」を探す
            address = self.extract_label_value(soup, "住所")

        # 電話番号
        phone: Optional[str] = None
        tel_tag = soup.find("a", href=re.compile(r"^tel:"))
        if tel_tag:
            phone = tel_tag["href"].replace("tel:", "").strip()
        if not phone:
            phone = self.extract_label_value(soup, "電話番号") or self.extract_label_value(soup, "TEL")

        # 営業時間 / 定休日
        open_hours = self.extract_label_value(soup, "営業時間") or self.extract_label_value(soup, "営業時間帯")
        holiday = self.extract_label_value(soup, "定休日") or self.extract_label_value(soup, "休日")

        # 緯度経度: キャッシュ → 個別ページの Google Maps リンク
        lat: Optional[float] = None
        lng: Optional[float] = None

        cached = self._coord_cache.get(page_url)
        if cached:
            lat, lng = cached
        else:
            # Google Maps ナビリンクから取得
            for maps_tag in soup.find_all("a", href=re.compile(r"google\.com/maps")):
                href: str = maps_tag["href"]
                m = _DESTINATION_PATTERN.search(href) or _MAPS_Q_PATTERN.search(href)
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
                address=address or "",
                lat=lat,
                lng=lng,
                phone=phone,
                open_hours=open_hours,
                holiday=holiday,
                source_url=page_url,
            ),
            "facility_type": "sento",
        }


