"""HTML パーシングモジュール。"""
import logging
import math
import re
from typing import Optional

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_ITEM_URL_PATTERN = re.compile(r"https://www\.1010\.or\.jp/map/item/item-cnt-\d+$")
_POSTAL_PATTERN = re.compile(r"〒\d{3}-\d{4}")
_DESTINATION_PATTERN = re.compile(r"destination=([-\d.]+),([-\d.]+)")
# 1010.or.jp のシェアリンクや Google マップは外部 URL として除外する
_EXCLUDE_URL_PATTERNS = [
    "1010.or.jp",
    "google.com",
    "maps.google.com",
    "maps.app.goo.gl",
    "goo.gl",           # Google 短縮 URL
    "facebook.com",
    "twitter.com",
    "instagram.com",
]
_PAGE_URL_PATTERN = re.compile(r"https://www\.1010\.or\.jp/map/item/page/(\d+)")


def parse_item_urls(html: str) -> list[str]:
    """一覧ページ（1ページ分）から個別ページ URL リストを抽出する。"""
    soup = BeautifulSoup(html, "lxml")
    urls: list[str] = []
    seen: set[str] = set()

    for a in soup.find_all("a", href=True):
        href: str = a["href"]
        # 絶対 URL に正規化
        if href.startswith("/"):
            href = "https://www.1010.or.jp" + href
        if _ITEM_URL_PATTERN.match(href) and href not in seen:
            seen.add(href)
            urls.append(href)

    return urls


_HIT_COUNT_PATTERN = re.compile(r"(\d+)件ヒット")
_ITEMS_PER_PAGE = 10


def parse_last_page(html: str) -> int:
    """一覧ページから最終ページ番号を算出する。

    「X件ヒットしました」テキストから総件数を取得し、10件/ページで割り上げる。
    取得できない場合はページネーションリンクの最大値にフォールバック。
    それも取得できない場合は 1 を返す。
    """
    soup = BeautifulSoup(html, "lxml")

    # 「X件ヒットしました」から総件数を計算
    full_text = soup.get_text(separator="\n")
    m = _HIT_COUNT_PATTERN.search(full_text)
    if m:
        total = int(m.group(1))
        return math.ceil(total / _ITEMS_PER_PAGE)

    # フォールバック: ページネーションリンクの最大ページ番号
    max_page = 1
    for a in soup.find_all("a", href=True):
        pm = _PAGE_URL_PATTERN.match(a["href"])
        if pm:
            page_num = int(pm.group(1))
            if page_num > max_page:
                max_page = page_num
    return max_page


def _extract_label_value(lines: list[str], label: str) -> Optional[str]:
    """テキスト行リストからラベルの次の行の値を返す。"""
    for i, line in enumerate(lines):
        if line == label and i + 1 < len(lines):
            value = lines[i + 1]
            # 次の行が別のラベルでないこと（ラベルは短い傾向）
            if value and len(value) < 80:
                return value
    return None


def parse_sento(html: str, page_url: str) -> Optional[dict]:
    """個別ページから銭湯データを抽出する。

    Returns:
        dict: {name, address, lat, lng, phone, url, open_hours, holiday}
        None: 必須フィールド（name, lat, lng）が取れなかった場合
    """
    soup = BeautifulSoup(html, "lxml")

    # テキスト行リストを作成（空行除去済み）
    full_text = soup.get_text(separator="\n")
    lines = [ln.strip() for ln in full_text.splitlines() if ln.strip()]

    # --- name ---
    # 個別ページでは h2 が銭湯名「水神湯 [品川区]」の形式
    name: Optional[str] = None
    h2_tags = soup.find_all("h2")
    if h2_tags:
        raw = h2_tags[0].get_text(strip=True)
        # "[区名]" 部分を除去
        name = re.sub(r"\s*\[.+?\]\s*$", "", raw).strip()
    if not name:
        # title タグからフォールバック: "銭湯名  区名：..." 形式
        title_tag = soup.find("title")
        if title_tag:
            title_text = title_tag.get_text(strip=True)
            # 東京銭湯マップ の手前まで
            name = title_text.split("東京銭湯マップ")[0].split("：")[0].strip()

    # --- 住所（郵便番号ラベルの次が〒XXX-XXXX、その次が住所）---
    address: Optional[str] = None
    for i, line in enumerate(lines):
        if _POSTAL_PATTERN.match(line):
            # 〒XXX-XXXX の次の行が住所
            if i + 1 < len(lines):
                candidate = lines[i + 1]
                if re.search(r"[都道府県区市町村]", candidate):
                    address = candidate
            break
        elif _POSTAL_PATTERN.search(line):
            # 〒XXX-XXXX が行中に埋め込まれている場合
            after = _POSTAL_PATTERN.split(line)[-1].strip()
            if after and re.search(r"[都道府県区市町村]", after):
                address = after
            elif i + 1 < len(lines):
                candidate = lines[i + 1]
                if re.search(r"[都道府県区市町村]", candidate):
                    address = candidate
            break

    # --- phone ---
    phone: Optional[str] = None
    tel_tag = soup.find("a", href=re.compile(r"^tel:"))
    if tel_tag:
        phone = tel_tag["href"].replace("tel:", "").strip()

    # --- open_hours / holiday（ラベルの次の行が値）---
    open_hours: Optional[str] = _extract_label_value(lines, "営業時間")
    holiday: Optional[str] = _extract_label_value(lines, "休日") or _extract_label_value(lines, "定休日")

    # --- lat / lng ---
    lat: Optional[float] = None
    lng: Optional[float] = None
    maps_tag = soup.find("a", href=re.compile(r"google\.com/maps"))
    if maps_tag:
        m = _DESTINATION_PATTERN.search(maps_tag["href"])
        if m:
            try:
                lat = float(m.group(1))
                lng = float(m.group(2))
            except ValueError:
                pass

    # --- 外部 URL（SNS・シェアリンク・Google 短縮 URL 等は除外）---
    external_url: Optional[str] = None
    for a in soup.find_all("a", href=True):
        href: str = a["href"]
        if not href.startswith("http"):
            continue
        domain = href.split("/")[2].lower().removeprefix("www.")
        if not any(ex in domain for ex in _EXCLUDE_URL_PATTERNS):
            external_url = href
            break

    # --- 必須フィールドチェック ---
    if not name:
        logger.warning("name が取得できません: %s", page_url)
        return None
    if lat is None or lng is None:
        logger.warning("座標が取得できません: %s (name=%s)", page_url, name)
        return None
    if not address:
        logger.warning("住所が取得できません (name=%s): 空文字で続行", name)
        address = ""

    return {
        "name": name,
        "address": address,
        "lat": lat,
        "lng": lng,
        "phone": phone,
        "url": external_url,
        "open_hours": open_hours,
        "holiday": holiday,
    }
