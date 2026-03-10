"""
銭湯情報スクレイパー

usage:
  uv run python scraper.py                                  # 東京（デフォルト）
  uv run python scraper.py --region 東京都                  # 東京のみ
  uv run python scraper.py --region 京都府                  # 京都のみ
  uv run python scraper.py --region 福岡県                  # 福岡のみ
  uv run python scraper.py --all                            # 実装済み全都道府県
  uv run python scraper.py --dry-run                        # ドライラン（DB 書き込みなし）
  uv run python scraper.py --dry-run --limit 5 --region 東京都
"""
import argparse
import json
import logging
import sys
from typing import Optional

from dotenv import load_dotenv

from fetcher import fetch
from osm_geocoder import geocode_prefecture
from parsers import PARSERS, BaseParser
from parsers.tokyo import TokyoParser

REQUEST_INTERVAL = 2.0
_GEOCODE_REQUIRED_PREFECTURES: frozenset[str] = frozenset({"北海道"})


def _post_geocode_if_needed(
    prefecture: str,
    logger: logging.Logger,
    session: Optional[object],
    dry_run: bool,
) -> None:
    """必要な都道府県のみ、スクレイピング後に座標補完を実行する。"""
    if dry_run or prefecture not in _GEOCODE_REQUIRED_PREFECTURES:
        return
    if session is None:
        logger.error("北海道の座標補完をスキップ: DB セッションがありません")
        return

    logger.info("北海道は公式サイトに座標がないため、OSM で座標補完を実行します")
    matched, skipped, total = geocode_prefecture(session, prefecture, dry_run=False)
    logger.info("%s: OSM座標補完=%d / スキップ=%d / 対象=%d", prefecture, matched, skipped, total)


def run_parser(
    parser: BaseParser,
    logger: logging.Logger,
    session: Optional[object],
    dry_run: bool,
    limit: int,
) -> tuple[int, int, int]:
    """1つのパーサーに対してスクレイピングを実行する。

    Returns:
        (success_count, skip_count, fail_count)
    """
    from db import upsert_sento

    # ---- 全一覧ページ URL の確定 ----
    # ページ1を先行取得してページ数を確定するパーサー（Tokyo・Kyoto）に対応。
    # ページ1 HTML をキャッシュして後のループで再フェッチしない。
    page1_html_cache: dict[str, str] = {}

    if isinstance(parser, TokyoParser):
        list_url_page1 = "https://www.1010.or.jp/map/item/page/1"
        logger.info("ページ1を取得中: %s", list_url_page1)
        p1 = fetch(list_url_page1, interval=REQUEST_INTERVAL)
        if not p1:
            logger.error("ページ1の取得に失敗しました")
            return 0, 0, 1
        parser.update_last_page(p1)
        list_urls = parser.get_list_urls()
        page1_html_cache[list_url_page1] = p1
    else:
        init_urls = parser.get_list_urls()
        if hasattr(parser, "get_all_list_urls"):
            # Kyoto 等: ページ1の HTML からページ数を確定
            page1_url = init_urls[0]
            logger.info("ページ1を取得中（ページ数確定）: %s", page1_url)
            p1 = fetch(page1_url, interval=REQUEST_INTERVAL)
            if not p1:
                logger.error("ページ1の取得に失敗しました")
                return 0, 0, 1
            list_urls = parser.get_all_list_urls(p1)
            page1_html_cache[page1_url] = p1
        else:
            list_urls = init_urls

    # ---- 個別ページ URL を収集 ----
    all_item_urls: list[str] = []
    for i, list_url in enumerate(list_urls):
        logger.info("[一覧 %d/%d] %s", i + 1, len(list_urls), list_url)

        html = page1_html_cache.get(list_url) or fetch(list_url, interval=REQUEST_INTERVAL)

        if not html:
            logger.error("一覧ページ取得失敗（スキップ）: %s", list_url)
            continue

        urls = parser.get_item_urls(html, list_url)
        all_item_urls.extend(urls)
        logger.info("一覧 %d: %d 件取得（累計 %d 件）", i + 1, len(urls), len(all_item_urls))

    # 重複除去
    seen: set[str] = set()
    unique_urls: list[str] = []
    for u in all_item_urls:
        if u not in seen:
            seen.add(u)
            unique_urls.append(u)
    logger.info("個別ページ収集完了: %d 件", len(unique_urls))

    if limit > 0:
        unique_urls = unique_urls[:limit]
        logger.info("--limit %d 件に絞って処理します", limit)

    total = len(unique_urls)
    success_count = 0
    skip_count = 0
    fail_count = 0

    for i, url in enumerate(unique_urls, start=1):
        logger.info("[%d/%d] 取得中: %s", i, total, url)
        html = fetch(url, interval=REQUEST_INTERVAL)
        if not html:
            logger.error("取得失敗（スキップ）: %s", url)
            fail_count += 1
            continue

        data = parser.parse_sento(html, url)
        if data is None:
            logger.warning("パース失敗（スキップ）: %s", url)
            skip_count += 1
            continue

        if dry_run:
            print(json.dumps(data, ensure_ascii=False, indent=2))
            success_count += 1
        else:
            ok = upsert_sento(session, data)  # type: ignore[arg-type]
            if ok:
                logger.info("UPSERT 完了: %s", data["name"])
                success_count += 1
            else:
                fail_count += 1

    return success_count, skip_count, fail_count


def main() -> None:
    load_dotenv()

    arg_parser = argparse.ArgumentParser(description="銭湯組合サイト スクレイパー")
    group = arg_parser.add_mutually_exclusive_group()
    group.add_argument("--region", metavar="PREF", help="対象都道府県（例: 東京都）。省略時は東京都")
    group.add_argument("--all", action="store_true", help="実装済み全都道府県を処理")
    arg_parser.add_argument("--dry-run", action="store_true", help="DB 書き込みなし（標準出力に結果を表示）")
    arg_parser.add_argument("--limit", type=int, default=0, metavar="N", help="処理件数上限（0=全件）")
    args = arg_parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        stream=sys.stderr,
    )
    logger = logging.getLogger(__name__)

    # 対象都道府県を決定
    if args.all:
        target_prefectures = list(PARSERS.keys())
    elif args.region:
        if args.region not in PARSERS:
            logger.error("未実装の都道府県: %s（実装済み: %s）", args.region, list(PARSERS.keys()))
            sys.exit(1)
        target_prefectures = [args.region]
    else:
        target_prefectures = ["東京都"]

    logger.info("対象都道府県: %s", target_prefectures)

    # DB セットアップ
    session: Optional[object] = None
    if not args.dry_run:
        try:
            from db import get_engine
            from sqlalchemy.orm import Session

            engine = get_engine()
            session = Session(engine)
            logger.info("DB 接続完了")
        except Exception as exc:
            logger.error("DB 接続失敗: %s", exc)
            sys.exit(1)
    else:
        logger.info("ドライランモード: DB への書き込みはスキップします")

    total_success = 0
    total_skip = 0
    total_fail = 0

    for pref in target_prefectures:
        logger.info("=== %s を処理中 ===", pref)
        parser = PARSERS[pref]()
        s, sk, f = run_parser(parser, logger, session, args.dry_run, args.limit)
        _post_geocode_if_needed(pref, logger, session, args.dry_run)
        total_success += s
        total_skip += sk
        total_fail += f
        logger.info("%s: 成功=%d / スキップ=%d / 失敗=%d", pref, s, sk, f)

    if session is not None:
        session.close()  # type: ignore[union-attr]

    logger.info(
        "全体完了 - 成功: %d / スキップ: %d / 失敗: %d",
        total_success, total_skip, total_fail,
    )

    if total_fail > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
