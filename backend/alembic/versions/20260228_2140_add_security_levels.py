"""add_security_levels

Revision ID: 82d63b904bbe
Revises: 9d8b6e14e653
Create Date: 2026-02-28 21:40:13.965991

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '82d63b904bbe'
down_revision: Union[str, None] = '9d8b6e14e653'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Crear tabla security_levels
    op.create_table(
        'security_levels',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('color', sa.String(length=20), nullable=False, server_default='blue'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )
    op.create_index(op.f('ix_security_levels_id'), 'security_levels', ['id'], unique=False)

    # Crear tabla de asociacion security_level_modules
    op.create_table(
        'security_level_modules',
        sa.Column('security_level_id', sa.Integer(), nullable=False),
        sa.Column('module_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['module_id'], ['modules.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['security_level_id'], ['security_levels.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('security_level_id', 'module_id'),
    )

    # Agregar columna security_level_id a users
    op.add_column('users', sa.Column('security_level_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_users_security_level_id'), 'users', ['security_level_id'], unique=False)
    op.create_foreign_key(
        'fk_users_security_level_id',
        'users', 'security_levels',
        ['security_level_id'], ['id'],
        ondelete='SET NULL'
    )

    # Seed inicial de modulos (solo si la tabla esta vacia)
    op.execute("""
        INSERT INTO modules (key, name, description, icon, sort_order, is_active)
        SELECT key, name, description, icon, sort_order, true
        FROM (VALUES
            ('dashboard',    'Dashboard',            'Vista general y metricas',              'chart-bar',       1),
            ('empresas',     'Empresas',             'Gestion de empresas y centros de carga','building-office', 2),
            ('obligaciones', 'Obligaciones',         'Cumplimiento y obligaciones regulatorias','clipboard-list',3),
            ('proyectos',    'Proyectos',            'Gestion de proyectos electricos',       'folder-open',     4),
            ('documentos',   'Documentos',           'Repositorio documental',                'document',        5),
            ('reportes',     'Reportes',             'Reportes y analisis',                   'chart-pie',       6),
            ('usuarios',     'Usuarios',             'Administracion de usuarios',            'users',           7),
            ('auditoria',    'Auditoria',            'Registro de actividad',                 'shield-check',    8),
            ('cotizaciones', 'Cotizaciones',         'Gestion de cotizaciones',               'currency-dollar', 9)
        ) AS v(key, name, description, icon, sort_order)
        WHERE NOT EXISTS (SELECT 1 FROM modules WHERE modules.key = v.key)
    """)


def downgrade() -> None:
    op.drop_constraint('fk_users_security_level_id', 'users', type_='foreignkey')
    op.drop_index(op.f('ix_users_security_level_id'), table_name='users')
    op.drop_column('users', 'security_level_id')
    op.drop_table('security_level_modules')
    op.drop_index(op.f('ix_security_levels_id'), table_name='security_levels')
    op.drop_table('security_levels')
