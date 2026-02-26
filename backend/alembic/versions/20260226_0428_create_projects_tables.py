"""create_projects_tables

Revision ID: 240a1b9b943a
Revises: 359d44c42b9d
Create Date: 2026-02-26 04:28:10.475263

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '240a1b9b943a'
down_revision: Union[str, None] = '359d44c42b9d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Alter existing projects table and create missing tables"""
    
    # 1. Alter projects table (table already exists, but missing columns)
    # Check if columns exist before adding them
    from sqlalchemy import inspect
    from sqlalchemy.engine import reflection
    
    # Add missing columns to projects table
    op.execute("""
        DO $$ 
        BEGIN
            -- Add project_type column if it doesn't exist
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='projects' AND column_name='project_type') THEN
                ALTER TABLE projects ADD COLUMN project_type VARCHAR(50);
            END IF;
            
            -- Add priority column if it doesn't exist
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='projects' AND column_name='priority') THEN
                ALTER TABLE projects ADD COLUMN priority VARCHAR(50);
            END IF;
            
            -- Add start_date column if it doesn't exist
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='projects' AND column_name='start_date') THEN
                ALTER TABLE projects ADD COLUMN start_date DATE;
            END IF;
            
            -- Add due_date column if it doesn't exist
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='projects' AND column_name='due_date') THEN
                ALTER TABLE projects ADD COLUMN due_date DATE;
            END IF;
            
            -- Add completed_at column if it doesn't exist
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='projects' AND column_name='completed_at') THEN
                ALTER TABLE projects ADD COLUMN completed_at TIMESTAMP;
            END IF;
            
            -- Add closed_at column if it doesn't exist
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='projects' AND column_name='closed_at') THEN
                ALTER TABLE projects ADD COLUMN closed_at TIMESTAMP;
            END IF;
            
            -- Add created_by column if it doesn't exist
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='projects' AND column_name='created_by') THEN
                ALTER TABLE projects ADD COLUMN created_by INTEGER REFERENCES users(id);
            END IF;
            
            -- Add updated_by column if it doesn't exist
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='projects' AND column_name='updated_by') THEN
                ALTER TABLE projects ADD COLUMN updated_by INTEGER REFERENCES users(id);
            END IF;
        END $$;
    """)
    
    # Update existing NULL values for required columns
    op.execute("""
        UPDATE projects 
        SET project_type = 'AUDITORIA' 
        WHERE project_type IS NULL
    """)
    
    op.execute("""
        UPDATE projects 
        SET created_by = (SELECT id FROM users LIMIT 1) 
        WHERE created_by IS NULL
    """)
    
    # Convert columns to ENUMs and set NOT NULL
    op.execute("""
        ALTER TABLE projects 
        ALTER COLUMN project_type TYPE projecttype 
        USING project_type::projecttype
    """)
    
    op.execute("""
        ALTER TABLE projects 
        ALTER COLUMN project_type SET NOT NULL
    """)
    
    op.execute("""
        ALTER TABLE projects 
        ALTER COLUMN status TYPE projectstatus 
        USING COALESCE(status, 'ABIERTO')::projectstatus
    """)
    
    op.execute("""
        ALTER TABLE projects 
        ALTER COLUMN status SET NOT NULL
    """)
    
    op.execute("""
        ALTER TABLE projects 
        ALTER COLUMN priority TYPE priority 
        USING priority::priority
    """)
    
    op.execute("""
        ALTER TABLE projects 
        ALTER COLUMN created_by SET NOT NULL
    """)
    
    # Create index on project_type
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_projects_project_type 
        ON projects(project_type)
    """)
    
    # 2. Create project_tasks table (if not exists)
    op.execute("""
        CREATE TABLE IF NOT EXISTS project_tasks (
            id SERIAL PRIMARY KEY,
            project_id INTEGER NOT NULL REFERENCES projects(id),
            task_type VARCHAR(50) NOT NULL,
            requirement_id INTEGER REFERENCES compliance_requirements(id),
            code VARCHAR(50),
            title VARCHAR(300) NOT NULL,
            description TEXT,
            status VARCHAR(50) NOT NULL,
            assignee_user_id INTEGER REFERENCES users(id),
            due_date DATE,
            progress_percentage INTEGER NOT NULL DEFAULT 0,
            sort_order INTEGER NOT NULL DEFAULT 0,
            notes TEXT,
            created_by INTEGER NOT NULL REFERENCES users(id),
            updated_by INTEGER REFERENCES users(id),
            created_at TIMESTAMP NOT NULL DEFAULT now(),
            updated_at TIMESTAMP NOT NULL DEFAULT now()
        )
    """)
    
    # Convert to ENUMs
    op.execute("""
        ALTER TABLE project_tasks 
        ALTER COLUMN task_type TYPE tasktype 
        USING task_type::tasktype
    """)
    
    op.execute("""
        ALTER TABLE project_tasks 
        ALTER COLUMN status TYPE taskstatus 
        USING status::taskstatus
    """)
    
    # 3. Create task_evidences table (if not exists)
    op.execute("""
        CREATE TABLE IF NOT EXISTS task_evidences (
            id SERIAL PRIMARY KEY,
            task_id INTEGER NOT NULL REFERENCES project_tasks(id),
            storage_key VARCHAR(500) NOT NULL,
            file_url VARCHAR(1000),
            filename VARCHAR(300) NOT NULL,
            mime_type VARCHAR(100),
            size_bytes INTEGER,
            evidence_type VARCHAR(50) NOT NULL,
            comment TEXT,
            uploaded_by INTEGER NOT NULL REFERENCES users(id),
            uploaded_at TIMESTAMP NOT NULL DEFAULT now()
        )
    """)
    
    # Convert to ENUM
    op.execute("""
        ALTER TABLE task_evidences 
        ALTER COLUMN evidence_type TYPE evidencetype 
        USING evidence_type::evidencetype
    """)
    
    # 4. Create task_comments table (if not exists)
    op.execute("""
        CREATE TABLE IF NOT EXISTS task_comments (
            id SERIAL PRIMARY KEY,
            task_id INTEGER NOT NULL REFERENCES project_tasks(id),
            comment TEXT NOT NULL,
            created_by INTEGER NOT NULL REFERENCES users(id),
            created_at TIMESTAMP NOT NULL DEFAULT now(),
            updated_at TIMESTAMP NOT NULL DEFAULT now()
        )
    """)
    
    # 5. Create task_activity_logs table (if not exists)
    op.execute("""
        CREATE TABLE IF NOT EXISTS task_activity_logs (
            id SERIAL PRIMARY KEY,
            task_id INTEGER NOT NULL REFERENCES project_tasks(id),
            event_type VARCHAR(50) NOT NULL,
            payload_json TEXT,
            created_by INTEGER NOT NULL REFERENCES users(id),
            created_at TIMESTAMP NOT NULL DEFAULT now()
        )
    """)
    
    # Create indexes
    op.execute("CREATE INDEX IF NOT EXISTS ix_project_tasks_project ON project_tasks(project_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_project_tasks_status ON project_tasks(status)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_task_evidences_task ON task_evidences(task_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_task_comments_task ON task_comments(task_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_task_activity_logs_task ON task_activity_logs(task_id)")


def downgrade() -> None:
    """Drop all project-related tables"""
    op.drop_table('task_activity_logs')
    op.drop_table('task_comments')
    op.drop_table('task_evidences')
    op.drop_table('project_tasks')
    op.drop_table('projects')
