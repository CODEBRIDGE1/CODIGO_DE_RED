"""rename quote_items to quote_lines

Revision ID: 026cf65e139d
Revises: 929c252dcd2d
Create Date: 2026-02-28 18:54:46.794599

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '026cf65e139d'
down_revision: Union[str, None] = '929c252dcd2d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Renombrar tabla quote_items a quote_lines para evitar conflicto
    # con el nuevo catálogo global quote_items
    op.rename_table('quote_items', 'quote_lines')


def downgrade() -> None:
    op.rename_table('quote_lines', 'quote_items')
