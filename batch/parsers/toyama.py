"""富山県公衆浴場組合 (toyama1010.com) パーサー。

HTML 構造（調査済み）:
- 一覧: https://toyama1010.com/sentou-list.html
  - 1ページに全店舗が掲載される table#sp-table-3
  - 個別リンク: 各行の浴場名セル(th.col-title)内の a[href]
- 個別: https://toyama1010.com/{slug}.html
  - 銭湯名: h1.entry-title
  - 詳細情報: 本文の「【住所】」「【電話番号】」「【営業時間】」「【定休日】」
  - 緯度経度: Google Maps リンク/iframe src から抽出（無ければ None）
"""
import logging
import re
from typing import Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from parsers.base import BaseParser

logger = logging.getLogger(__name__)

BASE_URL = "https://toyama1010.com"
LIST_URL = f"{BASE_URL}/sentou-list.html"

# 銭湯詳細ページ URL（一覧表の .html ページ）
_DETAIL_PATH_PATTERN = re.compile(r"/[a-z0-9-]+\.html$", re.IGNORECASE)
# サイトの共通ページ（銭湯詳細ではない）
_EXCLUDED_PAGES = {
    "index.html",
    "about-union.html",
    "sentou-list.html",
    "ryoukin.html",
    "entrance.html",
    "salon.html",
    "event.html",
    "mailform.html",
    "privacy.html",
}

# 本文内の「【ラベル】値」を抽出
_BRACKET_FIELD_PATTERN = re.compile(r"【\s*(?P<label>[^】]+?)\s*】\s*(?P<value>.*?)(?=\s*【|\Z)", re.DOTALL)

# Google Maps URL から緯度経度を抽出
_GMAPS_Q_PATTERN = re.compile(r"[?&]q=([-\d.]+),([-\d.]+)")
_GMAPS_LL_PATTERN = re.compile(r"[?&]ll=([-\d.]+),([-\d.]+)")
_GMAPS_AT_PATTERN = re.compile(r"@([-\d.]+),([-\d.]+)")
_GMAPS_EMBED_LAT_FIRST_PATTERN = re.compile(r"!3d([-\d.]+)!.*?(?:2d|4d)([-\d.]+)")
_GMAPS_EMBED_LNG_FIRST_PATTERN = re.compile(r"!(?:2d|4d)([-\d.]+)!.*?3d([-\d.]+)")
_DESTINATION_PATTERN = re.compile(r"destination=([-\d.]+),([-\d.]+)")


class ToyamaParser(BaseParser):
    prefecture = "富山県"
    region = "中部"

    def get_list_urls(self) -> list[str]:
        return [LIST_URL]

    def get_item_urls(self, html: str, page_url: str) -> list[str]:
        soup = BeautifulSoup(html, "lxml")
        urls: list[str] = []
        seen: set[str] = set()

        # 一覧表の浴場名セル配下のリンクのみを対象にする
        for a in soup.select("table#sp-table-3 th.col-title a[href], table#sp-table-3 th a[href]"):
            href: str = a["href"]
            if not href.startswith("http"):
                href = urljoin(BASE_URL, href)

            parsed = urlparse(href)
            if "toyama1010.com" not in parsed.netloc:
                continue

            path = parsed.path.rsplit("/", 1)[-1]
            if path in _EXCLUDED_PAGES:
                continue
            if not _DETAIL_PATH_PATTERN.search(parsed.path):
                continue

            if href not in seen:
                seen.add(href)
                urls.append(href)

        logger.info("富山一覧: %d 件取得", len(urls))
        return urls

    def parse_sento(self, html: str, page_url: str) -> Optional[dict]:
        soup = BeautifulSoup(html, "lxml")

        name: Optional[str] = None
        for selector in ("h1.entry-title", "h1", "h2.entry-title", "h2"):
            tag = soup.select_one(selector)
            if tag:
                raw = tag.get_text(" ", strip=True)
                if raw and len(raw) < 80 and raw not in {"銭湯一覧"}:
                    name = raw
                    break

        if not name:
            logger.warning("name が取得できません: %s", page_url)
            return None

        content = soup.select_one("#page-content") or soup
        fields = self._extract_bracket_fields(content.get_text("\n", strip=True))

        address = fields.get("住所") or self.extract_label_value(soup, "住所") or ""
        phone = (
            fields.get("電話番号")
            or fields.get("電話")
            or fields.get("TEL")
            or self.extract_label_value(soup, "電話番号")
            or self.extract_label_value(soup, "電話")
            or self.extract_label_value(soup, "TEL")
        )
        open_hours = fields.get("営業時間") or self.extract_label_value(soup, "営業時間")
        holiday = (
            fields.get("定休日")
            or fields.get("休日")
            or self.extract_label_value(soup, "定休日")
            or self.extract_label_value(soup, "休日")
        )
        url = fields.get("URL")

        lat, lng = self._extract_lat_lng(content)

        return {
            **self.make_sento_dict(
                name=name,
                address=address,
                lat=lat,
                lng=lng,
                phone=phone,
                url=url,
                open_hours=open_hours,
                holiday=holiday,
                source_url=page_url,
            ),
            "facility_type": "sento",
        }

    @staticmethod
    def _extract_bracket_fields(text: str) -> dict[str, str]:
        fields: dict[str, str] = {}
        normalized = re.sub(r"\u3000", " ", text)

        for m in _BRACKET_FIELD_PATTERN.finditer(normalized):
            label = m.group("label").strip()
            value = re.sub(r"\s+", " ", m.group("value")).strip()
            if label and value:
                fields[label] = value
        return fields

    @staticmethod
    def _extract_lat_lng(scope: BeautifulSoup) -> tuple[Optional[float], Optional[float]]:
        for tag in scope.find_all("a", href=True):
            lat_lng = ToyamaParser._extract_lat_lng_from_url(tag["href"])
            if lat_lng != (None, None):
                return lat_lng

        for iframe in scope.find_all("iframe", src=True):
            lat_lng = ToyamaParser._extract_lat_lng_from_url(iframe["src"])
            if lat_lng != (None, None):
                return lat_lng

        return None, None

    @staticmethod
    def _extract_lat_lng_from_url(url: str) -> tuple[Optional[float], Optional[float]]:
        if "google" not in url and "goo.gl/maps" not in url:
            return None, None

        for pat in (
            _GMAPS_Q_PATTERN,
            _DESTINATION_PATTERN,
            _GMAPS_LL_PATTERN,
            _GMAPS_AT_PATTERN,
            _GMAPS_EMBED_LAT_FIRST_PATTERN,
        ):
            m = pat.search(url)
            if not m:
                continue
            try:
                return float(m.group(1)), float(m.group(2))
            except ValueError:
                return None, None

        m = _GMAPS_EMBED_LNG_FIRST_PATTERN.search(url)
        if m:
            try:
                return float(m.group(2)), float(m.group(1))
            except ValueError:
                return None, None

        return None, None
