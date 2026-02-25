"""create_documents_table

Revision ID: 106a4efd50b9
Revises: 3812f61f5df1
Create Date: 2026-02-22 23:44:46.770199

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '106a4efd50b9'
down_revision: Union[str, None] = '3812f61f5df1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Crear tabla de documentos
    op.create_table(
        'documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('tipo_documento', sa.String(length=50), nullable=False),
        sa.Column('nombre_archivo', sa.String(length=500), nullable=False),
        sa.Column('nombre_original', sa.String(length=500), nullable=False),
        sa.Column('ruta_minio', sa.String(length=1000), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('tamano_bytes', sa.Integer(), nullable=True),
        sa.Column('descripcion', sa.String(length=500), nullable=True),
        sa.Column('vigencia', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'])
    )
    
    # Crear índices
    op.create_index('ix_documents_company_id', 'documents', ['company_id'])
    op.create_index('ix_documents_tenant_id', 'documents', ['tenant_id'])
    op.create_index('ix_documents_tipo_documento', 'documents', ['tipo_documento'])


def downgrade() -> None:
    op.drop_index('ix_documents_tipo_documento', table_name='documents')
    op.drop_index('ix_documents_tenant_id', table_name='documents')
    op.drop_index('ix_documents_company_id', table_name='documents')
    op.drop_table('documents')
