"""DB 接続・UPSERT 処理。SQLAlchemy Core（同期）を使用。"""
import logging
import os
from typing import Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def get_engine() -> Engine:
    """環境変数 DATABASE_URL から同期エンジンを作成する。

    asyncpg 形式の URL は psycopg2 形式に変換する。
    """
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        raise RuntimeError("環境変数 DATABASE_URL が設定されていません")

    # back/ は postgresql+asyncpg:// を使用するため、バッチ側で変換する
    if "asyncpg" in url:
        url = url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")

    # スキームなし or postgres:// 形式への対応
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg2://", 1)

    return create_engine(url, pool_pre_ping=True)


def upsert_sento(session: Session, data: dict) -> bool:
    """銭湯データを UPSERT する。

    url が存在する場合は url でユニーク判定。
    url が None の場合は name+address で判定。
    更新対象: name, address, lat, lng, phone, open_hours, holiday, updated_at

    Returns:
        True: 成功（INSERT または UPDATE）
        False: 失敗（例外発生）
    """
    try:
        external_url: Optional[str] = data.get("url")

        # 既存レコードを検索
        if external_url:
            row = session.execute(
                text("SELECT id FROM sentos WHERE url = :url"),
                {"url": external_url},
            ).fetchone()
        else:
            row = session.execute(
                text(
                    "SELECT id FROM sentos WHERE name = :name AND address = :address"
                ),
                {"name": data["name"], "address": data["address"]},
            ).fetchone()

        params = {
            "name": data["name"],
            "address": data["address"],
            "lat": data["lat"],
            "lng": data["lng"],
            "phone": data.get("phone"),
            "url": external_url,
            "open_hours": data.get("open_hours"),
            "holiday": data.get("holiday"),
        }

        if row:
            params["id"] = row[0]
            session.execute(
                text(
                    """
                    UPDATE sentos
                    SET name       = :name,
                        address    = :address,
                        lat        = :lat,
                        lng        = :lng,
                        phone      = :phone,
                        url        = :url,
                        open_hours = :open_hours,
                        holiday    = :holiday,
                        updated_at = NOW()
                    WHERE id = :id
                    """
                ),
                params,
            )
            logger.debug("UPDATE: %s (id=%d)", data["name"], row[0])
        else:
            session.execute(
                text(
                    """
                    INSERT INTO sentos
                        (name, address, lat, lng, phone, url, open_hours, holiday,
                         created_at, updated_at)
                    VALUES
                        (:name, :address, :lat, :lng, :phone, :url, :open_hours, :holiday,
                         NOW(), NOW())
                    """
                ),
                params,
            )
            logger.debug("INSERT: %s", data["name"])

        session.commit()
        return True

    except Exception as exc:  # noqa: BLE001
        logger.error("UPSERT 失敗 (name=%s): %s", data.get("name"), exc)
        session.rollback()
        return False
