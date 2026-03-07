"""add pagos to quotes

Revision ID: 20260307_0100
Revises: 20260307_0000
Create Date: 2026-03-07 01:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '20260307_0100'
down_revision = '20260307_0000'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'quotes',
        sa.Column('pagos', sa.JSON(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('quotes', 'pagos')
