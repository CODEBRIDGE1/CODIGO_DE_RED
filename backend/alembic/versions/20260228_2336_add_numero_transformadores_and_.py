"""Add numero_transformadores and observaciones to quotes, quote_item_id to quote_lines

Revision ID: 50ea586af333
Revises: 82d63b904bbe
Create Date: 2026-02-28 23:36:56.039876

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '50ea586af333'
down_revision: Union[str, None] = '82d63b904bbe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _drop_index_if_exists(index_name: str) -> None:
    op.execute(f'DROP INDEX IF EXISTS {index_name}')


def _drop_constraint_if_exists(table: str, constraint: str) -> None:
    op.execute(
        f"DO $$ BEGIN "
        f"IF EXISTS (SELECT 1 FROM information_schema.table_constraints "
        f"WHERE table_name='{table}' AND constraint_name='{constraint}') "
        f"THEN ALTER TABLE {table} DROP CONSTRAINT {constraint}; END IF; END $$"
    )


def _create_index_if_not_exists(index_name: str, table: str, columns: str, unique: str = '') -> None:
    op.execute(f'CREATE INDEX IF NOT EXISTS {index_name} ON {table} ({columns})')


def _create_unique_index_if_not_exists(index_name: str, table: str, columns: str) -> None:
    op.execute(f'CREATE UNIQUE INDEX IF NOT EXISTS {index_name} ON {table} ({columns})')


def upgrade() -> None:
    # All DROP operations use IF EXISTS / DO blocks to be safe across environments
    # (production DB schema may differ from local dev schema at this migration point)

    # Old dev-only 'tasks' table cleanup
    _drop_index_if_exists('ix_tasks_project_id')
    _drop_index_if_exists('ix_tasks_status')
    _drop_index_if_exists('ix_tasks_tenant_id')
    op.execute('DROP TABLE IF EXISTS tasks')

    # companies
    op.alter_column('companies', 'rpu',
               existing_type=sa.VARCHAR(length=50),
               nullable=False)
    op.alter_column('companies', 'tipo_suministro',
               existing_type=sa.VARCHAR(length=50),
               nullable=False)
    op.alter_column('companies', 'is_active',
               existing_type=sa.BOOLEAN(),
               nullable=True,
               existing_server_default=sa.text('true'))

    # company_classifications indexes/constraints
    _drop_index_if_exists('ix_company_classifications_company_id')
    _drop_index_if_exists('ix_company_classifications_tenant_id')
    _create_index_if_not_exists('ix_company_classifications_id', 'company_classifications', 'id')
    _drop_constraint_if_exists('company_classifications', 'company_classifications_company_id_fkey')
    op.execute(
        "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints "
        "WHERE table_name='company_classifications' AND constraint_name='company_classifications_company_id_fkey1') "
        "THEN ALTER TABLE company_classifications ADD FOREIGN KEY (company_id) REFERENCES companies (id); END IF; END $$"
    )

    # compliance_audit_logs
    _drop_index_if_exists('ix_compliance_audit_logs_company_id')
    _drop_index_if_exists('ix_compliance_audit_logs_created_at')
    _drop_index_if_exists('ix_compliance_audit_logs_tenant_id')
    _create_index_if_not_exists('ix_compliance_audit_logs_id', 'compliance_audit_logs', 'id')
    _drop_constraint_if_exists('compliance_audit_logs', 'compliance_audit_logs_company_id_fkey')
    op.execute(
        "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints "
        "WHERE table_name='compliance_audit_logs' AND constraint_name='compliance_audit_logs_company_id_fkey1') "
        "THEN ALTER TABLE compliance_audit_logs ADD FOREIGN KEY (company_id) REFERENCES companies (id); END IF; END $$"
    )

    # compliance_requirements
    op.alter_column('compliance_requirements', 'is_active',
               existing_type=sa.BOOLEAN(),
               nullable=True,
               existing_server_default=sa.text('true'))
    op.alter_column('compliance_requirements', 'created_at',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True)
    _drop_constraint_if_exists('compliance_requirements', 'compliance_requirements_codigo_key')
    _drop_index_if_exists('ix_compliance_requirements_codigo')
    _create_unique_index_if_not_exists('ix_compliance_requirements_codigo', 'compliance_requirements', 'codigo')
    _create_index_if_not_exists('ix_compliance_requirements_id', 'compliance_requirements', 'id')

    # compliance_rules
    op.alter_column('compliance_rules', 'created_at',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True,
               existing_server_default=sa.text('now()'))
    _drop_index_if_exists('ix_compliance_rules_requirement_id')
    _drop_index_if_exists('ix_compliance_rules_tipo')
    _create_index_if_not_exists('ix_compliance_rules_id', 'compliance_rules', 'id')
    _drop_constraint_if_exists('compliance_rules', 'compliance_rules_requirement_id_fkey')
    op.execute(
        "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints "
        "WHERE table_name='compliance_rules' AND constraint_name='compliance_rules_requirement_id_fkey1') "
        "THEN ALTER TABLE compliance_rules ADD FOREIGN KEY (requirement_id) REFERENCES compliance_requirements (id); END IF; END $$"
    )

    # documents
    op.alter_column('documents', 'is_active',
               existing_type=sa.BOOLEAN(),
               nullable=True,
               existing_server_default=sa.text('true'))
    op.alter_column('documents', 'created_at',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True,
               existing_server_default=sa.text('now()'))
    op.alter_column('documents', 'updated_at',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True,
               existing_server_default=sa.text('now()'))
    _drop_index_if_exists('ix_documents_company_id')
    _drop_index_if_exists('ix_documents_tenant_id')
    _drop_index_if_exists('ix_documents_tipo_documento')
    _create_index_if_not_exists('ix_documents_id', 'documents', 'id')

    # project_tasks
    op.alter_column('project_tasks', 'updated_at',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True,
               existing_server_default=sa.text('now()'))
    _drop_index_if_exists('ix_project_tasks_project')
    _create_index_if_not_exists('ix_project_tasks_id', 'project_tasks', 'id')
    _create_index_if_not_exists('ix_project_tasks_project_id', 'project_tasks', 'project_id')

    # projects
    op.alter_column('projects', 'name',
               existing_type=sa.VARCHAR(length=300),
               type_=sa.String(length=200),
               existing_nullable=False)
    op.alter_column('projects', 'created_at',
               existing_type=postgresql.TIMESTAMP(),
               nullable=False)
    _create_index_if_not_exists('ix_projects_id', 'projects', 'id')

    # quote_items
    op.alter_column('quote_items', 'updated_at',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True,
               existing_server_default=sa.text('now()'))

    # quote_lines
    op.execute(
        "ALTER TABLE quote_lines ADD COLUMN IF NOT EXISTS quote_item_id INTEGER"
    )
    _drop_index_if_exists('ix_quote_items_quote_id')
    _drop_index_if_exists('ix_quote_items_tenant_id')
    _create_index_if_not_exists('ix_quote_lines_quote_id', 'quote_lines', 'quote_id')
    _create_index_if_not_exists('ix_quote_lines_quote_item_id', 'quote_lines', 'quote_item_id')
    _create_index_if_not_exists('ix_quote_lines_tenant_id', 'quote_lines', 'tenant_id')
    op.execute(
        "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints "
        "WHERE table_name='quote_lines' AND constraint_name='quote_lines_quote_item_id_fkey') "
        "THEN ALTER TABLE quote_lines ADD FOREIGN KEY (quote_item_id) REFERENCES quote_items (id); END IF; END $$"
    )

    # quotes
    op.execute("ALTER TABLE quotes ADD COLUMN IF NOT EXISTS numero_transformadores INTEGER")
    op.execute("ALTER TABLE quotes ADD COLUMN IF NOT EXISTS observaciones TEXT")

    # task_activity_logs
    _drop_index_if_exists('ix_task_activity_logs_task')
    _create_index_if_not_exists('ix_task_activity_logs_id', 'task_activity_logs', 'id')
    _create_index_if_not_exists('ix_task_activity_logs_task_id', 'task_activity_logs', 'task_id')

    # task_comments
    op.alter_column('task_comments', 'updated_at',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True,
               existing_server_default=sa.text('now()'))
    _drop_index_if_exists('ix_task_comments_task')
    _create_index_if_not_exists('ix_task_comments_id', 'task_comments', 'id')
    _create_index_if_not_exists('ix_task_comments_task_id', 'task_comments', 'task_id')

    # task_evidences
    _drop_index_if_exists('ix_task_evidences_task')
    _create_index_if_not_exists('ix_task_evidences_id', 'task_evidences', 'id')
    _create_index_if_not_exists('ix_task_evidences_task_id', 'task_evidences', 'task_id')

    # tenant_quote_item_prices
    op.alter_column('tenant_quote_item_prices', 'updated_at',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True,
               existing_server_default=sa.text('now()'))
    _drop_constraint_if_exists('tenant_quote_item_prices', 'uq_tenant_quote_item')
    _drop_constraint_if_exists('tenant_quote_item_prices', 'tenant_quote_item_prices_quote_item_id_fkey')
    op.execute(
        "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints "
        "WHERE table_name='tenant_quote_item_prices' AND constraint_name='tenant_quote_item_prices_quote_item_id_fkey1') "
        "THEN ALTER TABLE tenant_quote_item_prices ADD FOREIGN KEY (quote_item_id) REFERENCES quote_items (id); END IF; END $$"
    )

    # users
    _drop_constraint_if_exists('users', 'fk_users_security_level_id')
    op.execute(
        "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints "
        "WHERE table_name='users' AND constraint_name='users_security_level_id_fkey') "
        "THEN ALTER TABLE users ADD FOREIGN KEY (security_level_id) REFERENCES security_levels (id); END IF; END $$"
    )


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'users', type_='foreignkey')
    op.create_foreign_key(op.f('fk_users_security_level_id'), 'users', 'security_levels', ['security_level_id'], ['id'], ondelete='SET NULL')
    op.drop_constraint(None, 'tenant_quote_item_prices', type_='foreignkey')
    op.create_foreign_key(op.f('tenant_quote_item_prices_quote_item_id_fkey'), 'tenant_quote_item_prices', 'quote_items', ['quote_item_id'], ['id'], ondelete='CASCADE')
    op.create_unique_constraint(op.f('uq_tenant_quote_item'), 'tenant_quote_item_prices', ['tenant_id', 'quote_item_id'], postgresql_nulls_not_distinct=False)
    op.alter_column('tenant_quote_item_prices', 'updated_at',
               existing_type=postgresql.TIMESTAMP(),
               nullable=False,
               existing_server_default=sa.text('now()'))
    op.drop_index(op.f('ix_task_evidences_task_id'), table_name='task_evidences')
    op.drop_index(op.f('ix_task_evidences_id'), table_name='task_evidences')
    op.create_index(op.f('ix_task_evidences_task'), 'task_evidences', ['task_id'], unique=False)
    op.drop_index(op.f('ix_task_comments_task_id'), table_name='task_comments')
    op.drop_index(op.f('ix_task_comments_id'), table_name='task_comments')
    op.create_index(op.f('ix_task_comments_task'), 'task_comments', ['task_id'], unique=False)
    op.alter_column('task_comments', 'updated_at',
               existing_type=postgresql.TIMESTAMP(),
               nullable=False,
               existing_server_default=sa.text('now()'))
    op.drop_index(op.f('ix_task_activity_logs_task_id'), table_name='task_activity_logs')
    op.drop_index(op.f('ix_task_activity_logs_id'), table_name='task_activity_logs')
    op.create_index(op.f('ix_task_activity_logs_task'), 'task_activity_logs', ['task_id'], unique=False)
    op.drop_column('quotes', 'observaciones')
    op.drop_column('quotes', 'numero_transformadores')
    op.drop_constraint(None, 'quote_lines', type_='foreignkey')
    op.drop_index(op.f('ix_quote_lines_tenant_id'), table_name='quote_lines')
    op.drop_index(op.f('ix_quote_lines_quote_item_id'), table_name='quote_lines')
    op.drop_index(op.f('ix_quote_lines_quote_id'), table_name='quote_lines')
    op.create_index(op.f('ix_quote_items_tenant_id'), 'quote_lines', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_quote_items_quote_id'), 'quote_lines', ['quote_id'], unique=False)
    op.drop_column('quote_lines', 'quote_item_id')
    op.alter_column('quote_items', 'updated_at',
               existing_type=postgresql.TIMESTAMP(),
               nullable=False,
               existing_server_default=sa.text('now()'))
    op.drop_index(op.f('ix_projects_id'), table_name='projects')
    op.alter_column('projects', 'created_at',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True)
    op.alter_column('projects', 'name',
               existing_type=sa.String(length=200),
               type_=sa.VARCHAR(length=300),
               existing_nullable=False)
    op.drop_index(op.f('ix_project_tasks_project_id'), table_name='project_tasks')
    op.drop_index(op.f('ix_project_tasks_id'), table_name='project_tasks')
    op.create_index(op.f('ix_project_tasks_project'), 'project_tasks', ['project_id'], unique=False)
    op.alter_column('project_tasks', 'updated_at',
               existing_type=postgresql.TIMESTAMP(),
               nullable=False,
               existing_server_default=sa.text('now()'))
    op.drop_index(op.f('ix_documents_id'), table_name='documents')
    op.create_index(op.f('ix_documents_tipo_documento'), 'documents', ['tipo_documento'], unique=False)
    op.create_index(op.f('ix_documents_tenant_id'), 'documents', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_documents_company_id'), 'documents', ['company_id'], unique=False)
    op.alter_column('documents', 'updated_at',
               existing_type=postgresql.TIMESTAMP(),
               nullable=False,
               existing_server_default=sa.text('now()'))
    op.alter_column('documents', 'created_at',
               existing_type=postgresql.TIMESTAMP(),
               nullable=False,
               existing_server_default=sa.text('now()'))
    op.alter_column('documents', 'is_active',
               existing_type=sa.BOOLEAN(),
               nullable=False,
               existing_server_default=sa.text('true'))
    op.drop_constraint(None, 'compliance_rules', type_='foreignkey')
    op.create_foreign_key(op.f('compliance_rules_requirement_id_fkey'), 'compliance_rules', 'compliance_requirements', ['requirement_id'], ['id'], ondelete='CASCADE')
    op.drop_index(op.f('ix_compliance_rules_id'), table_name='compliance_rules')
    op.create_index(op.f('ix_compliance_rules_tipo'), 'compliance_rules', ['tipo_centro_carga'], unique=False)
    op.create_index(op.f('ix_compliance_rules_requirement_id'), 'compliance_rules', ['requirement_id'], unique=False)
    op.alter_column('compliance_rules', 'created_at',
               existing_type=postgresql.TIMESTAMP(),
               nullable=False,
               existing_server_default=sa.text('now()'))
    op.drop_index(op.f('ix_compliance_requirements_id'), table_name='compliance_requirements')
    op.drop_index(op.f('ix_compliance_requirements_codigo'), table_name='compliance_requirements')
    op.create_index(op.f('ix_compliance_requirements_codigo'), 'compliance_requirements', ['codigo'], unique=False)
    op.create_unique_constraint(op.f('compliance_requirements_codigo_key'), 'compliance_requirements', ['codigo'], postgresql_nulls_not_distinct=False)
    op.alter_column('compliance_requirements', 'created_at',
               existing_type=postgresql.TIMESTAMP(),
               nullable=False)
    op.alter_column('compliance_requirements', 'is_active',
               existing_type=sa.BOOLEAN(),
               nullable=False,
               existing_server_default=sa.text('true'))
    op.drop_constraint(None, 'compliance_audit_logs', type_='foreignkey')
    op.create_foreign_key(op.f('compliance_audit_logs_company_id_fkey'), 'compliance_audit_logs', 'companies', ['company_id'], ['id'], ondelete='SET NULL')
    op.drop_index(op.f('ix_compliance_audit_logs_id'), table_name='compliance_audit_logs')
    op.create_index(op.f('ix_compliance_audit_logs_tenant_id'), 'compliance_audit_logs', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_compliance_audit_logs_created_at'), 'compliance_audit_logs', ['created_at'], unique=False)
    op.create_index(op.f('ix_compliance_audit_logs_company_id'), 'compliance_audit_logs', ['company_id'], unique=False)
    op.drop_constraint(None, 'company_classifications', type_='foreignkey')
    op.create_foreign_key(op.f('company_classifications_company_id_fkey'), 'company_classifications', 'companies', ['company_id'], ['id'], ondelete='CASCADE')
    op.drop_index(op.f('ix_company_classifications_id'), table_name='company_classifications')
    op.create_index(op.f('ix_company_classifications_tenant_id'), 'company_classifications', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_company_classifications_company_id'), 'company_classifications', ['company_id'], unique=False)
    op.alter_column('companies', 'is_active',
               existing_type=sa.BOOLEAN(),
               nullable=False,
               existing_server_default=sa.text('true'))
    op.alter_column('companies', 'tipo_suministro',
               existing_type=sa.VARCHAR(length=50),
               nullable=True)
    op.alter_column('companies', 'rpu',
               existing_type=sa.VARCHAR(length=50),
               nullable=True)
    op.create_table('tasks',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('tenant_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('project_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('title', sa.VARCHAR(length=300), autoincrement=False, nullable=False),
    sa.Column('status', sa.VARCHAR(length=50), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('updated_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name=op.f('tasks_project_id_fkey')),
    sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name=op.f('tasks_tenant_id_fkey')),
    sa.PrimaryKeyConstraint('id', name=op.f('tasks_pkey'))
    )
    op.create_index(op.f('ix_tasks_tenant_id'), 'tasks', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_tasks_status'), 'tasks', ['status'], unique=False)
    op.create_index(op.f('ix_tasks_project_id'), 'tasks', ['project_id'], unique=False)
    # ### end Alembic commands ###
