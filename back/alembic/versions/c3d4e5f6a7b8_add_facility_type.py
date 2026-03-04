"""add facility_type column for sento/onsen/super_sento classification

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-03-04 02:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, Sequence[str], None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add facility_type column to distinguish sento/onsen/super_sento."""
    op.add_column(
        "sentos",
        sa.Column("facility_type", sa.String(20), nullable=True),
    )
    # 既存レコードは銭湯として扱う（1010.or.jp は普通公衆浴場のみ）
    op.execute("UPDATE sentos SET facility_type = 'sento' WHERE facility_type IS NULL")


def downgrade() -> None:
    """Remove facility_type column."""
    op.drop_column("sentos", "facility_type")
