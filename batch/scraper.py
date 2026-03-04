"""
銭湯情報スクレイパー (1010.or.jp)

usage:
  uv run python scraper.py                      # 通常実行（DB に UPSERT）
  uv run python scraper.py --dry-run            # ドライラン（標準出力のみ、DB 書き込みなし）
  uv run python scraper.py --dry-run --limit 5  # 最初の 5 件だけ処理
"""
import argparse
import json
import logging
import sys
from typing import Optional

from dotenv import load_dotenv

from fetcher import fetch
from parser import parse_item_urls, parse_last_page, parse_sento

BASE_URL = "https://www.1010.or.jp"
LIST_URL = f"{BASE_URL}/map/item"
REQUEST_INTERVAL = 2.0  # サーバ負荷軽減のため最低 2 秒のリクエスト間隔


def collect_all_item_urls(logger: logging.Logger) -> list[str]:
    """全ページを巡回して銭湯個別ページの URL を収集する。"""
    # ページ1を取得して最終ページ番号を取得
    page1_url = f"{LIST_URL}/page/1"
    logger.info("ページ1を取得中: %s", page1_url)
    page1_html = fetch(page1_url, interval=REQUEST_INTERVAL)
    if not page1_html:
        logger.error("ページ1の取得に失敗しました")
        return []

    all_urls = parse_item_urls(page1_html)
    last_page = parse_last_page(page1_html)
    logger.info("全 %d ページを処理します（ページ1: %d 件取得済み）", last_page, len(all_urls))

    for page_num in range(2, last_page + 1):
        page_url = f"{LIST_URL}/page/{page_num}"
        logger.info("一覧ページ %d/%d を取得中: %s", page_num, last_page, page_url)
        html = fetch(page_url, interval=REQUEST_INTERVAL)
        if not html:
            logger.error("ページ %d の取得に失敗しました（スキップ）", page_num)
            continue
        urls = parse_item_urls(html)
        all_urls.extend(urls)
        logger.info("ページ %d: %d 件取得（累計 %d 件）", page_num, len(urls), len(all_urls))

    # 重複除去（順序維持）
    seen: set[str] = set()
    unique_urls: list[str] = []
    for u in all_urls:
        if u not in seen:
            seen.add(u)
            unique_urls.append(u)

    logger.info("全ページ収集完了: %d 件（重複除去後）", len(unique_urls))
    return unique_urls


def main() -> None:
    load_dotenv()

    arg_parser = argparse.ArgumentParser(description="1010.or.jp 銭湯スクレイパー")
    arg_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="DB への書き込みを行わず、標準出力に結果を表示する",
    )
    arg_parser.add_argument(
        "--limit",
        type=int,
        default=0,
        metavar="N",
        help="処理する銭湯数の上限（0 = 全件）",
    )
    args = arg_parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        stream=sys.stderr,
    )
    logger = logging.getLogger(__name__)

    # --- DB セットアップ（dry-run でない場合のみ）---
    session: Optional[object] = None
    if not args.dry_run:
        try:
            from db import get_engine, upsert_sento
            from sqlalchemy.orm import Session

            engine = get_engine()
            session = Session(engine)
            logger.info("DB 接続完了")
        except Exception as exc:
            logger.error("DB 接続失敗: %s", exc)
            sys.exit(1)
    else:
        logger.info("ドライランモード: DB への書き込みはスキップします")

    # 1. 全ページを巡回して銭湯 URL を収集
    item_urls = collect_all_item_urls(logger)
    if not item_urls:
        logger.error("銭湯 URL が0件でした。サイト構造が変わった可能性があります")
        sys.exit(1)

    # --limit 指定がある場合は件数を絞る
    if args.limit > 0:
        item_urls = item_urls[: args.limit]
        logger.info("--limit %d 件に絞って処理します", args.limit)

    total = len(item_urls)
    logger.info("個別ページ処理対象: %d 件", total)

    # 2. 各個別ページをスクレイピング
    success_count = 0
    skip_count = 0
    fail_count = 0

    for i, url in enumerate(item_urls, start=1):
        logger.info("[%d/%d] 取得中: %s", i, total, url)

        html = fetch(url, interval=REQUEST_INTERVAL)
        if not html:
            logger.error("取得失敗（スキップ）: %s", url)
            fail_count += 1
            continue

        data = parse_sento(html, url)
        if data is None:
            logger.warning("パース失敗（必須フィールド欠損、スキップ）: %s", url)
            skip_count += 1
            continue

        # 3. DB に UPSERT または dry-run 出力
        if args.dry_run:
            print(json.dumps(data, ensure_ascii=False, indent=2))
            success_count += 1
        else:
            from db import upsert_sento

            ok = upsert_sento(session, data)  # type: ignore[arg-type]
            if ok:
                logger.info("UPSERT 完了: %s", data["name"])
                success_count += 1
            else:
                fail_count += 1

    # DB セッションを閉じる
    if session is not None:
        session.close()  # type: ignore[union-attr]

    # 4. 統計ログ出力
    logger.info(
        "完了 - 成功: %d / スキップ: %d / 失敗: %d / 合計: %d",
        success_count,
        skip_count,
        fail_count,
        total,
    )

    if fail_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
