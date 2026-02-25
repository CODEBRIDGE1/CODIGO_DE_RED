"""create_compliance_tables

Revision ID: 20260223_0100
Revises: 106a4efd50b9
Create Date: 2026-02-23 01:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260223_0100'
down_revision = '106a4efd50b9'
branch_labels = None
depends_on = None


def upgrade():
    # Create ENUM types
    tipocentrocarga_enum = sa.Enum('TIPO_A', 'TIPO_B', 'TIPO_C', name='tipocentrocarga')
    tipocentrocarga_enum.create(op.get_bind(), checkfirst=True)
    
    estadoaplicabilidad_enum = sa.Enum('APLICA', 'NO_APLICA', 'APLICA_RDC', 'APLICA_TIC', name='estadoaplicabilidad')
    estadoaplicabilidad_enum.create(op.get_bind(), checkfirst=True)
    
    # Create company_classifications table
    op.create_table(
        'company_classifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('tipo_centro_carga', sa.String(20), nullable=False),
        sa.Column('justificacion', sa.Text(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('company_id')
    )
    op.create_index('ix_company_classifications_company_id', 'company_classifications', ['company_id'])
    op.create_index('ix_company_classifications_tenant_id', 'company_classifications', ['tenant_id'])

    # Create compliance_requirements table
    op.create_table(
        'compliance_requirements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('codigo', sa.String(20), nullable=False),
        sa.Column('nombre', sa.String(200), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('orden', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['parent_id'], ['compliance_requirements.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('codigo')
    )
    op.create_index('ix_compliance_requirements_codigo', 'compliance_requirements', ['codigo'])

    # Create compliance_rules table
    op.create_table(
        'compliance_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('requirement_id', sa.Integer(), nullable=False),
        sa.Column('tipo_centro_carga', sa.String(20), nullable=False),
        sa.Column('estado_aplicabilidad', sa.String(20), nullable=False),
        sa.Column('notas', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['requirement_id'], ['compliance_requirements.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_compliance_rules_requirement_id', 'compliance_rules', ['requirement_id'])
    op.create_index('ix_compliance_rules_tipo', 'compliance_rules', ['tipo_centro_carga'])

    # Create compliance_audit_logs table
    op.create_table(
        'compliance_audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('action_type', sa.String(50), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('old_value', sa.Text(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_compliance_audit_logs_company_id', 'compliance_audit_logs', ['company_id'])
    op.create_index('ix_compliance_audit_logs_tenant_id', 'compliance_audit_logs', ['tenant_id'])
    op.create_index('ix_compliance_audit_logs_created_at', 'compliance_audit_logs', ['created_at'])


def downgrade():
    op.drop_table('compliance_audit_logs')
    op.drop_table('compliance_rules')
    op.drop_table('compliance_requirements')
    op.drop_table('company_classifications')
    
    # Drop ENUM types
    sa.Enum(name='estadoaplicabilidad').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='tipocentrocarga').drop(op.get_bind(), checkfirst=True)
