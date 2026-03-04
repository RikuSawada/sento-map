"""add prefecture, region, source_url to sentos

Revision ID: a1b2c3d4e5f6
Revises: 171902c5cd9f
Create Date: 2026-03-04 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "171902c5cd9f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add prefecture, region, source_url columns to sentos table."""
    op.add_column("sentos", sa.Column("prefecture", sa.String(10), nullable=True))
    op.add_column("sentos", sa.Column("region", sa.String(20), nullable=True))
    op.add_column("sentos", sa.Column("source_url", sa.Text(), nullable=True))

    op.create_index("ix_sentos_prefecture", "sentos", ["prefecture"])

    # 既存データ（1010.or.jp 由来の東京データ）に prefecture = '東京都' を設定
    # 注: スクレイパーが「品川区〜」形式で住所を保存するため LIKE '東京都%' は使わない
    op.execute(
        "UPDATE sentos SET prefecture = '東京都', region = '関東' "
        "WHERE prefecture IS NULL"
    )


def downgrade() -> None:
    """Remove prefecture, region, source_url columns from sentos table."""
    op.drop_index("ix_sentos_prefecture", table_name="sentos")
    op.drop_column("sentos", "source_url")
    op.drop_column("sentos", "region")
    op.drop_column("sentos", "prefecture")
