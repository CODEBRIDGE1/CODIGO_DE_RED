"""add superadmin_id to tenants

Revision ID: 20260307_0000
Revises: 20260301_1200_add_photo_url_to_users
Create Date: 2026-03-07 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260307_0000'
down_revision = 'f02125977068'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Agregar columna superadmin_id (nullable) a tenants
    op.add_column(
        'tenants',
        sa.Column('superadmin_id', sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        'fk_tenants_superadmin_id',
        'tenants', 'users',
        ['superadmin_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_index('ix_tenants_superadmin_id', 'tenants', ['superadmin_id'])

    # Backfill: asignar el primer superadmin existente a todos los tenants sin asignación
    op.execute("""
        UPDATE tenants
        SET superadmin_id = (
            SELECT id FROM users
            WHERE is_superadmin = true
            ORDER BY id
            LIMIT 1
        )
        WHERE superadmin_id IS NULL
    """)


def downgrade() -> None:
    op.drop_index('ix_tenants_superadmin_id', table_name='tenants')
    op.drop_constraint('fk_tenants_superadmin_id', 'tenants', type_='foreignkey')
    op.drop_column('tenants', 'superadmin_id')
