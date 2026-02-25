"""make_rpu_optional

Revision ID: 3812f61f5df1
Revises: d529e184c99c
Create Date: 2026-02-22 23:34:04.694633

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3812f61f5df1'
down_revision: Union[str, None] = 'd529e184c99c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Hacer que las columnas rpu y tipo_suministro sean opcionales (nullable)
    op.alter_column('companies', 'rpu',
                    existing_type=sa.String(length=50),
                    nullable=True)
    op.alter_column('companies', 'tipo_suministro',
                    existing_type=sa.String(length=10),
                    nullable=True)


def downgrade() -> None:
    # Revertir los cambios
    op.alter_column('companies', 'rpu',
                    existing_type=sa.String(length=50),
                    nullable=False)
    op.alter_column('companies', 'tipo_suministro',
                    existing_type=sa.String(length=10),
                    nullable=False)
