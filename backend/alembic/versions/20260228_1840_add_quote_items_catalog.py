"""add_quote_items_catalog

Revision ID: a5f44784c761
Revises: 929c252dcd2d
Create Date: 2026-02-28 18:40:32.815652

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a5f44784c761'
down_revision: Union[str, None] = '026cf65e139d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create quote items catalog tables"""
    
    # 1. Create enums (solo si no existen)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE itemcategory AS ENUM (
                'INSTALACION',
                'MANTENIMIENTO', 
                'AUDITORIA',
                'CERTIFICACION',
                'CONSULTORIA',
                'MATERIALES',
                'MANO_OBRA',
                'EQUIPO',
                'OTRO'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE unit AS ENUM (
                'PIEZA',
                'METRO',
                'METRO_CUADRADO',
                'METRO_CUBICO',
                'SERVICIO',
                'HORA',
                'DIA',
                'LOTE',
                'KILOGRAMO',
                'LITRO'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # 2. Create quote_items table (catálogo global)
    op.create_table(
        'quote_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('unit', sa.String(length=50), nullable=False),
        sa.Column('base_price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Ahora cambiar las columnas a usar los tipos enum
    op.execute("ALTER TABLE quote_items ALTER COLUMN category TYPE itemcategory USING category::itemcategory")
    op.execute("ALTER TABLE quote_items ALTER COLUMN unit TYPE unit USING unit::unit")
    op.create_index('ix_quote_items_id', 'quote_items', ['id'])
    op.create_index('ix_quote_items_code', 'quote_items', ['code'], unique=True)
    
    # 3. Create tenant_quote_item_prices table
    op.create_table(
        'tenant_quote_item_prices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('quote_item_id', sa.Integer(), nullable=False),
        sa.Column('custom_price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.ForeignKeyConstraint(['quote_item_id'], ['quote_items.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_tenant_quote_item_prices_id', 'tenant_quote_item_prices', ['id'])
    
    # Unique constraint: un tenant solo puede tener un precio custom por item
    op.create_unique_constraint(
        'uq_tenant_quote_item', 
        'tenant_quote_item_prices', 
        ['tenant_id', 'quote_item_id']
    )


def downgrade() -> None:
    """Drop quote items catalog tables"""
    
    # Drop tables
    op.drop_table('tenant_quote_item_prices')
    op.drop_table('quote_items')
    
    # Drop enums
    op.execute("DROP TYPE IF EXISTS unit;")
    op.execute("DROP TYPE IF EXISTS itemcategory;")
