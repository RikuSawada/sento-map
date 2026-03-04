"""千葉県銭湯組合 (chiba1126sento.com) パーサー。

HTML 構造（調査済み）:
- ベース: WordPress ベースのサイト
- エリア一覧ページ: ?page_id={N} 形式
  - 各エリアページから個別銭湯ページへのリンクを収集
- 個別ページ: 銭湯毎の投稿ページ
  - 銭湯名: h1 または h2 (post-title)
  - 住所・電話・営業時間・定休日: dl/dt/dd ペア または テキスト抽出
  - 緯度経度: Google Maps リンクまたは埋め込み map から取得

エリア一覧ページ（推測・実装時に確認が必要）:
  - ?page_id=2 等（WordPress の固定ページ）
"""
import logging
import re
from typing import Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from parsers.base import BaseParser

logger = logging.getLogger(__name__)

BASE_URL = "https://chiba1126sento.com"
# エリア一覧ページ（WordPress 固定ページ ID は実装時に確認）
# 初回アクセスでトップページからエリアリンクを収集する
TOP_URL = BASE_URL + "/"

# 個別銭湯ページ URL パターン（WordPress 投稿・固定ページ）
_SENTO_URL_PATTERN = re.compile(r"https?://chiba1126sento\.com/\?p=\d+|/\d{4}/\d{2}/\d{2}/")
# Google Maps リンクから緯度経度を抽出
_GMAPS_Q_PATTERN = re.compile(r"[?&]q=([-\d.]+),([-\d.]+)")
_DESTINATION_PATTERN = re.compile(r"destination=([-\d.]+),([-\d.]+)")
_GMAPS_LL_PATTERN = re.compile(r"[?&]ll=([-\d.]+),([-\d.]+)")
_GMAPS_EMBED_PATTERN = re.compile(r"pb=.*!3d([-\d.]+)!.*!4d([-\d.]+)")
# エリアページ判定: ?page_id= 形式
_AREA_PAGE_PATTERN = re.compile(r"\?page_id=\d+$")


class ChibaParser(BaseParser):
    prefecture = "千葉県"
    region = "関東"

    def get_list_urls(self) -> list[str]:
        """トップページから開始し、エリア一覧ページを収集する。"""
        return [TOP_URL]

    def get_item_urls(self, html: str, page_url: str) -> list[str]:
        """一覧・エリアページから個別銭湯ページ URL を収集する。

        WordPress のサイト構造:
        1. トップ → エリア固定ページ → 銭湯個別ページ
        2. トップ → 銭湯個別ページへの直接リンク
        """
        soup = BeautifulSoup(html, "lxml")
        urls: list[str] = []
        seen: set[str] = set()

        for a in soup.find_all("a", href=True):
            href: str = a["href"]
            if not href.startswith("http"):
                href = urljoin(BASE_URL, href)

            # 外部ドメインは除外
            parsed = urlparse(href)
            if "chiba1126sento.com" not in parsed.netloc:
                continue

            # 管理ページ・ログインページ等を除外
            if any(x in href for x in ("/wp-admin", "/wp-login", "?page_id=1&")):
                continue

            # 投稿ページ（数字パス、?p=N 等）
            path = parsed.path
            if re.search(r"/\d{4}/\d{2}/\d{2}/|/\?p=\d+", href):
                if href not in seen:
                    seen.add(href)
                    urls.append(href)
                continue

            # ?page_id=N 形式のエリアページ（再帰的に処理するためリストに含める）
            # ただし、すでに処理中のページは除外
            if _AREA_PAGE_PATTERN.search(href) and href != page_url:
                if href not in seen:
                    seen.add(href)
                    urls.append(href)

        return urls

    def parse_sento(self, html: str, page_url: str) -> Optional[dict]:
        soup = BeautifulSoup(html, "lxml")

        # エリア一覧ページ（固定ページ）の場合は銭湯データなし
        if _AREA_PAGE_PATTERN.search(page_url) and not self._looks_like_sento_page(soup):
            return None

        # 銭湯名
        name: Optional[str] = None
        for selector in ("h1.entry-title", "h2.entry-title", ".entry-title", "h1", "h2"):
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
        address = _extract_label_value(soup, "住所") or ""
        phone = _extract_label_value(soup, "TEL") or _extract_label_value(soup, "電話")
        if not phone:
            tel_tag = soup.find("a", href=re.compile(r"^tel:"))
            if tel_tag:
                phone = tel_tag["href"].replace("tel:", "").strip()
        open_hours = _extract_label_value(soup, "営業時間")
        holiday = _extract_label_value(soup, "定休日") or _extract_label_value(soup, "休日")

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

        if lat is None:
            for iframe in soup.find_all("iframe", src=True):
                src: str = iframe["src"]
                if "google.com/maps" not in src:
                    continue
                for pat in (_GMAPS_EMBED_PATTERN, _GMAPS_Q_PATTERN, _GMAPS_LL_PATTERN):
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

    def _looks_like_sento_page(self, soup: BeautifulSoup) -> bool:
        """個別銭湯ページかどうかを判定する（エリア一覧ページと区別）。"""
        text = soup.get_text(separator="\n")
        indicators = ["営業時間", "定休日", "TEL", "電話", "住所"]
        return sum(1 for ind in indicators if ind in text) >= 2


def _extract_label_value(soup: BeautifulSoup, label: str) -> Optional[str]:
    """dt または th テキストが label に一致する dd/td の値を返す。"""
    for dt in soup.find_all(["dt", "th"]):
        if label in dt.get_text(strip=True):
            sibling = dt.find_next_sibling(["dd", "td"])
            if sibling:
                val = sibling.get_text(strip=True)
                if val:
                    return val
    # strong タグに label がある場合も確認
    for strong in soup.find_all(["strong", "b"]):
        if label in strong.get_text(strip=True):
            parent = strong.parent
            if parent:
                text = parent.get_text(strip=True).replace(label, "").strip()
                if text and len(text) < 100:
                    return text
    return None
