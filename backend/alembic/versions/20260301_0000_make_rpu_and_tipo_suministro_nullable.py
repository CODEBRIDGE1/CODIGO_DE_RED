"""make rpu and tipo_suministro nullable in companies

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-03-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop the NOT NULL constraint and unique index on rpu, make nullable
    op.alter_column('companies', 'rpu',
                    existing_type=sa.String(50),
                    nullable=True)

    # Drop the NOT NULL constraint on tipo_suministro, make nullable
    op.alter_column('companies', 'tipo_suministro',
                    existing_type=sa.String(50),
                    nullable=True)


def downgrade() -> None:
    op.alter_column('companies', 'rpu',
                    existing_type=sa.String(50),
                    nullable=False)
    op.alter_column('companies', 'tipo_suministro',
                    existing_type=sa.String(50),
                    nullable=False)
