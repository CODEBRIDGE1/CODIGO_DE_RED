"""merge_branches

Revision ID: 9d8b6e14e653
Revises: add_tenant_contact_fields, a5f44784c761
Create Date: 2026-02-28 21:40:07.545162

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9d8b6e14e653'
down_revision: Union[str, None] = ('add_tenant_contact_fields', 'a5f44784c761')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
