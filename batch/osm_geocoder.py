"""
OSM Overpass API による座標補完・新規インポートスクリプト

【座標補完モード（デフォルト）】
lat/lng が NULL の銭湯に対して、OSM の amenity=public_bath データを
名前・住所のファジーマッチングで照合し、座標を補完する。

【新規インポートモード（--import-new）】
Overpass API から amenity=public_bath / amenity=spa を取得し、
source_url = "osm:{element_id}" で重複チェックしながら新規 INSERT する。
公式パーサーが未実装な都道府県向け。

usage:
  # 座標補完
  uv run python osm_geocoder.py --prefecture 大阪府 --dry-run
  uv run python osm_geocoder.py --prefecture 大阪府
  uv run python osm_geocoder.py --all

  # 新規インポート
  uv run python osm_geocoder.py --import-new --prefecture 大分県 --dry-run
  uv run python osm_geocoder.py --import-new --prefecture 大分県
  uv run python osm_geocoder.py --import-new --all

ライセンス: OSM データは ODbL ライセンス。
  フロントに © OpenStreetMap contributors の帰属表示が必要。
"""
import argparse
import logging
import sys
import time
from difflib import SequenceMatcher
from typing import Optional

import requests
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.orm import Session

from db import get_engine
from parsers import PARSERS

logger = logging.getLogger(__name__)

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
USER_AGENT = "sento-map-bot/1.0 (https://github.com/RikuSawada/sento-map; ODbL)"

# 都道府県の admin_level=4 マッピング（OSM area クエリ用）
PREFECTURE_NAMES = [
    "北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県",
    "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県",
    "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県",
    "岐阜県", "静岡県", "愛知県", "三重県",
    "滋賀県", "京都府", "大阪府", "兵庫県", "奈良県", "和歌山県",
    "鳥取県", "島根県", "岡山県", "広島県", "山口県",
    "徳島県", "香川県", "愛媛県", "高知県",
    "福岡県", "佐賀県", "長崎県", "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県",
]

# 公式パーサーが実装済みの都道府県（--import-new --all 時に除外）
# parsers/__init__.py の PARSERS dict から自動参照することで手動更新不要
PARSER_IMPLEMENTED_PREFECTURES: set[str] = set(PARSERS.keys())

# 都道府県 → 地域区分マッピング（INSERT 時の region カラムに使用）
PREFECTURE_TO_REGION: dict[str, str] = {
    "北海道": "北海道",
    "青森県": "東北", "岩手県": "東北", "宮城県": "東北",
    "秋田県": "東北", "山形県": "東北", "福島県": "東北",
    "茨城県": "関東", "栃木県": "関東", "群馬県": "関東",
    "埼玉県": "関東", "千葉県": "関東", "東京都": "関東", "神奈川県": "関東",
    "新潟県": "中部", "富山県": "中部", "石川県": "中部", "福井県": "中部",
    "山梨県": "中部", "長野県": "中部", "岐阜県": "中部",
    "静岡県": "中部", "愛知県": "中部",
    "三重県": "近畿", "滋賀県": "近畿", "京都府": "近畿",
    "大阪府": "近畿", "兵庫県": "近畿", "奈良県": "近畿", "和歌山県": "近畿",
    "鳥取県": "中国", "島根県": "中国", "岡山県": "中国",
    "広島県": "中国", "山口県": "中国",
    "徳島県": "四国", "香川県": "四国", "愛媛県": "四国", "高知県": "四国",
    "福岡県": "九州", "佐賀県": "九州", "長崎県": "九州",
    "熊本県": "九州", "大分県": "九州", "宮崎県": "九州",
    "鹿児島県": "九州", "沖縄県": "九州",
}


def fetch_osm_public_baths(prefecture: str) -> list[dict]:
    """Overpass API で指定都道府県の public_bath を一括取得する（座標補完用）。"""
    query = f"""
[out:json][timeout:60];
area["name"="{prefecture}"]["admin_level"="4"]->.pref;
nwr(area.pref)[amenity=public_bath];
out body center;
"""
    return _fetch_overpass(query, prefecture)


def fetch_osm_bath_facilities(prefecture: str) -> list[dict]:
    """Overpass API で指定都道府県の public_bath + spa を一括取得する（新規インポート用）。"""
    query = f"""
[out:json][timeout:90];
area["name"="{prefecture}"]["admin_level"="4"]->.pref;
(
  nwr(area.pref)[amenity=public_bath];
  nwr(area.pref)[amenity=spa];
);
out body center;
"""
    return _fetch_overpass(query, prefecture)


def _fetch_overpass(query: str, prefecture: str) -> list[dict]:
    """Overpass API クエリを実行して要素リストを返す。"""
    try:
        logger.info("Overpass API クエリ実行中: %s", prefecture)
        resp = requests.post(
            OVERPASS_URL,
            data={"data": query},
            headers={"User-Agent": USER_AGENT},
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        elements = data.get("elements", [])
        logger.info("OSM データ取得完了: %d 件", len(elements))
        return elements
    except requests.RequestException as exc:
        logger.error("Overpass API エラー: %s", exc)
        return []


def extract_coords(element: dict) -> tuple[Optional[float], Optional[float]]:
    """OSM element から緯度経度を取得する。node/way/relation に対応。"""
    if element["type"] == "node":
        return element.get("lat"), element.get("lon")
    # way/relation は center を使用
    center = element.get("center", {})
    return center.get("lat"), center.get("lon")


def resolve_facility_type(tags: dict) -> str:
    """OSM タグから facility_type を決定する。

    Rules:
    - amenity=spa → 'super_sento'
    - amenity=public_bath + bath:type=onsen → 'onsen'
    - amenity=public_bath（それ以外）→ 'sento'
    """
    amenity = tags.get("amenity", "")
    if amenity == "spa":
        return "super_sento"
    bath_type = tags.get("bath:type", "")
    if bath_type == "onsen":
        return "onsen"
    return "sento"


def name_similarity(a: str, b: str) -> float:
    """2つの銭湯名の類似度（0.0〜1.0）を返す。"""
    return SequenceMatcher(None, a, b).ratio()


def find_best_match(
    db_name: str,
    db_address: str,
    osm_elements: list[dict],
    threshold: float = 0.6,
) -> Optional[dict]:
    """OSM elements から最も一致する要素を探す。

    マッチング基準:
    - 名前完全一致: 信頼度 高
    - 名前部分一致 (≥threshold) + 住所の市区町村一致: 信頼度 中
    - それ以外: スキップ
    """
    best_score = 0.0
    best_element = None

    for el in osm_elements:
        tags = el.get("tags", {})
        osm_name = tags.get("name", "")

        if not osm_name:
            continue

        score = name_similarity(db_name, osm_name)

        # 完全一致は即採用
        if score == 1.0:
            return el

        if score >= threshold and score > best_score:
            best_score = score
            best_element = el

    return best_element


def geocode_prefecture(
    session: Session,
    prefecture: str,
    dry_run: bool = False,
) -> tuple[int, int, int]:
    """指定都道府県の lat IS NULL 銭湯を OSM データで座標補完する。

    Returns:
        (matched, skipped, total_null) のタプル
    """
    # 1. DB から lat IS NULL の銭湯を取得
    rows = session.execute(
        text(
            "SELECT id, name, address FROM sentos "
            "WHERE prefecture = :pref AND lat IS NULL"
        ),
        {"pref": prefecture},
    ).fetchall()

    if not rows:
        logger.info("%s: lat IS NULL の銭湯なし", prefecture)
        return 0, 0, 0

    logger.info("%s: lat IS NULL の銭湯 %d 件", prefecture, len(rows))

    # 2. OSM から一括取得
    osm_elements = fetch_osm_public_baths(prefecture)
    if not osm_elements:
        logger.warning("%s: OSM データ取得失敗", prefecture)
        return 0, len(rows), len(rows)

    # 3. マッチング
    matched = 0
    skipped = 0
    for row_id, name, address in rows:
        element = find_best_match(name, address, osm_elements)
        if element is None:
            logger.debug("マッチなし: %s", name)
            skipped += 1
            continue

        lat, lng = extract_coords(element)
        if lat is None or lng is None:
            logger.debug("座標なし: %s", name)
            skipped += 1
            continue

        osm_name = element.get("tags", {}).get("name", "")
        logger.info(
            "マッチ: DB=%s  OSM=%s  (%.2f, %.2f)",
            name,
            osm_name,
            lat,
            lng,
        )

        if not dry_run:
            session.execute(
                text(
                    "UPDATE sentos SET lat = :lat, lng = :lng, "
                    "geocoded_by = 'osm', updated_at = NOW() "
                    "WHERE id = :id"
                ),
                {"lat": lat, "lng": lng, "id": row_id},
            )
            session.commit()

        matched += 1

    return matched, skipped, len(rows)


def import_new_prefecture(
    session: Optional[Session],
    prefecture: str,
    dry_run: bool = False,
) -> tuple[int, int, int]:
    """指定都道府県の OSM 施設データを新規 INSERT する。

    source_url = "osm:{element_id}" で重複チェックし、未登録のみ INSERT する。
    dry-run かつ session=None の場合は重複チェックを行わない。

    Returns:
        (inserted, skipped, total) のタプル
    """
    if not dry_run and session is None:
        raise ValueError("non-dry-run では DB セッションが必要です")

    elements = fetch_osm_bath_facilities(prefecture)
    if not elements:
        logger.warning("%s: OSM データ取得失敗", prefecture)
        return 0, 0, 0

    logger.info("%s: OSM 施設 %d 件取得", prefecture, len(elements))

    inserted = 0
    skipped = 0

    for element in elements:
        element_id = element.get("id")
        if element_id is None:
            skipped += 1
            continue

        source_url = f"osm:{element_id}"
        tags = element.get("tags", {})
        name = tags.get("name") or tags.get("name:ja")

        if not name:
            logger.debug("名前なし: element_id=%s", element_id)
            skipped += 1
            continue

        lat, lng = extract_coords(element)
        if lat is None or lng is None:
            logger.debug("座標なし: %s (id=%s)", name, element_id)
            skipped += 1
            continue

        if session is not None:
            # 重複チェック（dry-run + session=None の場合はスキップ）
            existing = session.execute(
                text("SELECT id FROM sentos WHERE source_url = :source_url"),
                {"source_url": source_url},
            ).fetchone()
            if existing:
                logger.debug("既存レコード SKIP: %s (source_url=%s)", name, source_url)
                skipped += 1
                continue

        address = (
            tags.get("addr:full")
            or _build_address(tags, prefecture)
        )
        facility_type = resolve_facility_type(tags)

        logger.info(
            "INSERT: %s / %s / %s (%.4f, %.4f)",
            name,
            address,
            facility_type,
            lat,
            lng,
        )

        if not dry_run:
            session.execute(
                text(
                    """
                    INSERT INTO sentos
                        (name, address, lat, lng, phone, url, open_hours, holiday,
                         prefecture, region, source_url, geocoded_by, facility_type,
                         created_at, updated_at)
                    VALUES
                        (:name, :address, :lat, :lng, :phone, :url, :open_hours, :holiday,
                         :prefecture, :region, :source_url, 'osm', :facility_type,
                         NOW(), NOW())
                    """
                ),
                {
                    "name": name,
                    "address": address,
                    "lat": lat,
                    "lng": lng,
                    "phone": tags.get("phone") or tags.get("contact:phone"),
                    "url": tags.get("website") or tags.get("contact:website"),
                    "open_hours": tags.get("opening_hours"),
                    "holiday": None,
                    "prefecture": prefecture,
                    "region": PREFECTURE_TO_REGION.get(prefecture),
                    "source_url": source_url,
                    "facility_type": facility_type,
                },
            )
            session.commit()

        inserted += 1

    return inserted, skipped, len(elements)


def _build_address(tags: dict, prefecture: str) -> str:
    """OSM の addr タグから住所文字列を構築する。"""
    parts = []
    for key in ("addr:province", "addr:city", "addr:suburb", "addr:quarter",
                "addr:neighbourhood", "addr:street", "addr:housenumber"):
        val = tags.get(key)
        if val:
            parts.append(val)
    if parts:
        return "".join(parts)
    # フォールバック: 都道府県名のみ
    return prefecture


def main() -> None:
    load_dotenv()

    arg_parser = argparse.ArgumentParser(description="OSM Overpass API 座標補完・新規インポート")
    mode_group = arg_parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--import-new",
        action="store_true",
        help="新規レコードを OSM から INSERT する（公式パーサー未実装都道府県向け）",
    )
    pref_group = arg_parser.add_mutually_exclusive_group(required=True)
    pref_group.add_argument("--prefecture", metavar="NAME", help="対象都道府県（例: 大阪府）")
    pref_group.add_argument("--all", action="store_true", help="全都道府県を処理")
    arg_parser.add_argument("--dry-run", action="store_true", help="DB 更新を行わず結果を表示")
    args = arg_parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        stream=sys.stderr,
    )

    session: Optional[Session] = None
    if not (args.import_new and args.dry_run):
        engine = get_engine()
        session = Session(engine)

    if args.dry_run:
        logger.info("ドライランモード: DB 更新はスキップします")
        if args.import_new:
            logger.info("import-new dry-run: DB 接続なしで OSM データ検証を実行します")

    if args.all:
        if args.import_new:
            # 公式パーサー実装済みの都道府県は除外
            prefectures = [p for p in PREFECTURE_NAMES if p not in PARSER_IMPLEMENTED_PREFECTURES]
            logger.info("OSM インポート対象: %d 都道府県（公式パーサー実装済み %d 県を除外）",
                        len(prefectures), len(PARSER_IMPLEMENTED_PREFECTURES))
        else:
            prefectures = PREFECTURE_NAMES
    else:
        prefectures = [args.prefecture]

    total_primary = 0  # matched (補完) or inserted (インポート)
    total_skipped = 0
    total_total = 0

    try:
        for i, pref in enumerate(prefectures):
            if args.import_new:
                primary, skipped, total = import_new_prefecture(session, pref, dry_run=args.dry_run)
                logger.info("%s: INSERT=%d / スキップ=%d / 合計=%d", pref, primary, skipped, total)
            else:
                primary, skipped, total = geocode_prefecture(session, pref, dry_run=args.dry_run)
                logger.info("%s: 座標補完=%d / スキップ=%d / 対象=%d", pref, primary, skipped, total)

            total_primary += primary
            total_skipped += skipped
            total_total += total

            # 都道府県間のインターバル（Overpass API への負荷軽減）
            if args.all and i < len(prefectures) - 1 and total > 0:
                time.sleep(5)
    finally:
        if session is not None:
            session.close()

    if args.import_new:
        logger.info(
            "完了 - INSERT: %d / スキップ: %d / 合計: %d",
            total_primary,
            total_skipped,
            total_total,
        )
    else:
        logger.info(
            "完了 - 座標補完: %d / スキップ: %d / 対象合計: %d",
            total_primary,
            total_skipped,
            total_total,
        )


if __name__ == "__main__":
    main()
