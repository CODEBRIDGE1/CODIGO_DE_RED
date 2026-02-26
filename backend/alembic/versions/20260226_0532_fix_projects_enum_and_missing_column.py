"""fix_projects_enum_and_missing_column

Revision ID: 929c252dcd2d
Revises: 240a1b9b943a
Create Date: 2026-02-26 05:32:39.892582

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '929c252dcd2d'
down_revision: Union[str, None] = '240a1b9b943a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Fix projects module issues:
    1. Add ABIERTO value to projectstatus enum
    2. Add progress_percentage column to project_tasks
    """
    
    # 1. Add ABIERTO to projectstatus enum if it doesn't exist
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_enum 
                WHERE enumlabel = 'ABIERTO' 
                AND enumtypid = 'projectstatus'::regtype
            ) THEN
                ALTER TYPE projectstatus ADD VALUE 'ABIERTO';
            END IF;
        END $$;
    """)
    
    # 2. Add progress_percentage column to project_tasks if it doesn't exist
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='project_tasks' 
                AND column_name='progress_percentage'
            ) THEN
                ALTER TABLE project_tasks 
                ADD COLUMN progress_percentage INTEGER DEFAULT 0 NOT NULL;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    """
    Rollback changes:
    1. Remove progress_percentage column
    2. Cannot remove enum value (PostgreSQL limitation)
    """
    op.execute("""
        ALTER TABLE project_tasks 
        DROP COLUMN IF EXISTS progress_percentage;
    """)
