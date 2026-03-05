"""add geocoded_by, make lat/lng nullable for OSM geocoding

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-03-04 01:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add geocoded_by column and make lat/lng nullable for OSM geocoding support."""
    op.add_column(
        "sentos",
        sa.Column("geocoded_by", sa.String(20), nullable=True),
    )
    # lat/lng を nullable に変更（全国スクレイパーで座標なし施設を保存可能にする）
    op.alter_column("sentos", "lat", existing_type=sa.Float(), nullable=True)
    op.alter_column("sentos", "lng", existing_type=sa.Float(), nullable=True)

    # 既存データは batch スクレイパー由来なのでフラグを設定
    op.execute("UPDATE sentos SET geocoded_by = 'batch' WHERE lat IS NOT NULL AND geocoded_by IS NULL")


def downgrade() -> None:
    """Revert lat/lng to NOT NULL and drop geocoded_by."""
    # NULL 値があると NOT NULL に戻せないため、NULL を 0 に変換してから戻す
    op.execute("UPDATE sentos SET lat = 0.0 WHERE lat IS NULL")
    op.execute("UPDATE sentos SET lng = 0.0 WHERE lng IS NULL")
    op.alter_column("sentos", "lat", existing_type=sa.Float(), nullable=False)
    op.alter_column("sentos", "lng", existing_type=sa.Float(), nullable=False)
    op.drop_column("sentos", "geocoded_by")
