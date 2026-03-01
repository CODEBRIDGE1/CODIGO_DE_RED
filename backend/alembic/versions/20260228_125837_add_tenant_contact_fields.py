"""add tenant contact fields

Revision ID: add_tenant_contact_fields
Revises: 
Create Date: 2026-02-28 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_tenant_contact_fields'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('tenants', sa.Column('contact_name', sa.String(length=200), nullable=True))
    op.add_column('tenants', sa.Column('contact_email', sa.String(length=255), nullable=True))
    op.add_column('tenants', sa.Column('contact_phone', sa.String(length=50), nullable=True))
    op.add_column('tenants', sa.Column('address', sa.Text(), nullable=True))
    op.add_column('tenants', sa.Column('notes', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('tenants', 'notes')
    op.drop_column('tenants', 'address')
    op.drop_column('tenants', 'contact_phone')
    op.drop_column('tenants', 'contact_email')
    op.drop_column('tenants', 'contact_name')
