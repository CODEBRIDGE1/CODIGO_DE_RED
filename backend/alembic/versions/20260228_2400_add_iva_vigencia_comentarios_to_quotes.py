"""Add iva_percent, fecha_vigencia, comentarios_admin to quotes

Revision ID: a1b2c3d4e5f6
Revises: 50ea586af333
Create Date: 2026-02-28 24:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '50ea586af333'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('quotes', sa.Column('iva_percent', sa.Integer(), nullable=True, server_default='16'))
    op.add_column('quotes', sa.Column('iva_amount', sa.Numeric(15, 2), nullable=True, server_default='0'))
    op.add_column('quotes', sa.Column('total_con_iva', sa.Numeric(15, 2), nullable=True, server_default='0'))
    op.add_column('quotes', sa.Column('fecha_vigencia', sa.Date(), nullable=True))
    op.add_column('quotes', sa.Column('comentarios_admin', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('quotes', 'comentarios_admin')
    op.drop_column('quotes', 'fecha_vigencia')
    op.drop_column('quotes', 'total_con_iva')
    op.drop_column('quotes', 'iva_amount')
    op.drop_column('quotes', 'iva_percent')
