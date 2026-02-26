"""add_projects_module

Revision ID: 359d44c42b9d
Revises: 20260223_0100
Create Date: 2026-02-23 05:30:41.946180

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '359d44c42b9d'
down_revision: Union[str, None] = '20260223_0100'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    This migration was simplified to only create ENUM types.
    The actual table/column changes will be regenerated in a future migration.
    """
    # Create ENUM types (idempotent)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE tasktype AS ENUM ('OBLIGATION', 'CUSTOM');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE taskstatus AS ENUM ('NO_INICIADO', 'EN_PROGRESO', 'COMPLETADO', 'CERRADO');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE evidencetype AS ENUM ('MEDICION', 'FOTO', 'INFORME', 'BITACORA', 'DICTAMEN', 'MANUAL', 'OTRO');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE projecttype AS ENUM ('AUDITORIA', 'CORRECTIVO', 'MANTENIMIENTO', 'REVISION_RUTINA', 'TC');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE projectstatus AS ENUM ('ABIERTO', 'EN_PROGRESO', 'COMPLETADO', 'CERRADO');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE priority AS ENUM ('BAJA', 'MEDIA', 'ALTA', 'CRITICA');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)


def downgrade() -> None:
    """Drop ENUM types"""
    op.execute("DROP TYPE IF EXISTS priority CASCADE")
    op.execute("DROP TYPE IF EXISTS projectstatus CASCADE")
    op.execute("DROP TYPE IF EXISTS projecttype CASCADE")
    op.execute("DROP TYPE IF EXISTS evidencetype CASCADE")
    op.execute("DROP TYPE IF EXISTS taskstatus CASCADE")
    op.execute("DROP TYPE IF EXISTS tasktype CASCADE")
