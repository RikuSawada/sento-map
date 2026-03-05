"""兵庫銭湯組合 (hyogo1010.com) パーサー。

HTML 構造（調査済み）:
- 一覧: https://hyogo1010.com/sento_list/
  - .data-sento div に JSON データが data 属性として埋め込まれている（全74件一括）
  - または JSON 形式の JS 変数
  - 個別ページリンク: /sento_list/{area}-{slug}/
- 個別ページ: /sento_list/{area}-{slug}/
  - 銭湯名: h1 または h2
  - 住所・電話・営業時間・定休日: dt/dd ペア

重要注意:
  JSON 内の "lat" キー = 実際の経度 (longitude)
  JSON 内の "lng" キー = 実際の緯度 (latitude)
  → actual_lat = float(data["lng"]),  actual_lng = float(data["lat"])
"""
import json
import logging
import re
from typing import Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from parsers.base import BaseParser
from parsers.utils import extract_label_value

logger = logging.getLogger(__name__)

BASE_URL = "https://hyogo1010.com"
LIST_URL = f"{BASE_URL}/sento_list/"

# 個別ページ URL パターン: /sento_list/{area}-{slug}/
_DETAIL_URL_PATTERN = re.compile(r"/sento_list/[^/]+-[^/]+/?$")
# JSON 配列の JS 変数（例: var sentoList = [...]）
_SENTO_LIST_PATTERN = re.compile(
    r"(?:var\s+sentoList|sentoData|sento_list)\s*=\s*(\[.*?\])\s*;",
    re.DOTALL,
)
# Google Maps リンクから緯度経度を抽出
_GMAPS_Q_PATTERN = re.compile(r"[?&]q=([-\d.]+),([-\d.]+)")
_DESTINATION_PATTERN = re.compile(r"destination=([-\d.]+),([-\d.]+)")


class HyogoParser(BaseParser):
    prefecture = "兵庫県"
    region = "関西"

    def __init__(self) -> None:
        # source_url → (actual_lat, actual_lng) キャッシュ（lat/lng スワップ済み）
        self._coord_cache: dict[str, tuple[float, float]] = {}
        # source_url → JSON データキャッシュ（住所等）
        self._data_cache: dict[str, dict] = {}

    def get_list_urls(self) -> list[str]:
        return [LIST_URL]

    def get_item_urls(self, html: str, page_url: str) -> list[str]:
        """一覧ページから個別 URL を抽出し、JSON データもキャッシュする。"""
        soup = BeautifulSoup(html, "lxml")

        # data 属性から JSON を取得（例: <div class="data-sento" data-sento='{"lat":...}'>）
        urls_from_data = self._extract_from_data_attrs(soup)
        if urls_from_data:
            return urls_from_data

        # JavaScript 変数から JSON 配列を取得
        urls_from_js = self._extract_from_js(html, soup)
        if urls_from_js:
            return urls_from_js

        # フォールバック: a タグから個別ページリンクを収集
        return self._extract_item_urls_fallback(soup)

    def _extract_from_data_attrs(self, soup: BeautifulSoup) -> list[str]:
        """data-* 属性に JSON が埋め込まれた要素を処理する。"""
        urls: list[str] = []
        seen: set[str] = set()

        for el in soup.find_all(attrs={"data-sento": True}):
            try:
                data = json.loads(el["data-sento"])
            except (json.JSONDecodeError, KeyError):
                continue

            url = data.get("url") or data.get("link")
            if url:
                if not url.startswith("http"):
                    url = urljoin(BASE_URL, url)
                self._cache_from_json(url, data)
                if url not in seen:
                    seen.add(url)
                    urls.append(url)

        return urls

    def _extract_from_js(self, html: str, soup: BeautifulSoup) -> list[str]:
        """JavaScript 変数の JSON 配列を処理する。"""
        m = _SENTO_LIST_PATTERN.search(html)
        if not m:
            return []

        raw_json = m.group(1)
        raw_json = re.sub(r",\s*([}\]])", r"\1", raw_json)

        try:
            items = json.loads(raw_json)
        except json.JSONDecodeError as exc:
            logger.warning("JSON パース失敗: %s", exc)
            return []

        urls: list[str] = []
        seen: set[str] = set()

        for data in items:
            url = data.get("url") or data.get("link") or data.get("href")
            if not url:
                continue
            if not url.startswith("http"):
                url = urljoin(BASE_URL, url)
            self._cache_from_json(url, data)
            if url not in seen:
                seen.add(url)
                urls.append(url)

        logger.info("JS JSON から %d 件取得（座標キャッシュ %d 件）",
                    len(urls), len(self._coord_cache))
        return urls

    def _cache_from_json(self, url: str, data: dict) -> None:
        """JSON データから座標（lat/lng スワップ補正済み）とデータをキャッシュする。

        重要: hyogo1010.com の JSON は lat/lng が逆（スワップ）している。
        JSON["lat"] = 実際の経度 (lng)
        JSON["lng"] = 実際の緯度 (lat)
        """
        # スワップ補正: JSON の "lng" が実際の lat
        raw_lat = data.get("lng")
        raw_lng = data.get("lat")
        if raw_lat is not None and raw_lng is not None:
            try:
                actual_lat = float(raw_lat)
                actual_lng = float(raw_lng)
                self._coord_cache[url] = (actual_lat, actual_lng)
            except (TypeError, ValueError):
                pass

        self._data_cache[url] = data

    def _extract_item_urls_fallback(self, soup: BeautifulSoup) -> list[str]:
        """フォールバック: a タグから /sento_list/... リンクを収集。"""
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

        # キャッシュから座標取得（lat/lng スワップ補正済み）
        lat: Optional[float] = None
        lng: Optional[float] = None
        cached_coord = self._coord_cache.get(page_url)
        if cached_coord:
            lat, lng = cached_coord

        # キャッシュからデータ取得
        cached_data = self._data_cache.get(page_url, {})

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
            name = cached_data.get("name")

        if not name:
            logger.warning("name が取得できません: %s", page_url)
            return None

        # 住所
        address = (
            extract_label_value(soup, "住所")
            or cached_data.get("address")
            or ""
        )

        # 電話
        phone = extract_label_value(soup, "TEL") or extract_label_value(soup, "電話")
        if not phone:
            tel_tag = soup.find("a", href=re.compile(r"^tel:"))
            if tel_tag:
                phone = tel_tag["href"].replace("tel:", "").strip()
        if not phone:
            phone = cached_data.get("tel") or cached_data.get("phone")

        # 営業時間・定休日
        open_hours = extract_label_value(soup, "営業時間") or cached_data.get("open_hours")
        holiday = (
            extract_label_value(soup, "定休日")
            or extract_label_value(soup, "休日")
            or cached_data.get("holiday")
        )

        # 座標がキャッシュになければ個別ページの Google Maps リンクから取得
        if lat is None:
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
