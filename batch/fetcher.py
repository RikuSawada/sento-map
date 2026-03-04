"""HTTP 取得モジュール。リクエスト間隔を制御する。"""
import logging
import time
from typing import Optional

import requests

USER_AGENT = "sento-map-bot/1.0 (https://github.com/RikuSawada/sento-map; educational purpose)"

logger = logging.getLogger(__name__)


def fetch(url: str, interval: float = 2.0) -> Optional[str]:
    """指定 URL の HTML を取得する。

    失敗時は None を返す。リトライしない。
    interval 秒スリープは成功・失敗問わず必ず実施する。
    """
    try:
        response = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=30,
        )
        response.encoding = response.apparent_encoding
        if response.status_code >= 400:
            logger.error("HTTP %d: %s", response.status_code, url)
            return None
        return response.text
    except requests.RequestException as exc:
        logger.error("接続エラー %s: %s", url, exc)
        return None
    finally:
        time.sleep(interval)
